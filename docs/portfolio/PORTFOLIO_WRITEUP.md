# FraudWar Room: Adaptive Fraud Simulation and Investigation Cockpit

## Problem

Fraud detection is often presented as static classification. Real financial-crime operations
must balance detection, false positives, investigator workload, graph evidence, dollars
saved, and adversarial drift.

## Product Concept

FraudWar Room generates a synthetic payment network with accounts, merchants, devices,
transactions, refunds, chargebacks, synthetic rings, alerts, cases, and investigator queues.
Rings adapt abstractly after detection, and defenses are compared through the FraudArena
environment.

## Technical Architecture

- Python simulation package.
- FastAPI endpoints.
- NetworkX graph evidence.
- scikit-learn transaction and graph-feature models.
- Investigator queue and cost model.
- JSON, Markdown, and HTML after-action reports.
- Next.js dashboard.

## Screenshots

![Command Center](screenshots/command-center.png)

![Battlefield graph](screenshots/battlefield.png)

![Case queue](screenshots/cases.png)

![Defense lab](screenshots/defense-lab.png)

![After-action report](screenshots/after-action.png)

## Resume Bullets

- Built FraudWar Room, an adaptive fraud simulation and investigation cockpit that evaluates
  fraud defenses against synthetic fraud rings that change behavior after detection.
- Generated a synthetic payment network with accounts, merchants, devices, transactions,
  refunds, chargebacks, mule networks, collusive merchants, alerts, cases, and investigator
  workflows.
- Implemented rules-based, supervised, and graph-feature detection strategies, then evaluated
  them using fraud dollars missed, false-positive cost, investigator workload, ring-level
  recall, time-to-detection, and adversarial half-life.
- Built an executive-grade war-room dashboard with network graph evidence, active ring
  timelines, case queues, defense comparisons, and after-action reports.

## Limitations

The simulator is not a calibrated production model. It uses synthetic assumptions and should
be evaluated as a portfolio benchmark environment, not as a real fraud-control system.
