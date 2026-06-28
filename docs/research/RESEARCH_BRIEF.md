# FraudWar Room Research Brief

FraudWar Room uses synthetic data and abstract adversarial behavior for defensive research,
analytics, and product testing. It is not a guide to committing fraud and must not
be used to facilitate abuse.

## Executive Takeaways

Static fraud modeling is useful but incomplete. Current research and commercial products
show three important patterns:

- Financial-crime systems increasingly combine transaction scoring, graph/network evidence,
  case management, and operations metrics.
- Research datasets and benchmarks remain mostly static. They rarely model investigator
  capacity, false-positive harm, ring-level disruption, and post-detection adversarial drift
  in one environment.
- Commercial platforms communicate real-time decisions, behavioral analytics, alert
  reduction, and investigation workflow, but their evaluation environments are proprietary.

FraudWar Room should differentiate through FraudArena: a reproducible closed-world simulator
where synthetic rings adapt after defensive friction and defenses are evaluated on money,
operations, graph linkage, and recall decay.

## Sources Inspected

- Feedzai risk operations and fraud prevention: https://feedzai.com/
- Featurespace ARIC Risk Hub and adaptive behavioral analytics: https://www.featurespace.com/
- FICO Falcon Fraud Manager: https://www.fico.com/en/products/fico-falcon-fraud-manager
- NICE Actimize fraud management and financial crime operations: https://www.niceactimize.com/
- SAS fraud management: https://www.sas.com/en_us/software/fraud-management.html
- Palantir financial services and AML positioning: https://www.palantir.com/industries/financial-services/
- IBM AMLSim synthetic transaction simulator: https://github.com/IBM/AMLSim
- Elliptic Bitcoin transaction graph dataset paper: https://arxiv.org/abs/1908.02591
- DGraph financial graph anomaly dataset: https://arxiv.org/abs/2207.03579
- PaySim mobile money simulator: https://www.kaggle.com/datasets/ealaxi/paysim1
- Credit card fraud cost-sensitive learning survey entry point: https://ieeexplore.ieee.org/document/9451544
- Scikit-learn precision/recall and average precision documentation:
  https://scikit-learn.org/stable/modules/model_evaluation.html
- NetworkX graph analytics documentation: https://networkx.org/documentation/stable/

## Research Method Table

| Area | What exists | Static or adaptive | Investigator model | False-positive burden | Ring-level detection | Gap for FraudWar Room |
| --- | --- | --- | --- | --- | --- | --- |
| Credit-card fraud classifiers | Logistic regression, tree ensembles, gradient boosting, deep learning | Usually static | Rare | Sometimes via cost models | Rare | Add operations and adaptation |
| Graph fraud detection | GNNs, heterogeneous graphs, shared devices/IPs, bipartite account-merchant graphs | Usually static | Rare | Rare | Sometimes node/community metrics | Make graph evidence actionable in cases |
| Synthetic AML generation | AMLSim and AMLNet-like synthetic transaction work | Generated but often static | No | No | AML typology labels | Add adaptation and investigator queues |
| Public graph datasets | Elliptic, DGraph-Fin style benchmarks | Static snapshots | No | No | Node/edge classification focus | Evaluate ring disruption, not just AUC |
| Commercial platforms | Real-time scoring, case queues, graph investigation, alert reduction | Adaptive analytics claimed, proprietary | Yes | Yes | Product-dependent | Build transparent open simulator |

## Competitor Table

| Tool | High-level positioning | What to learn | What not to copy |
| --- | --- | --- | --- |
| Feedzai | Risk operations for fraud and financial crime | Real-time decisions, explainability, analyst workflows | Proprietary claims or brand language |
| Featurespace | Adaptive behavioral analytics through ARIC Risk Hub | Behavioral baselines and adaptive scoring | Vendor-specific architecture |
| FICO Falcon | Enterprise card/payment fraud decisioning | Mature transaction scoring and decision orchestration | Card-network-specific assumptions |
| NICE Actimize | Financial crime, fraud, AML, case management | Investigation queues and operational dashboards | Compliance-heavy enterprise scope for MVP |
| SAS Fraud Management | Enterprise fraud detection and analytics | Cost/risk analytics, alert triage, enterprise reporting | Overbroad platform surface |
| Palantir financial crime | Graph-centric investigation and data integration | Entity resolution, graph evidence, investigation workspace | Any implication of access to real bank data |

## Recent Graph and Simulation Research

Public graph fraud research is useful for feature inspiration but does not fully solve the
product question. Elliptic and DGraph-style datasets benchmark graph anomaly detection on
financial networks, but they remain static. GNN literature improves node or edge
classification; FraudWar Room uses NetworkX graph features for MVP because the benchmark
environment matters more than the model family.

AMLSim and related synthetic AML work show that transaction networks can be generated
without real customer data. FraudWar Room should borrow the defensive synthetic-data
discipline, but broaden evaluation to investigator capacity, graph evidence, and adaptive
ring behavior.

The prompt mentions SAGE and MultiAgentFraudBench-like frameworks. I did not treat those as
validated canonical sources without a stable source URL in this pass. They remain research
targets for follow-up inspection. The core loop should be deterministic and auditable.

## Evaluation Methodology

Classification metrics are necessary but insufficient:

- Precision, recall, F1, AUROC, and AUPRC describe account or transaction detection.
- Cost-sensitive metrics capture fraud dollars blocked, fraud dollars missed, false-positive
  cost, review cost, and net savings.
- Operations metrics capture alerts per 1,000 transactions, cases opened, backlog, SLA missed,
  and investigator hours used.
- Graph/ring metrics capture ring-level recall, time to first detection, time to ring linkage,
  and investigator hours per ring detected.
- Adversarial metrics capture pre/post adaptation recall, recall decay, adversarial half-life,
  brittleness score, and robustness index.

## Gap Analysis

Many public demos train on a static fraud CSV and display AUC. That misses the operating
problem. Commercial platforms handle operations more seriously, but their evaluation
environments are closed. Academic benchmarks help model design but rarely include review
capacity and adaptive response.

FraudWar Room can be genuinely different by making the arena the primitive:

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

## Recommended MVP Scope

- Synthetic accounts, merchants, devices, IP clusters, transactions, refunds, chargebacks, and
  fraud rings.
- Abstract ring adaptation after synthetic defensive friction.
- Rules baseline, supervised transaction model, and graph-feature model.
- Investigator queue with capacity and backlog.
- Ring-level recall, adversarial half-life, and investigator ROI.
- Run memo and dashboard backed by generated data.

## What To Avoid

- Real platform evasion, refund abuse instructions, account takeover instructions, money
  laundering guidance, phishing, credential theft, or dark-web content.
- A dashboard that is only static cards with fake numbers.
- Provider-generated case conclusions as the core product.
- Claims that the simulator prevents real fraud.

## How To Stay Non-Generic

Lead every demo with the adaptive loop:

1. The ring emerges in a synthetic payment network.
2. The defense catches transactions.
3. Investigators create friction under capacity constraints.
4. The ring adapts abstractly.
5. The system reports whether defense effectiveness decays.
