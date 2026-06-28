# FraudWar Room: Evaluating Fraud Defenses Against Adaptive Synthetic Fraud Rings

## Abstract

Fraud detection is commonly evaluated as static binary classification. FraudWar Room frames
fraud defense as an adversarial operations problem: synthetic rings generate activity,
defenses create friction, investigators operate under capacity constraints, and rings adapt
abstractly after detection. The benchmark reports transaction metrics, graph/ring metrics,
financial impact, investigator workload, and adversarial resilience.

## Problem

Static fraud labels do not capture three operational realities:

- Fraud is coordinated across accounts, merchants, devices, and infrastructure.
- False positives consume investigator capacity and can harm legitimate users.
- Adversaries change behavior after controls create friction.

## FraudArena

FraudArena is a closed-world synthetic environment:

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

## Synthetic Data

The simulator generates customers, accounts, payment instruments, devices, IP clusters,
merchants, transactions, refunds, chargebacks, disputes, support contacts, account changes,
fraud rings, alerts, cases, investigators, graph evidence, and reports. Labels are synthetic
ground truth for benchmark evaluation.

## Defenses

The MVP evaluates rules, supervised transaction features, graph features, active learning
under simulated labels, and adaptive thresholding under queue pressure. An optional PyTorch
Geometric GCN is available through `PyGGraphNeuralNetwork` for environments that install the
`backend[gnn]` extra.

## Metrics

Key metrics include precision, recall, AUPRC, fraud dollars blocked, false-positive cost,
backlog, SLA misses, ring-level recall, adversarial half-life, and investigator ROI.

## Safety

FraudWar Room is defensive and synthetic only. It does not include real customer data,
platform-specific evasion, credential theft, phishing, social engineering, or steps for
committing fraud.

## Limitations

The environment is not calibrated to a production financial institution. Synthetic behavior
is useful for evaluating system design tradeoffs, not for claiming real-world fraud-control
performance.
