# Benchmarking

FraudWar Room includes a compact seed-sweep benchmark for comparing the six shipped
experiment strategies under repeatable synthetic pressure.

```bash
python scripts/benchmark_experiments.py --seeds 11,42,99
```

The benchmark writes ignored local artifacts to:

```text
data/benchmarks/benchmark_rows.csv
data/benchmarks/benchmark_summary.json
```

The default benchmark is intentionally smaller than the full 10,000-account generator so it
can run quickly on a laptop. Use larger arguments for deeper analysis:

```bash
python scripts/benchmark_experiments.py --seeds 1,2,3,4,5 --accounts 2500 --transactions 12000
```

Metrics summarized per experiment include precision, recall, F1, net savings,
investigator ROI, backlog, ring-level recall, time to first detection, recall decay,
adversarial half-life, and strategy robustness index.

All benchmark data is synthetic and generated locally.
