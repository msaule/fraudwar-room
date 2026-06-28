# Metrics

## Standard Classification

- `precision = true_positive_alerts / all_alerts`
- `recall = true_positive_alerts / fraud_entities`
- `F1 = 2 * precision * recall / (precision + recall)`
- `AUROC`: ranking quality across thresholds.
- `AUPRC`: preferred for imbalanced fraud settings.
- `precision_at_top_k`: true positives in top K ranked alerts.
- `recall_at_alert_budget`: recall achieved under a fixed alert budget.

## Financial Impact

- `fraud_dollars_attempted = sum(amount for fraud transactions)`
- `fraud_dollars_blocked = sum(amount for fraud transactions on alerted entities)`
- `fraud_dollars_missed = fraud_dollars_attempted - fraud_dollars_blocked`
- `false_positive_cost = false_positive_cases * false_positive_unit_cost`
- `review_cost = investigator_hours * hourly_cost`
- `net_savings = fraud_dollars_blocked - false_positive_cost - review_cost`

## Operations

- `alerts_per_1000_transactions = alerts / transactions * 1000`
- `cases_opened = count(cases)`
- `true_cases = cases linked to fraud labels`
- `false_positive_cases = cases not linked to fraud labels`
- `investigator_hours_used = reviewed_cases * review_hours_per_case`
- `backlog = cases_opened - reviewed_cases`
- `sla_missed = max(0, backlog - daily_capacity)`

## Ring-Level Recall

Ring-level recall is the percentage of fraud rings for which the defense identifies enough
connected entities to justify ring-level investigation or disruption.

```text
ring_level_recall = detected_rings / total_rings
```

A ring is detected when a configurable minimum number or percentage of its member accounts
are alerted.

## Adversarial Half-Life

Adversarial half-life is the number of simulation rounds it takes for effectiveness to fall
by 50 percent after rings begin adapting.

```text
target = initial_recall / 2
half_life = first interpolated day where recall <= target
```

If recall never falls to half, the system reports infinity.

## Investigator ROI

```text
investigator_roi =
  (prevented_fraud_loss - false_positive_cost - review_cost) / investigator_hours
```

Reported as dollars saved per investigator-hour.

