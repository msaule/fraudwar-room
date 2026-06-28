from __future__ import annotations

import json
from pathlib import Path

from fraudwar.adaptation.engine import adapt_rings
from fraudwar.defenses.active_learning import active_learning_scores
from fraudwar.defenses.adaptive_threshold import threshold_for_alert_budget
from fraudwar.defenses.model import GraphFeatureModel, TransactionModel
from fraudwar.defenses.rules import RulesEngine
from fraudwar.graph.engine import build_evidence_graph, graph_payload
from fraudwar.investigators.queue import create_cases, process_queue
from fraudwar.metrics.calculations import (
    adversarial_half_life,
    classification_metrics,
    financial_metrics,
    ring_level_recall,
    ring_timing_metrics,
)
from fraudwar.reports.after_action import build_after_action_report, write_reports
from fraudwar.schemas.entities import Investigator
from fraudwar.services.persistence import persist_run
from fraudwar.synthetic.generator import SyntheticWorld, generate_world


EXPERIMENTS = {
    "static-vs-adaptive": "Static Fraud vs Adaptive Fraud",
    "graph-vs-transaction": "Transaction Model vs Graph Model",
    "investigator-overload": "Recall vs Investigator Overload",
    "ring-takedown": "Ring Takedown vs Account Takedown",
    "active-learning": "Active Learning Under Drift",
    "adaptive-thresholding": "Adaptive Thresholding Under Queue Pressure",
}


def run_experiment(
    experiment_id: str = "static-vs-adaptive",
    seed: int = 42,
    output_dir: Path | str = Path("data/generated"),
    accounts: int = 900,
    merchants: int = 90,
    transactions: int = 4500,
    rings: int = 5,
    days: int = 30,
) -> dict:
    world = generate_world(seed, accounts, merchants, transactions, rings, days)
    run = evaluate_world(world, experiment_id=experiment_id, seed=seed, days=days)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    run_path = output_path / f"{run['run_id']}.json"
    run_path.write_text(json.dumps(run, indent=2), encoding="utf-8")
    report_paths = write_reports(run, output_path / "reports")
    persist_run(output_path / "fraudwar.sqlite", run, world, report_paths)
    return run


def evaluate_world(world: SyntheticWorld, experiment_id: str, seed: int, days: int) -> dict:
    train_cutoff = max(7, days // 3)
    train = [tx for tx in world.transactions if tx.day < train_cutoff]
    test = [tx for tx in world.transactions if tx.day >= train_cutoff]

    rules = RulesEngine()
    rules_alerts = rules.generate_alerts(test, threshold=_threshold_for_experiment(experiment_id))

    tx_model = TransactionModel().fit(train)
    tx_scores = tx_model.score(test)
    tx_alerts = _alerts_from_scores(test, tx_scores, "transaction_model", threshold=0.54)

    graph_model = GraphFeatureModel().fit(train)
    graph_scores = graph_model.score(test)
    graph_alerts = _alerts_from_scores(test, graph_scores, "graph_model", threshold=0.48)
    strategy_diagnostics: dict[str, float] = {}

    if experiment_id == "graph-vs-transaction":
        chosen_alerts = graph_alerts
        defense_name = "graph_feature_model"
    elif experiment_id == "investigator-overload":
        chosen_alerts = rules.generate_alerts(test, threshold=0.28)
        defense_name = "high_sensitivity_rules"
    elif experiment_id == "active-learning":
        active_scores, strategy_diagnostics = active_learning_scores(train, test, label_budget=60)
        chosen_alerts = _alerts_from_scores(test, active_scores, "active_learning_graph_model", threshold=0.46)
        defense_name = "active_learning_graph_model"
    elif experiment_id == "adaptive-thresholding":
        threshold, strategy_diagnostics = threshold_for_alert_budget(graph_scores, alert_budget=72)
        chosen_alerts = _alerts_from_scores(
            test,
            graph_scores,
            "adaptive_threshold_graph_model",
            threshold=threshold,
        )
        defense_name = "adaptive_threshold_graph_model"
    else:
        chosen_alerts = graph_alerts if len(graph_alerts) else rules_alerts
        defense_name = "graph_feature_model"

    cases = create_cases(chosen_alerts, strategy="ring_priority" if experiment_id != "ring-takedown" else "dollar_risk")
    investigators = [Investigator(investigator_id=f"inv_{i:02d}", cases_per_day=18) for i in range(4)]
    processed_cases, operations = process_queue(cases, investigators)
    adapted_rings, adaptation_events = adapt_rings(world.rings, processed_cases, day=days)
    daily_recalls = _daily_recall_curve(test, chosen_alerts, days=train_cutoff)
    metrics = {
        "classification": classification_metrics(test, chosen_alerts),
        "financial": financial_metrics(test, chosen_alerts, operations["investigator_hours_used"]),
        "operations": operations,
        "graph": {
            "ring_level_recall": ring_level_recall(world.rings, chosen_alerts),
            **ring_timing_metrics(world.rings, chosen_alerts),
        },
        "adversarial": {
            "pre_adaptation_recall": _first_nonzero(daily_recalls),
            "post_adaptation_recall": round(daily_recalls[-1], 4) if daily_recalls else 0.0,
            "recall_decay": round((_first_nonzero(daily_recalls) - daily_recalls[-1]), 4)
            if daily_recalls
            else 0.0,
            "adversarial_half_life": adversarial_half_life(daily_recalls),
            "defense_brittleness_score": _brittleness_score(daily_recalls, operations["backlog"]),
            "strategy_robustness_index": _robustness_index(daily_recalls, world.rings, chosen_alerts),
            "adaptation_pressure": round(len(adaptation_events) / max(len(world.rings), 1), 4),
        },
        "strategy": strategy_diagnostics,
    }
    evidence_graph = build_evidence_graph(
        world.accounts,
        world.merchants,
        test,
        world.rings,
        payment_instruments=world.payment_instruments,
        refunds=world.refunds,
        chargebacks=world.chargebacks,
        disputes=world.disputes,
        support_contacts=world.support_contacts,
        account_changes=world.account_changes,
        cases=processed_cases,
    )
    run_id = f"run_{experiment_id.replace('-', '_')}_{seed}"
    run = {
        "run_id": run_id,
        "experiment_id": experiment_id,
        "experiment_name": EXPERIMENTS.get(experiment_id, experiment_id),
        "seed": seed,
        "days": days,
        "defense_name": defense_name,
        "metrics": metrics,
        "rings": [ring.model_dump() for ring in adapted_rings],
        "entities": {
            "customers": len(world.customers),
            "accounts": len(world.accounts),
            "payment_instruments": len(world.payment_instruments),
            "devices": len(world.devices),
            "ip_clusters": len(world.ip_clusters),
            "merchant_categories": len(world.merchant_categories),
            "merchants": len(world.merchants),
            "transactions": len(world.transactions),
            "refunds": len(world.refunds),
            "chargebacks": len(world.chargebacks),
            "disputes": len(world.disputes),
            "support_contacts": len(world.support_contacts),
            "account_changes": len(world.account_changes),
        },
        "cases": [case.model_dump() for case in processed_cases[:250]],
        "alerts": [alert.model_dump() for alert in chosen_alerts[:500]],
        "timeline": _timeline(world.rings, chosen_alerts, adaptation_events),
        "graph": graph_payload(evidence_graph),
        "defense_comparison": _defense_comparison(
            world.rings,
            test,
            rules_alerts,
            tx_alerts,
            graph_alerts,
            selected_name=defense_name,
            selected_alerts=chosen_alerts,
        ),
        "recommendation": _recommendation_for(experiment_id),
        "persistence": {"sqlite_path": "fraudwar.sqlite"},
    }
    run["report"] = build_after_action_report(run)
    return run


def run_all(output_dir: Path | str = Path("data/generated")) -> list[dict]:
    return [run_experiment(experiment_id=experiment, seed=42, output_dir=output_dir) for experiment in EXPERIMENTS]


def _threshold_for_experiment(experiment_id: str) -> float:
    return 0.30 if experiment_id == "investigator-overload" else 0.42


def _recommendation_for(experiment_id: str) -> str:
    if experiment_id == "active-learning":
        return "active_learning_graph_model + ring_priority investigation"
    if experiment_id == "adaptive-thresholding":
        return "adaptive_threshold_graph_model + queue-aware investigation"
    return "graph_feature_model + ring_priority investigation"


def _alerts_from_scores(test, scores, prefix: str, threshold: float):
    from collections import defaultdict

    from fraudwar.schemas.entities import Alert

    grouped = defaultdict(list)
    for tx in test:
        grouped[tx.account_id].append(tx)
    alerts = []
    for account_id, score in scores.items():
        if score < threshold:
            continue
        txs = grouped[account_id]
        fraud = [tx for tx in txs if tx.fraud_label]
        alerts.append(
            Alert(
                alert_id=f"alert_{prefix}_{account_id}",
                day=max(tx.day for tx in txs),
                entity_id=account_id,
                entity_type="account",
                score=round(float(score), 4),
                reason=f"{prefix} account risk score",
                dollar_exposure=round(sum(tx.amount for tx in txs), 2),
                ring_id=fraud[0].ring_id if fraud else None,
                is_true_positive=bool(fraud),
            )
        )
    return alerts


def _daily_recall_curve(transactions, alerts, days: int) -> list[float]:
    alerted = {alert.entity_id for alert in alerts}
    recalls = []
    day_values = sorted({tx.day for tx in transactions})
    if not day_values:
        return [0.0]
    for day in day_values:
        day_txs = [tx for tx in transactions if tx.day <= day]
        fraud_accounts = {tx.account_id for tx in day_txs if tx.fraud_label}
        if not fraud_accounts:
            recalls.append(0.0)
        else:
            caught = len(fraud_accounts & alerted)
            decay = max(0.52, 1.0 - max(0, day - days) * 0.018)
            recalls.append(round((caught / len(fraud_accounts)) * decay, 4))
    return recalls


def _brittleness_score(daily_recalls: list[float], backlog: float) -> float:
    if not daily_recalls:
        return 0.0
    decay = max(0.0, _first_nonzero(daily_recalls) - daily_recalls[-1])
    return round(min(1.0, decay + backlog / 1000), 4)


def _robustness_index(daily_recalls: list[float], rings, alerts) -> float:
    half_life = adversarial_half_life(daily_recalls)
    half_life_score = 1.0 if half_life == float("inf") else min(1.0, half_life / 14)
    return round((half_life_score + ring_level_recall(rings, alerts)) / 2, 4)


def _first_nonzero(values: list[float]) -> float:
    for value in values:
        if value > 0:
            return round(value, 4)
    return 0.0


def _defense_comparison(
    rings,
    test,
    rules_alerts,
    tx_alerts,
    graph_alerts,
    selected_name: str | None = None,
    selected_alerts=None,
) -> list[dict]:
    rows = []
    for name, alerts in [
        ("rules_baseline", rules_alerts),
        ("supervised_transaction_model", tx_alerts),
        ("graph_feature_model", graph_alerts),
    ]:
        cls = classification_metrics(test, alerts)
        rows.append(
            {
                "defense": name,
                "precision": cls["precision"],
                "recall": cls["recall"],
                "alerts": cls["alerts"],
                "ring_level_recall": ring_level_recall(rings, alerts),
            }
        )
    if selected_name and selected_name not in {row["defense"] for row in rows}:
        cls = classification_metrics(test, selected_alerts or [])
        rows.append(
            {
                "defense": selected_name,
                "precision": cls["precision"],
                "recall": cls["recall"],
                "alerts": cls["alerts"],
                "ring_level_recall": ring_level_recall(rings, selected_alerts or []),
            }
        )
    return rows


def _timeline(rings, alerts, adaptation_events) -> list[dict]:
    events = []
    for ring in rings[:12]:
        events.append(
            {
                "day": ring.start_day,
                "type": "ring_emergence",
                "title": f"{ring.ring_id} emerged",
                "detail": f"{ring.ring_type.value} entered the synthetic network",
            }
        )
    for alert in alerts[:80]:
        events.append(
            {
                "day": alert.day,
                "type": "detection",
                "title": f"{alert.entity_id} alerted",
                "detail": alert.reason,
            }
        )
    for event in adaptation_events:
        events.append(
            {
                "day": event.day,
                "type": "adaptation",
                "title": f"{event.ring_id} adapted",
                "detail": event.action.value,
            }
        )
    return sorted(events, key=lambda item: item["day"])[:180]
