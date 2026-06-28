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
