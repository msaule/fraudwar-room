# Experiments

## 1. Static Fraud vs Adaptive Fraud

Train defenses on early synthetic behavior, then evaluate later behavior as rings adapt
after synthetic defensive friction.

## 2. Transaction Model vs Graph Model

Compare transaction-only features against graph-feature defenses. Primary metrics are
ring-level recall, time to first detection, and investigator ROI.

## 3. Recall vs Investigator Overload

Lower alert thresholds to increase recall, then measure backlog, false positives, and SLA
misses.

## 4. Ring Takedown vs Account Takedown

Compare account-priority review against ring-priority review.

## 5. Active Learning Under Drift

Simulate investigator labels feeding into retraining cadence. MVP documents the experiment
and implements one retraining event using synthetic investigator labels from the first test
window.

## 6. Adaptive Thresholding

Select a score threshold from the alert budget instead of using a fixed cutoff. The experiment
measures projected queue pressure and compares the resulting alerts against fixed-threshold
defenses.
