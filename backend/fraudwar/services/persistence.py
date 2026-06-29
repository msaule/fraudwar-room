from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

from fraudwar.synthetic.generator import SyntheticWorld


SCHEMA = """
CREATE TABLE IF NOT EXISTS simulation_runs (
  run_id TEXT PRIMARY KEY,
  experiment_id TEXT NOT NULL,
  seed INTEGER NOT NULL,
  days INTEGER NOT NULL,
  defense_name TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS entity_records (
  run_id TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  PRIMARY KEY (run_id, entity_type, entity_id)
);

CREATE TABLE IF NOT EXISTS metric_records (
  run_id TEXT NOT NULL,
  namespace TEXT NOT NULL,
  metric_name TEXT NOT NULL,
  metric_value TEXT NOT NULL,
  PRIMARY KEY (run_id, namespace, metric_name)
);

CREATE TABLE IF NOT EXISTS report_records (
  run_id TEXT NOT NULL,
  format TEXT NOT NULL,
  path TEXT NOT NULL,
  PRIMARY KEY (run_id, format)
);

CREATE TABLE IF NOT EXISTS simulation_jobs (
  job_id TEXT PRIMARY KEY,
  job_type TEXT NOT NULL,
  status TEXT NOT NULL,
  run_id TEXT,
  request_json TEXT NOT NULL,
  result_json TEXT,
  error TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS benchmark_reports (
  benchmark_id TEXT PRIMARY KEY,
  job_id TEXT,
  payload_json TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def init_db(db_path: Path | str) -> Path:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _engine(path).begin() as conn:
        for statement in _schema_statements():
            conn.execute(text(statement))
    return path


def persist_run(
    db_path: Path | str,
    run: dict,
    world: SyntheticWorld,
    report_paths: dict[str, str] | None = None,
) -> Path:
    path = init_db(db_path)
    with _engine(path).begin() as conn:
        conn.execute(
            text("""
            INSERT OR REPLACE INTO simulation_runs
            (run_id, experiment_id, seed, days, defense_name, payload_json)
            VALUES (:run_id, :experiment_id, :seed, :days, :defense_name, :payload_json)
            """),
            {
                "run_id": run["run_id"],
                "experiment_id": run["experiment_id"],
                "seed": int(run["seed"]),
                "days": int(run["days"]),
                "defense_name": run["defense_name"],
                "payload_json": json.dumps(run),
            },
        )
        _persist_world_entities(conn, run["run_id"], world)
        _persist_run_entities(conn, run)
        _persist_metrics(conn, run["run_id"], run["metrics"])
        for report_format, report_path in (report_paths or {}).items():
            conn.execute(
                text("""
                INSERT OR REPLACE INTO report_records (run_id, format, path)
                VALUES (:run_id, :format, :path)
                """),
                {"run_id": run["run_id"], "format": report_format, "path": report_path},
            )
    return path


def load_run(db_path: Path | str, run_id: str) -> dict | None:
    path = Path(db_path)
    if not path.exists():
        return None
    with _engine(path).connect() as conn:
        row = conn.execute(
            text("SELECT payload_json FROM simulation_runs WHERE run_id = :run_id"),
            {"run_id": run_id},
        ).first()
    return json.loads(row.payload_json) if row else None


def list_persisted_runs(db_path: Path | str) -> list[dict[str, str]]:
    path = Path(db_path)
    if not path.exists():
        return []
    with _engine(path).connect() as conn:
        rows = conn.execute(
            text("""
            SELECT run_id, experiment_id, defense_name, created_at
            FROM simulation_runs
            ORDER BY created_at DESC
            """)
        ).all()
    return [
        {
            "run_id": row.run_id,
            "experiment_id": row.experiment_id,
            "defense_name": row.defense_name,
            "created_at": row.created_at,
        }
        for row in rows
    ]


def run_history(db_path: Path | str) -> list[dict]:
    path = init_db(db_path)
    with _engine(path).connect() as conn:
        rows = conn.execute(
            text("""
            SELECT run_id, experiment_id, seed, days, defense_name, payload_json, created_at
            FROM simulation_runs
            ORDER BY created_at DESC
            """)
        ).all()
        reports = conn.execute(
            text("SELECT run_id, format, path FROM report_records")
        ).all()
    report_map: dict[str, dict[str, str]] = {}
    for row in reports:
        report_map.setdefault(row.run_id, {})[row.format] = row.path
    history = []
    for row in rows:
        payload = json.loads(row.payload_json)
        metrics = payload.get("metrics", {})
        history.append(
            {
                "run_id": row.run_id,
                "experiment_id": row.experiment_id,
                "experiment_name": payload.get("experiment_name", row.experiment_id),
                "seed": row.seed,
                "days": row.days,
                "defense_name": row.defense_name,
                "created_at": row.created_at,
                "metrics": {
                    "recall_decay": metrics.get("adversarial", {}).get("recall_decay", 0),
                    "backlog": metrics.get("operations", {}).get("backlog", 0),
                    "ring_level_recall": metrics.get("graph", {}).get("ring_level_recall", 0),
                    "investigator_roi": metrics.get("financial", {}).get("investigator_roi", 0),
                },
                "reports": report_map.get(row.run_id, {}),
            }
        )
    return history


def create_job(db_path: Path | str, job_id: str, job_type: str, request: dict) -> Path:
    path = init_db(db_path)
    with _engine(path).begin() as conn:
        conn.execute(
            text("""
            INSERT INTO simulation_jobs (job_id, job_type, status, request_json)
            VALUES (:job_id, :job_type, 'queued', :request_json)
            """),
            {
                "job_id": job_id,
                "job_type": job_type,
                "request_json": json.dumps(request),
            },
        )
    return path


def update_job(
    db_path: Path | str,
    job_id: str,
    *,
    status: str,
    run_id: str | None = None,
    result: dict | None = None,
    error: str | None = None,
) -> None:
    path = init_db(db_path)
    with _engine(path).begin() as conn:
        conn.execute(
            text("""
            UPDATE simulation_jobs
            SET status = :status,
                run_id = COALESCE(:run_id, run_id),
                result_json = :result_json,
                error = :error,
                updated_at = CURRENT_TIMESTAMP
            WHERE job_id = :job_id
            """),
            {
                "job_id": job_id,
                "status": status,
                "run_id": run_id,
                "result_json": json.dumps(result) if result is not None else None,
                "error": error,
            },
        )


def get_job(db_path: Path | str, job_id: str) -> dict | None:
    path = init_db(db_path)
    with _engine(path).connect() as conn:
        row = conn.execute(
            text("""
            SELECT job_id, job_type, status, run_id, request_json, result_json, error, created_at, updated_at
            FROM simulation_jobs
            WHERE job_id = :job_id
            """),
            {"job_id": job_id},
        ).first()
    if not row:
        return None
    return {
        "job_id": row.job_id,
        "job_type": row.job_type,
        "status": row.status,
        "run_id": row.run_id,
        "request": json.loads(row.request_json),
        "result": json.loads(row.result_json) if row.result_json else None,
        "error": row.error,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def list_jobs(db_path: Path | str, limit: int = 20) -> list[dict]:
    path = init_db(db_path)
    with _engine(path).connect() as conn:
        rows = conn.execute(
            text("""
            SELECT job_id, job_type, status, run_id, error, created_at, updated_at
            FROM simulation_jobs
            ORDER BY created_at DESC
            LIMIT :limit
            """),
            {"limit": limit},
        ).all()
    return [
        {
            "job_id": row.job_id,
            "job_type": row.job_type,
            "status": row.status,
            "run_id": row.run_id,
            "error": row.error,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
        for row in rows
    ]


def mark_interrupted_jobs(db_path: Path | str) -> None:
    path = init_db(db_path)
    with _engine(path).begin() as conn:
        conn.execute(
            text("""
            UPDATE simulation_jobs
            SET status = 'failed',
                error = 'Job was interrupted before completion.',
                updated_at = CURRENT_TIMESTAMP
            WHERE status IN ('queued', 'running')
            """)
        )


def persist_benchmark(db_path: Path | str, benchmark_id: str, job_id: str, payload: dict) -> None:
    path = init_db(db_path)
    with _engine(path).begin() as conn:
        conn.execute(
            text("""
            INSERT OR REPLACE INTO benchmark_reports
            (benchmark_id, job_id, payload_json)
            VALUES (:benchmark_id, :job_id, :payload_json)
            """),
            {
                "benchmark_id": benchmark_id,
                "job_id": job_id,
                "payload_json": json.dumps(payload),
            },
        )


def latest_benchmark(db_path: Path | str) -> dict | None:
    path = init_db(db_path)
    with _engine(path).connect() as conn:
        row = conn.execute(
            text("""
            SELECT payload_json
            FROM benchmark_reports
            ORDER BY created_at DESC
            LIMIT 1
            """)
        ).first()
    return json.loads(row.payload_json) if row else None


def _engine(db_path: Path | str) -> Engine:
    return create_engine(f"sqlite:///{Path(db_path).as_posix()}", future=True)


def _schema_statements() -> list[str]:
    return [statement.strip() for statement in SCHEMA.split(";") if statement.strip()]


def _persist_world_entities(conn: Connection, run_id: str, world: SyntheticWorld) -> None:
    for entity_type, records in world.as_dict().items():
        _insert_records(conn, run_id, entity_type, records)


def _persist_run_entities(conn: Connection, run: dict) -> None:
    for entity_type in ["alerts", "cases", "timeline"]:
        records = run.get(entity_type, [])
        normalized = []
        for idx, record in enumerate(records):
            entity_id = (
                record.get("alert_id")
                or record.get("case_id")
                or f"{entity_type}_{idx:08d}"
            )
            normalized.append({"_entity_id": entity_id, **record})
        _insert_records(conn, run["run_id"], entity_type, normalized)
    _insert_records(conn, run["run_id"], "graph", [{"_entity_id": "graph", **run.get("graph", {})}])


def _insert_records(
    conn: Connection,
    run_id: str,
    entity_type: str,
    records: Iterable[dict],
) -> None:
    rows = []
    for idx, record in enumerate(records):
        entity_id = _entity_id(record, entity_type, idx)
        rows.append(
            {
                "run_id": run_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "payload_json": json.dumps(_jsonable(record)),
            }
        )
    if rows:
        conn.execute(
            text("""
            INSERT OR REPLACE INTO entity_records
            (run_id, entity_type, entity_id, payload_json)
            VALUES (:run_id, :entity_type, :entity_id, :payload_json)
            """),
            rows,
        )


def _persist_metrics(conn: Connection, run_id: str, metrics: dict) -> None:
    rows = []
    for namespace, values in metrics.items():
        for metric_name, value in values.items():
            rows.append(
                {
                    "run_id": run_id,
                    "namespace": namespace,
                    "metric_name": metric_name,
                    "metric_value": json.dumps(value),
                }
            )
    if rows:
        conn.execute(
            text("""
            INSERT OR REPLACE INTO metric_records
            (run_id, namespace, metric_name, metric_value)
            VALUES (:run_id, :namespace, :metric_name, :metric_value)
            """),
            rows,
        )


def _entity_id(record: dict, entity_type: str, idx: int) -> str:
    for key in [
        "_entity_id",
        "customer_id",
        "account_id",
        "payment_instrument_id",
        "device_id",
        "ip_cluster_id",
        "category_id",
        "merchant_id",
        "ring_id",
        "transaction_id",
        "refund_id",
        "chargeback_id",
        "dispute_id",
        "support_contact_id",
        "account_change_id",
        "alert_id",
        "case_id",
    ]:
        if record.get(key):
            return str(record[key])
    return f"{entity_type}_{idx:08d}"


def _jsonable(value):
    if isinstance(value, BaseModel):
        return value.model_dump()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value
