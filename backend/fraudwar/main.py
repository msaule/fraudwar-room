from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException

from fraudwar.arena.environment import EXPERIMENTS, run_experiment
from fraudwar.schemas.entities import SAFETY_DISCLAIMER
from fraudwar.services.persistence import list_persisted_runs, load_run

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "generated"
DB_PATH = DATA_DIR / "fraudwar.sqlite"

app = FastAPI(title="FraudWar Room API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "disclaimer": SAFETY_DISCLAIMER}


@app.get("/dashboard/summary")
def dashboard_summary() -> dict:
    run = _latest_run()
    metrics = run["metrics"]
    return {
        "run_id": run["run_id"],
        "experiment": run["experiment_name"],
        "defense": run["defense_name"],
        "net_fraud_loss": metrics["financial"]["fraud_dollars_missed"],
        "prevented_loss": metrics["financial"]["fraud_dollars_blocked"],
        "active_rings": sum(1 for ring in run["rings"] if ring.get("active")),
        "backlog": metrics["operations"]["backlog"],
        "adversarial_half_life": metrics["adversarial"]["adversarial_half_life"],
        "ring_level_recall": metrics["graph"]["ring_level_recall"],
        "recommended_defense": run["recommendation"],
        "disclaimer": SAFETY_DISCLAIMER,
    }


@app.get("/experiments")
def list_experiments() -> list[dict[str, str]]:
    return [{"id": key, "name": value} for key, value in EXPERIMENTS.items()]


@app.get("/experiments/{experiment_id}")
def get_experiment(experiment_id: str) -> dict[str, str]:
    if experiment_id not in EXPERIMENTS:
        raise HTTPException(status_code=404, detail="experiment not found")
    return {"id": experiment_id, "name": EXPERIMENTS[experiment_id]}


@app.post("/experiments/{experiment_id}/run")
def run_experiment_endpoint(experiment_id: str) -> dict:
    if experiment_id not in EXPERIMENTS:
        raise HTTPException(status_code=404, detail="experiment not found")
    return run_experiment(experiment_id=experiment_id, output_dir=DATA_DIR)


@app.get("/runs")
def list_runs() -> list[dict[str, str]]:
    json_runs = [{"id": path.stem, "path": str(path), "source": "json"} for path in DATA_DIR.glob("run_*.json")]
    sqlite_runs = [
        {"id": row["run_id"], **row, "source": "sqlite"}
        for row in list_persisted_runs(DB_PATH)
    ]
    seen = set()
    merged = []
    for row in [*sqlite_runs, *json_runs]:
        run_id = row["id"]
        if run_id in seen:
            continue
        seen.add(run_id)
        merged.append(row)
    return merged


@app.get("/runs/{run_id}")
def get_run(run_id: str) -> dict:
    return _read_run(run_id)


@app.get("/runs/{run_id}/metrics")
def get_metrics(run_id: str) -> dict:
    return _read_run(run_id)["metrics"]


@app.get("/runs/{run_id}/rings")
def get_rings(run_id: str) -> list[dict]:
    return _read_run(run_id)["rings"]


@app.get("/runs/{run_id}/cases")
def get_cases(run_id: str) -> list[dict]:
    return _read_run(run_id)["cases"]


@app.get("/runs/{run_id}/graph")
def get_graph(run_id: str) -> dict:
    return _read_run(run_id)["graph"]


@app.get("/runs/{run_id}/timeline")
def get_timeline(run_id: str) -> list[dict]:
    return _read_run(run_id)["timeline"]


@app.get("/runs/{run_id}/report")
def get_report(run_id: str) -> dict:
    return _read_run(run_id)["report"]


@app.get("/rings/{ring_id}")
def get_ring(ring_id: str) -> dict:
    run = _latest_run()
    for ring in run["rings"]:
        if ring["ring_id"] == ring_id:
            return ring
    raise HTTPException(status_code=404, detail="ring not found")


@app.get("/cases/{case_id}")
def get_case(case_id: str) -> dict:
    run = _latest_run()
    for case in run["cases"]:
        if case["case_id"] == case_id:
            return case
    raise HTTPException(status_code=404, detail="case not found")


def _read_run(run_id: str) -> dict:
    persisted = load_run(DB_PATH, run_id)
    if persisted:
        return persisted
    path = DATA_DIR / f"{run_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="run not found")
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_run() -> dict:
    runs = sorted(DATA_DIR.glob("run_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not runs:
        return run_experiment(output_dir=DATA_DIR)
    return json.loads(runs[0].read_text(encoding="utf-8"))
