from __future__ import annotations

from pathlib import Path

from fastapi import BackgroundTasks

import fraudwar.main as api_main
from fraudwar.adaptation.engine import adapt_rings
from fraudwar.arena.environment import run_experiment
from fraudwar.defenses.active_learning import active_learning_scores
from fraudwar.defenses.adaptive_threshold import threshold_for_alert_budget
from fraudwar.defenses.gnn import OptionalDependencyError, PyGGraphNeuralNetwork
from fraudwar.defenses.rules import RulesEngine
from fraudwar.graph.engine import build_evidence_graph, extract_account_graph_features, graph_payload
from fraudwar.investigators.queue import create_cases, process_queue
from fraudwar.main import health
from fraudwar.metrics.calculations import adversarial_half_life, investigator_roi, ring_level_recall
from fraudwar.reports.after_action import write_reports
from fraudwar.reports.investigator_summary import summarize_case
from fraudwar.schemas.entities import Investigator
from fraudwar.services.persistence import list_persisted_runs, load_run
from fraudwar.synthetic.generator import generate_world


def test_synthetic_generation_reproducible() -> None:
    a = generate_world(seed=7, accounts=180, merchants=30, transactions=800, rings=3)
    b = generate_world(seed=7, accounts=180, merchants=30, transactions=800, rings=3)
    assert a.transactions[0].model_dump() == b.transactions[0].model_dump()
    assert len(a.rings) == 3
    assert any(tx.fraud_label for tx in a.transactions)
    assert a.customers
    assert a.payment_instruments
    assert a.devices
    assert a.ip_clusters
    assert a.refunds or a.chargebacks or a.disputes


def test_graph_features_and_rules_alerts() -> None:
    world = generate_world(seed=9, accounts=220, merchants=40, transactions=1200, rings=4)
    graph = build_evidence_graph(
        world.accounts,
        world.merchants,
        world.transactions,
        world.rings,
        payment_instruments=world.payment_instruments,
        refunds=world.refunds,
        chargebacks=world.chargebacks,
        disputes=world.disputes,
        support_contacts=world.support_contacts,
        account_changes=world.account_changes,
    )
    features = extract_account_graph_features(world.transactions)
    alerts = RulesEngine().generate_alerts(world.transactions, threshold=0.20)
    assert graph.number_of_nodes() > len(world.accounts)
    assert {"transaction", "payment_instrument"} <= {
        data.get("kind") for _, data in graph.nodes(data=True)
    }
    payload_types = {node["type"] for node in graph_payload(graph)["nodes"]}
    assert {"transaction", "payment_instrument", "refund"} & payload_types
    assert features
    assert alerts


def test_signature_metrics() -> None:
    assert ring_level_recall([], []) == 0.0
    assert adversarial_half_life([0.8, 0.7, 0.41, 0.35]) > 1
    assert investigator_roi(10_000, 500, 650, 10) == 885


def test_investigator_queue_and_adaptation() -> None:
    world = generate_world(seed=11, accounts=250, merchants=40, transactions=1500, rings=4)
    alerts = RulesEngine().generate_alerts(world.transactions, threshold=0.18)
    cases = create_cases(alerts)
    processed, ops = process_queue(cases, [Investigator(investigator_id="i1", cases_per_day=20)])
    adapted, events = adapt_rings(world.rings, processed, day=30)
    assert ops["investigator_hours_used"] >= 0
    assert len(adapted) == len(world.rings)
    assert isinstance(events, list)


def test_run_experiment_and_reports(tmp_path: Path) -> None:
    run = run_experiment(
        "static-vs-adaptive",
        seed=12,
        output_dir=tmp_path,
        accounts=350,
        merchants=50,
        transactions=1800,
        rings=4,
        days=20,
    )
    paths = write_reports(run, tmp_path / "reports")
    assert run["metrics"]["graph"]["ring_level_recall"] >= 0
    assert "adversarial_half_life" in run["metrics"]["adversarial"]
    assert run["entities"]["customers"] == 350
    assert Path(paths["json"]).exists()
    persisted = list_persisted_runs(tmp_path / "fraudwar.sqlite")
    assert persisted
    assert load_run(tmp_path / "fraudwar.sqlite", run["run_id"])["run_id"] == run["run_id"]


def test_active_learning_and_adaptive_thresholding() -> None:
    world = generate_world(seed=14, accounts=320, merchants=45, transactions=1600, rings=4)
    train = [tx for tx in world.transactions if tx.day < 10]
    test = [tx for tx in world.transactions if tx.day >= 10]
    scores, diagnostics = active_learning_scores(train, test, label_budget=20)
    threshold, threshold_diagnostics = threshold_for_alert_budget(scores, alert_budget=12)
    assert scores
    assert diagnostics["retraining_events"] >= 0
    assert 0.20 <= threshold <= 0.92
    assert threshold_diagnostics["projected_alerts"] >= 1


def test_api_health() -> None:
    assert health()["status"] == "ok"


def test_api_jobs_history_and_benchmark(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(api_main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(api_main, "DB_PATH", tmp_path / "fraudwar.sqlite")
    run_request = api_main.RunScenarioRequest(
        experiment_id="static-vs-adaptive",
        seed=31,
        accounts=120,
        merchants=20,
        transactions=450,
        rings=2,
        days=12,
    )
    started = api_main.start_run(run_request, BackgroundTasks())
    api_main._run_scenario_job(started["job_id"], run_request.model_dump())
    job = api_main.job_status(started["job_id"])
    assert job["status"] == "succeeded"
    assert job["run_id"]
    history = api_main.get_run_history()
    assert history
    assert history[0]["run_id"] == job["run_id"]

    benchmark_request = api_main.BenchmarkRequest(
        seeds=[31],
        experiment_ids=["static-vs-adaptive"],
        accounts=120,
        merchants=20,
        transactions=450,
        rings=2,
        days=12,
    )
    benchmark_started = api_main.start_benchmark(benchmark_request, BackgroundTasks())
    api_main._run_benchmark_job(benchmark_started["job_id"], benchmark_request.model_dump())
    benchmark_job = api_main.job_status(benchmark_started["job_id"])
    assert benchmark_job["status"] == "succeeded"
    benchmark = api_main.get_latest_benchmark()
    assert benchmark["summary"][0]["runs"] == 1


def test_optional_gnn_dependency_path() -> None:
    assert isinstance(PyGGraphNeuralNetwork.is_available(), bool)
    if not PyGGraphNeuralNetwork.is_available():
        world = generate_world(seed=21, accounts=80, merchants=20, transactions=300, rings=2)
        try:
            PyGGraphNeuralNetwork(epochs=1).fit(world.transactions)
        except OptionalDependencyError as exc:
            assert "backend[gnn]" in str(exc)
        else:
            raise AssertionError("Expected OptionalDependencyError when PyG is unavailable.")


def test_investigator_summary_fallback_and_provider(monkeypatch) -> None:
    case = {
        "case_id": "case_test",
        "ring_id": "ring_001",
        "priority_score": 0.87,
        "dollar_exposure": 1200,
        "recommended_action": "link to ring and escalate synthetic disruption review",
    }
    monkeypatch.delenv("FRAUDWAR_ENABLE_CASE_SUMMARIES", raising=False)
    fallback = summarize_case(case)
    assert fallback["provider_enabled"] is False
    assert "case_test" in str(fallback["summary"])
    monkeypatch.setenv("FRAUDWAR_ENABLE_CASE_SUMMARIES", "1")
    monkeypatch.setenv("FRAUDWAR_CASE_SUMMARY_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    provider_result = summarize_case(case)
    assert provider_result["provider_enabled"] is False
    assert provider_result["provider"] == "openai"
    assert "OPENAI_API_KEY" in str(provider_result["provider_error"])
