# FraudWar Room

Fraud detection is usually presented as a static classification problem.

Real fraud is not static.

Fraud rings observe friction, abandon burned accounts, split clusters, change timing,
exploit investigator capacity, and learn back.

FraudWar Room is an adaptive fraud simulation and investigation cockpit. It generates a
synthetic payment network with benign users, merchants, fraud rings, mule accounts, refunds,
chargebacks, graph evidence, and investigator workflows. Fraud rings adapt after detection
while defense strategies are evaluated on fraud loss, false-positive harm, ring-level recall,
time-to-detection, adversarial half-life, and investigator workload.

Fraud is not a dataset. It is an opponent.

> FraudWar Room uses synthetic data and abstract adversarial behavior for defensive research,
> analytics, and portfolio demonstration. It is not a guide to committing fraud and must not
> be used to facilitate abuse.

## What Is FraudWar Room?

FraudWar Room is a portfolio-grade synthetic benchmark and dashboard for evaluating fraud
defenses under adaptive pressure. The core primitive is FraudArena:

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

The fraud model is not the project. The arena is the project.

## Why Static Fraud Models Are Not Enough

A classifier can catch suspicious transactions and still miss the organization behind them.
A threshold can improve recall and still bury investigators in false positives. A model can
look strong on yesterday's labels and fail after synthetic rings adapt.

FraudWar Room evaluates defenses at three levels:

- Transaction intelligence: is this transaction or account suspicious?
- Network intelligence: is this entity part of a coordinated synthetic ring?
- Adversarial operations intelligence: does the defense survive after abstract adaptation?

## Quickstart

```bash
cd fraudwar-room
pip install -e "backend[dev]"
python scripts/export_frontend_demo.py
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

## Demo Screenshots

Command Center:

![Command Center](docs/portfolio/screenshots/command-center.png)

Battlefield graph and ring overlays:

![Battlefield](docs/portfolio/screenshots/battlefield.png)

Case queue:

![Cases](docs/portfolio/screenshots/cases.png)

Defense Lab:

![Defense Lab](docs/portfolio/screenshots/defense-lab.png)

After-Action Report:

![After-Action Report](docs/portfolio/screenshots/after-action.png)

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
transactions, and 10 rings. Dashboard demo export uses a smaller scenario so UI checks remain
fast while the full-scale generator path remains available and reproducible.

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

- Command center metrics.
- Network graph evidence.
- Battlefield timeline.
- Ring table.
- Case queue.
- Defense comparison charts.
- After-action report summary.
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
docs                   Research, product, safety, metrics, usage, portfolio
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

## Portfolio Value

FraudWar Room demonstrates financial-crime analytics, graph intelligence, simulation,
model evaluation, operations strategy, FastAPI, Next.js, product judgment, and safety-aware
portfolio presentation in one coherent system.

## Roadmap

- Scenario config files.
- Larger benchmark scenarios.
- Multi-seed benchmark dashboards.
- Calibrated queue simulation with configurable investigator staffing.
- Optional GNN comparison runs in an environment with PyTorch Geometric installed.
- Provider-backed LLM summaries as an opt-in assistive layer, never core.

See [OPTIONAL_GNN_AND_LLM.md](docs/usage/OPTIONAL_GNN_AND_LLM.md) for opt-in setup.
See [BENCHMARKING.md](docs/benchmarks/BENCHMARKING.md) for seed-sweep evaluation.
See [DEPLOYMENT.md](docs/usage/DEPLOYMENT.md) for Docker and local production checks.
