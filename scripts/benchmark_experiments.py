from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fraudwar.arena.environment import EXPERIMENTS, run_experiment


KEY_METRICS = [
    ("classification", "precision"),
    ("classification", "recall"),
    ("classification", "f1"),
    ("financial", "net_savings"),
    ("financial", "investigator_roi"),
    ("operations", "backlog"),
    ("graph", "ring_level_recall"),
    ("graph", "time_to_first_detection"),
    ("adversarial", "recall_decay"),
    ("adversarial", "adversarial_half_life"),
    ("adversarial", "strategy_robustness_index"),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a compact multi-seed experiment benchmark.")
    parser.add_argument("--seeds", default="11,42,99", help="Comma-separated integer seeds.")
    parser.add_argument("--accounts", type=int, default=600)
    parser.add_argument("--merchants", type=int, default=70)
    parser.add_argument("--transactions", type=int, default=2400)
    parser.add_argument("--rings", type=int, default=5)
    parser.add_argument("--days", type=int, default=24)
    parser.add_argument("--output-dir", type=Path, default=Path("data") / "benchmarks")
    args = parser.parse_args()

    seeds = [int(seed.strip()) for seed in args.seeds.split(",") if seed.strip()]
    args.output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, float | int | str]] = []
    for experiment_id in EXPERIMENTS:
        for seed in seeds:
            run = run_experiment(
                experiment_id,
                seed=seed,
                output_dir=args.output_dir / "runs",
                accounts=args.accounts,
                merchants=args.merchants,
                transactions=args.transactions,
                rings=args.rings,
                days=args.days,
            )
            row: dict[str, float | int | str] = {
                "experiment_id": experiment_id,
                "run_id": run["run_id"],
                "seed": seed,
            }
            for namespace, metric_name in KEY_METRICS:
                row[f"{namespace}.{metric_name}"] = run["metrics"][namespace][metric_name]
            rows.append(row)

    summary = summarize(rows)
    write_csv(args.output_dir / "benchmark_rows.csv", rows)
    (args.output_dir / "benchmark_summary.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    print(json.dumps({"rows": len(rows), "summary": str(args.output_dir / "benchmark_summary.json")}))


def summarize(rows: list[dict[str, float | int | str]]) -> dict[str, dict[str, dict[str, float]]]:
    by_experiment: dict[str, list[dict[str, float | int | str]]] = {}
    for row in rows:
        by_experiment.setdefault(str(row["experiment_id"]), []).append(row)

    summary: dict[str, dict[str, dict[str, float]]] = {}
    for experiment_id, experiment_rows in by_experiment.items():
        metric_summary: dict[str, dict[str, float]] = {}
        for _, metric_name in KEY_METRICS:
            key = next(k for k in experiment_rows[0] if k.endswith(f".{metric_name}"))
            values = [float(row[key]) for row in experiment_rows if _is_finite_number(row[key])]
            if values:
                metric_summary[key] = {
                    "mean": round(statistics.fmean(values), 4),
                    "min": round(min(values), 4),
                    "max": round(max(values), 4),
                }
        summary[experiment_id] = metric_summary
    return summary


def write_csv(path: Path, rows: list[dict[str, float | int | str]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _is_finite_number(value: object) -> bool:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False
    return number == number and number not in {float("inf"), float("-inf")}


if __name__ == "__main__":
    main()
