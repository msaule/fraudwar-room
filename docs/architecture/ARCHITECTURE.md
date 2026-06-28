# Architecture

The MVP is a local monorepo:

- `backend/fraudwar`: Python package with simulation, graph features, defenses, metrics,
  reports, CLI, and FastAPI.
- `frontend`: Next.js dashboard consuming generated demo data.
- `data/generated`: experiment outputs and after-action reports.
- `data/generated/fraudwar.sqlite`: local SQLite store for runs, entities, metrics, graph
  payloads, alerts, cases, and report paths.
- `docs`: research, product, safety, metrics, usage, and portfolio materials.

## Core Loop

1. Generate benign and fraud transactions for a synthetic world.
2. Train or apply defenses.
3. Generate alerts.
4. Convert alerts into cases.
5. Process cases under investigator capacity.
6. Feed synthetic friction back to rings.
7. Record adaptation events.
8. Compute metrics and reports.

## FraudArena Components

- `SyntheticPaymentNetwork`: accounts, merchants, devices, IP clusters, transactions.
- `FraudRingSimulator`: abstract ring membership and behavior parameters.
- `AdaptationEngine`: closed-world response to synthetic defensive friction.
- `DetectionPolicies`: rules, supervised model, graph-feature model.
- `InvestigatorQueue`: capacity, backlog, SLA, review hours.
- `CostModel`: loss, blocked value, false positives, review cost.
- `GraphEvidenceEngine`: NetworkX graph and account-level graph features.
- `AfterActionReport`: JSON, Markdown, and HTML.
- `PersistenceStore`: local SQLite tables for reproducible experiment artifacts.
