# FraudWar Room

Fraud detection is usually presented as a static classification problem.

Real fraud is not static.

Fraud rings react to friction. In the simulator they abandon burned accounts, split
clusters, change timing, and put pressure on the review queue.

FraudWar Room is a local fraud simulation and review dashboard. It generates a
synthetic payment network with benign users, merchants, fraud rings, mule accounts, refunds,
chargebacks, graph evidence, and investigator workflows. Fraud rings adapt after detection
while defense strategies are evaluated on fraud loss, false-positive harm, ring-level recall,
time-to-detection, adversarial half-life, and investigator workload.

> FraudWar Room uses synthetic data and abstract adversarial behavior for defensive research,
> analytics, and product testing. It is not a guide to committing fraud and must not be used
> to facilitate abuse.

## What Is FraudWar Room?

FraudWar Room is a local simulator for testing fraud controls under drift. It generates a
closed payment network, runs defenses against it, and reports what happened to loss, review
load, and ring discovery. The core primitive is FraudArena:

```text
SyntheticPaymentNetwork
+ BenignBehaviorSimulator
+ FraudRingSimulator
+ AdaptationEngine
+ DetectionPolicies
+ InvestigatorQueue
+ CaseManagementSimulation
+ CostModel
+ GraphEvidenceEngine
+ AfterActionReport
```

The point is the arena, not one score from one model.

## Why Static Fraud Models Are Not Enough

A classifier can catch suspicious transactions and still miss the organization behind them.
A threshold can improve recall and still bury investigators in false positives. A model can
look strong on yesterday's labels and fail after synthetic rings adapt.

FraudWar Room evaluates defenses at three levels:

- Transaction intelligence: is this transaction or account suspicious?
- Network intelligence: is this entity part of a coordinated synthetic ring?
- Drift and operations: does the defense still work after synthetic behavior changes?

## Quickstart

```bash
cd fraudwar-room
pip install -e "backend[dev]"
python scripts/export_frontend_demo.py
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. The dashboard uses demo data generated from the simulator.

## Demo Screenshots

Overview:

![Overview](docs/portfolio/screenshots/command-center.png)

Evidence map and ring overlays:

![Evidence Map](docs/portfolio/screenshots/battlefield.png)

Case queue:

![Cases](docs/portfolio/screenshots/cases.png)

Defense Tests:

![Defense Tests](docs/portfolio/screenshots/defense-lab.png)

Run Memo:

![Run Memo](docs/portfolio/screenshots/after-action.png)

Run the API:

```bash
cd backend
uvicorn fraudwar.main:app --reload
```

Run experiments:

```bash
python scripts/run_all_experiments.py
```

Run tests:

```bash
cd backend
python -m pytest
```

Build and test the dashboard:

```bash
cd frontend
npm run build
npm run test:e2e
```

On Windows without a downloaded Playwright browser, point tests at Edge:

```powershell
$env:PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH='C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
npm run test:e2e
```

Run the compact benchmark:

```bash
python scripts/benchmark_experiments.py --seeds 11,42,99
```

Run Docker Compose:

```bash
docker compose up --build
```

## Synthetic Data

The simulator generates accounts, merchants, devices, IP clusters, payment instruments,
transactions, refunds, chargebacks, fraud rings, alerts, cases, and investigator activity.
All data is synthetic and reproducible through seeds.

`python scripts/generate_world.py` defaults to 10,000 accounts, 500 merchants, 100,000
transactions, and 10 rings. The dashboard export uses a smaller run so local UI checks stay
quick.

## Adaptive Fraud Rings

Synthetic rings have abstract parameters such as velocity multiplier, amount multiplier,
refund multiplier, and shared infrastructure multiplier. When a ring experiences synthetic
defensive friction, the adaptation engine records abstract actions such as lowering velocity,
reducing shared infrastructure, or delaying activity.

These are closed-world simulation actions, not real-world instructions.

## Detection Defenses

- Rules baseline: refund ratio, chargeback ratio, velocity, shared devices, shared IPs.
- Supervised transaction model: account-level transaction features.
- Graph-feature model: transaction features plus NetworkX-derived shared-infrastructure and
  neighborhood features.
- Investigator priority policy: score, dollar exposure, graph linkage, and ring priority.
- Active learning policy: simulated investigator labels feed one graph-model retraining pass.
- Adaptive thresholding policy: thresholds are selected from alert budget and queue pressure.
- GNN extension point: `GNNStretchModel` preserves the model API for future PyTorch Geometric
  work while the MVP remains dependency-light. `PyGGraphNeuralNetwork` is available through
  the optional `backend[gnn]` extra.

## Metrics

Signature metrics:

- Ring-level recall.
- Adversarial half-life.
- Investigator ROI.

Other metrics include precision, recall, F1, AUROC, AUPRC, fraud dollars attempted, blocked
and missed, false-positive cost, review cost, backlog, SLA missed, time to first detection,
and strategy robustness index.

## Dashboard

The Next.js dashboard includes:

- Loss, recall, queue, and ROI metrics.
- Scenario selector for the implemented benchmark runs.
- Evidence map.
- Click-through evidence drawer for graph nodes and case rows.
- Event log.
- Ring table.
- Case queue.
- Defense result charts.
- Defense rationale table.
- Decision memo.
- Limitations panel.
- Methodology and safety boundary.

## Reports

Reports are generated in:

- JSON
- Markdown
- HTML

Example path:

```text
data/generated/reports/run_static_vs_adaptive_42_after_action.html
```

Runs are also persisted to local SQLite:

```text
data/generated/fraudwar.sqlite
```

The persistence layer uses SQLAlchemy over local SQLite so the API can load previously
generated runs without requiring an external database.

## Systems Design

API shape:

- `POST /runs/start` creates a background scenario job.
- `GET /jobs/{job_id}` returns job status, run ID, result summary, and errors.
- `GET /runs/history` lists persisted SQLite runs with seed, config, metrics, and report paths.
- `GET /runs/{run_id}` loads the full run payload.
- `POST /benchmarks/start` runs a multi-seed benchmark job.
- `GET /benchmarks/latest` returns the latest benchmark summary.

Data model:

- `simulation_runs`: run metadata and full run payload.
- `entity_records`: generated entities, alerts, cases, timeline entries, and graph payloads.
- `metric_records`: metric namespace, metric name, and value.
- `report_records`: JSON, Markdown, and HTML report paths.
- `simulation_jobs`: queued, running, succeeded, or failed background jobs.
- `benchmark_reports`: multi-seed benchmark summaries.

Async job flow:

1. The UI posts a scenario or benchmark request.
2. FastAPI creates a job row and returns a job ID.
3. A background task runs the simulator, writes JSON reports, persists SQLite rows, and marks
   the job succeeded or failed.
4. The UI polls job status, then loads the persisted run or benchmark report.

Scaling limits and next steps:

- Local SQLite is fine for the hosted static demo and local API. A multi-user version should use Postgres for run
  metadata and object storage for large graph/report payloads.
- FastAPI background tasks are process-local. A production version should use a durable queue
  and worker so jobs can survive restarts.
- Large benchmark runs should be sharded by seed and experiment ID, then reduced into one
  benchmark summary.
- Cache read-only run payloads and report responses by run ID. Invalidate only when a run is
  replaced or deleted.
- Failure modes to handle explicitly: bad scenario config, job timeout, worker crash, partial
  report write, API outage, and frontend API misconfiguration.

## Safety and Ethics

This project is defensive and synthetic only. It must not contain or be used for:

- Real fraud instructions.
- Credential theft or phishing.
- Real platform targeting.
- Refund abuse playbooks.
- Account takeover instructions.
- Synthetic identity instructions.
- Money-laundering instructions.
- Real customer or payment data.

## Architecture

```text
backend/fraudwar       Python simulation, metrics, API, reports
frontend               Next.js dashboard
data/generated         Local generated runs and reports
docs                   Research, product, safety, metrics, and usage notes
packages               Scenario and report JSON schemas
scripts                CLI wrappers and demo export helpers
```

## Experiments

- Static Fraud vs Adaptive Fraud
- Transaction Model vs Graph Model
- Recall vs Investigator Overload
- Ring Takedown vs Account Takedown
- Active Learning Under Drift
- Adaptive Thresholding Under Queue Pressure

## Why This Exists

Most fraud demos stop at transaction recall. This project tests a wider question: what
happens to loss, graph linkage, and review queues when the behavior changes after the first
round of friction?

## Roadmap

- Scenario config files.
- Larger benchmark scenarios.
- Multi-seed benchmark dashboards.
- Calibrated queue simulation with configurable investigator staffing.
- Optional GNN comparison runs in an environment with PyTorch Geometric installed.
- Optional case-summary drafting through a configured provider, never part of scoring.

See [OPTIONAL_MODELING_AND_SUMMARIES.md](docs/usage/OPTIONAL_MODELING_AND_SUMMARIES.md) for opt-in setup.
See [BENCHMARKING.md](docs/benchmarks/BENCHMARKING.md) for seed-sweep evaluation.
See [DEPLOYMENT.md](docs/usage/DEPLOYMENT.md) for Docker and local production checks.
