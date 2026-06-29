from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from fraudwar.arena.environment import EXPERIMENTS, benchmark_experiments, run_experiment
from fraudwar.schemas.entities import SAFETY_DISCLAIMER
from fraudwar.services.persistence import (
    create_job,
    get_job,
    latest_benchmark,
    list_jobs,
    list_persisted_runs,
    load_run,
    mark_interrupted_jobs,
    persist_benchmark,
    run_history,
    update_job,
)

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "generated"
DB_PATH = DATA_DIR / "fraudwar.sqlite"
logger = logging.getLogger("fraudwar.api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    mark_interrupted_jobs(DB_PATH)
    yield


app = FastAPI(title="FraudWar Room API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunScenarioRequest(BaseModel):
    experiment_id: str = "static-vs-adaptive"
    seed: int = 42
    accounts: int = Field(900, ge=80, le=5_000)
    merchants: int = Field(90, ge=10, le=700)
    transactions: int = Field(4_500, ge=300, le=50_000)
    rings: int = Field(5, ge=1, le=30)
    days: int = Field(30, ge=7, le=120)


class BenchmarkRequest(BaseModel):
    seeds: list[int] = Field(default_factory=lambda: [11, 42, 99, 123, 202])
    experiment_ids: list[str] | None = None
    accounts: int = Field(600, ge=80, le=2_000)
    merchants: int = Field(70, ge=10, le=300)
    transactions: int = Field(2_400, ge=300, le=15_000)
    rings: int = Field(5, ge=1, le=20)
    days: int = Field(24, ge=7, le=90)


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


@app.post("/runs/start")
def start_run(request: RunScenarioRequest, background_tasks: BackgroundTasks) -> dict:
    if request.experiment_id not in EXPERIMENTS:
        raise HTTPException(status_code=404, detail="experiment not found")
    job_id = f"job_{uuid4().hex[:12]}"
    create_job(DB_PATH, job_id, "scenario_run", request.model_dump())
    background_tasks.add_task(_run_scenario_job, job_id, request.model_dump())
    return {"job_id": job_id, "status": "queued", "poll_url": f"/jobs/{job_id}"}


@app.post("/benchmarks/start")
def start_benchmark(request: BenchmarkRequest, background_tasks: BackgroundTasks) -> dict:
    experiment_ids = request.experiment_ids or list(EXPERIMENTS)
    invalid = [experiment_id for experiment_id in experiment_ids if experiment_id not in EXPERIMENTS]
    if invalid:
        raise HTTPException(status_code=404, detail=f"unknown experiment: {invalid[0]}")
    if not request.seeds:
        raise HTTPException(status_code=400, detail="at least one seed is required")
    if len(request.seeds) > 30:
        raise HTTPException(status_code=400, detail="seed count is capped at 30")
    job_id = f"job_{uuid4().hex[:12]}"
    payload = request.model_dump()
    payload["experiment_ids"] = experiment_ids
    create_job(DB_PATH, job_id, "benchmark", payload)
    background_tasks.add_task(_run_benchmark_job, job_id, payload)
    return {"job_id": job_id, "status": "queued", "poll_url": f"/jobs/{job_id}"}


@app.get("/jobs")
def jobs() -> list[dict]:
    return list_jobs(DB_PATH)


@app.get("/jobs/{job_id}")
def job_status(job_id: str) -> dict:
    job = get_job(DB_PATH, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.get("/benchmarks/latest")
def get_latest_benchmark() -> dict:
    report = latest_benchmark(DB_PATH)
    if not report:
        raise HTTPException(status_code=404, detail="benchmark not found")
    return report


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


@app.get("/runs/history")
def get_run_history() -> list[dict]:
    return run_history(DB_PATH)


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
    persisted = run_history(DB_PATH)
    if persisted:
        run = load_run(DB_PATH, persisted[0]["run_id"])
        if run:
            return run
    runs = sorted(DATA_DIR.glob("run_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not runs:
        return run_experiment(output_dir=DATA_DIR)
    return json.loads(runs[0].read_text(encoding="utf-8"))


def _run_scenario_job(job_id: str, request: dict) -> None:
    update_job(DB_PATH, job_id, status="running")
    logger.info(
        "fraudwar_job_started",
        extra={"job_id": job_id, "job_type": "scenario_run", "experiment": request["experiment_id"]},
    )
    try:
        run = run_experiment(
            experiment_id=request["experiment_id"],
            seed=int(request["seed"]),
            output_dir=DATA_DIR,
            accounts=int(request["accounts"]),
            merchants=int(request["merchants"]),
            transactions=int(request["transactions"]),
            rings=int(request["rings"]),
            days=int(request["days"]),
            run_id_suffix=job_id.replace("job_", ""),
        )
        result = {
            "run_id": run["run_id"],
            "experiment_id": run["experiment_id"],
            "seed": run["seed"],
            "metrics": {
                "recall_decay": run["metrics"]["adversarial"]["recall_decay"],
                "backlog": run["metrics"]["operations"]["backlog"],
                "ring_level_recall": run["metrics"]["graph"]["ring_level_recall"],
                "investigator_roi": run["metrics"]["financial"]["investigator_roi"],
            },
        }
        update_job(DB_PATH, job_id, status="succeeded", run_id=run["run_id"], result=result)
        logger.info("fraudwar_job_succeeded", extra={"job_id": job_id, "run_id": run["run_id"]})
    except Exception as exc:  # pragma: no cover - defensive boundary for background task
        update_job(DB_PATH, job_id, status="failed", error=str(exc))
        logger.exception("fraudwar_job_failed", extra={"job_id": job_id})


def _run_benchmark_job(job_id: str, request: dict) -> None:
    update_job(DB_PATH, job_id, status="running")
    logger.info("fraudwar_job_started", extra={"job_id": job_id, "job_type": "benchmark"})
    try:
        report = benchmark_experiments(
            seeds=[int(seed) for seed in request["seeds"]],
            experiment_ids=request["experiment_ids"],
            output_dir=DATA_DIR,
            accounts=int(request["accounts"]),
            merchants=int(request["merchants"]),
            transactions=int(request["transactions"]),
            rings=int(request["rings"]),
            days=int(request["days"]),
        )
        report["job_id"] = job_id
        persist_benchmark(DB_PATH, report["benchmark_id"], job_id, report)
        update_job(DB_PATH, job_id, status="succeeded", result=report)
        logger.info("fraudwar_job_succeeded", extra={"job_id": job_id, "benchmark_id": report["benchmark_id"]})
    except Exception as exc:  # pragma: no cover - defensive boundary for background task
        update_job(DB_PATH, job_id, status="failed", error=str(exc))
        logger.exception("fraudwar_job_failed", extra={"job_id": job_id})
