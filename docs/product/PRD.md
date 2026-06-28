# Product Requirements Document

## Vision

FraudWar Room is an adaptive fraud simulation and review dashboard. It evaluates
defenses against synthetic rings that change behavior after detection and reports outcomes
through transaction, graph, operations, financial, and drift metrics.

## Target Users

- Fraud strategy analyst: compare defenses beyond AUC.
- Financial-crime investigator: review graph evidence, case context, and ring linkage.
- Risk operations leader: manage alert burden, backlog, capacity, and dollars saved.
- Data scientist: compare drift, robustness, features, and cost-sensitive metrics.
- Trust-and-safety team: evaluate defenses under synthetic attack pressure.
- Engineering reviewer: inspect the simulator, assumptions, API, tests, and dashboard.

## Non-Goals

- No real customer data.
- No real payment data.
- No fraud-enablement instructions.
- No claim that this prevents real fraud.
- No provider dependency for the core system.

## Product Surfaces

- FastAPI simulation API.
- Python CLI and scripts.
- Generated synthetic data and experiment outputs.
- Run memos in JSON, Markdown, and HTML.
- Next.js dashboard with overview, graph evidence, rings, cases, experiments, and report
  view.

## MVP Scope

- Synthetic payment network.
- Abstract fraud rings.
- Adaptation loop.
- Rules, supervised transaction, and graph-feature defenses.
- Investigator queue.
- Signature metrics: ring-level recall, adversarial half-life, investigator ROI.
- Usable dashboard and documentation.

## Future Scope

- Scenario schema with YAML/JSON configs.
- PyTorch Geometric GNN.
- Optional case-summary drafting.
- SQLite persistence.
- Dockerized one-command demo.
- Larger benchmark scenarios.

## Architecture

FraudArena coordinates:

```text
SyntheticPaymentNetwork -> DetectionPolicies -> InvestigatorQueue
        |                         |                    |
        v                         v                    v
FraudRingSimulator <------ AdaptationEngine ---- CaseManagementSimulation
        |
        v
GraphEvidenceEngine -> CostModel -> AfterActionReport -> Dashboard
```

## Risks and Mitigations

- Risk: synthetic behavior lacks credibility. Mitigation: document assumptions and show
  sensitivity through experiments.
- Risk: alert volume overwhelms demo. Mitigation: configurable thresholds and run sizes.
- Risk: safety boundary drift. Mitigation: safety disclaimer in docs, reports, API, and UI.
- Risk: model overfocus. Mitigation: metrics and UI prioritize arena outcomes.

## Launch Strategy

Keep the repo private until the assumptions, screenshots, generated reports, and local
setup steps are easy to review.
