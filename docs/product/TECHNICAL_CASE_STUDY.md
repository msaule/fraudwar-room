# FraudWar Room Case Study

## Problem

Most fraud demos score a static transaction file. That misses the operating problem: fraud
loss, false positives, review capacity, graph evidence, and drift all move together. A model
can look good on recall and still create a queue the team cannot work.

## Approach

FraudWar Room generates a closed synthetic payment network, runs detection policies, opens
cases, processes a limited review queue, records synthetic friction, and measures how recall
changes after behavior shifts. The project uses generated labels only for scoring. The
simulated reviewer never sees ground truth unless an experiment explicitly models labels.

## Architecture

- FastAPI exposes experiments, background jobs, run history, run payloads, benchmark reports,
  cases, rings, graph evidence, and health checks.
- SQLite stores run payloads, entity records, metric records, report paths, background jobs,
  and benchmark summaries.
- The simulator builds accounts, merchants, devices, IP clusters, payment instruments,
  transactions, refunds, chargebacks, disputes, rings, alerts, and cases.
- NetworkX builds the evidence graph and graph-derived account features.
- The Next.js dashboard loads the latest persisted run when the API is available and falls
  back to bundled demo data when it is not.

## Graph Model

The MVP uses graph features rather than a required graph neural network. Accounts are linked
to merchants, devices, IP clusters, payment instruments, transactions, cases, and rings.
Features include shared infrastructure, component behavior, neighborhood risk, refund and
chargeback context, and ring proximity. A PyTorch Geometric path exists as an optional
comparison, not as the core product.

## Metrics

The main readout is not a single AUC. The dashboard and reports track precision, recall,
blocked loss, missed loss, false-positive cost, backlog, SLA misses, investigator hours,
ring-level recall, recall decay, adversarial half-life, and investigator ROI.

## Product Surface

The dashboard can start a scenario through the API, poll a background job, load the persisted
run, inspect run history, open graph or case evidence, and compare multi-seed benchmark
variance. The same UI still works with bundled demo data if the API is not available.

## Safety Boundary

All data is synthetic. The simulator avoids real platform targeting, account takeover steps,
refund abuse instructions, credential theft, phishing, money laundering guidance, and real
customer or payment data. Adaptation events are abstract simulator changes, not operational
instructions.

## Tradeoffs

- SQLite keeps local setup simple. A production version would move run metadata and job
  status to Postgres and keep large graph payloads in object storage.
- FastAPI background tasks are enough for local runs. A production version would use a queue
  worker so jobs survive process restarts.
- The frontend can deploy independently, but live scenario runs need a reachable API.
- Synthetic assumptions make the benchmark useful for system design, not for claims about
  real fraud-control performance.

## Verification

Backend tests cover data generation, graph features, rules, metrics, queue processing,
adaptation, reports, optional providers, persistence, scenario jobs, and benchmark jobs.
Frontend tests cover the main dashboard routes, graph rendering, graph evidence drawer, and
case evidence drawer.
