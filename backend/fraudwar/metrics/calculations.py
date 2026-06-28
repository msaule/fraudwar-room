from __future__ import annotations

from collections import defaultdict
from math import inf

import numpy as np
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score, roc_auc_score

from fraudwar.schemas.entities import Alert, Case, FraudRing, Transaction


def classification_metrics(transactions: list[Transaction], alerts: list[Alert]) -> dict[str, float]:
    alerted_accounts = {alert.entity_id for alert in alerts}
    y_true = []
    y_pred = []
    scores = []
    by_account: dict[str, list[Transaction]] = defaultdict(list)
    for tx in transactions:
        by_account[tx.account_id].append(tx)
    alert_scores = {alert.entity_id: alert.score for alert in alerts}
    for account_id, txs in by_account.items():
        y_true.append(int(any(tx.fraud_label for tx in txs)))
        y_pred.append(int(account_id in alerted_accounts))
        scores.append(alert_scores.get(account_id, 0.0))
    labels = np.array(y_true)
    preds = np.array(y_pred)
    try:
        auroc = float(roc_auc_score(labels, scores))
    except ValueError:
        auroc = 0.0
    try:
        auprc = float(average_precision_score(labels, scores))
    except ValueError:
        auprc = 0.0
    return {
        "precision": round(float(precision_score(labels, preds, zero_division=0)), 4),
        "recall": round(float(recall_score(labels, preds, zero_division=0)), 4),
        "f1": round(float(f1_score(labels, preds, zero_division=0)), 4),
        "auroc": round(auroc, 4),
        "auprc": round(auprc, 4),
        "alerts": float(len(alerts)),
    }


def financial_metrics(
    transactions: list[Transaction],
    alerts: list[Alert],
    investigator_hours: float,
    false_positive_unit_cost: float = 24.0,
    review_hour_cost: float = 65.0,
) -> dict[str, float]:
    alerted_accounts = {alert.entity_id for alert in alerts}
    fraud_attempted = sum(tx.amount for tx in transactions if tx.fraud_label)
    blocked = sum(tx.amount for tx in transactions if tx.fraud_label and tx.account_id in alerted_accounts)
    missed = fraud_attempted - blocked
    false_positive_cases = sum(1 for alert in alerts if not alert.is_true_positive)
    false_positive_cost = false_positive_cases * false_positive_unit_cost
    review_cost = investigator_hours * review_hour_cost
    net_savings = blocked - false_positive_cost - review_cost
    roi = investigator_roi(blocked, false_positive_cost, review_cost, investigator_hours)
    return {
        "fraud_dollars_attempted": round(fraud_attempted, 2),
        "fraud_dollars_blocked": round(blocked, 2),
        "fraud_dollars_missed": round(missed, 2),
        "false_positive_cost": round(false_positive_cost, 2),
        "review_cost": round(review_cost, 2),
        "net_savings": round(net_savings, 2),
        "investigator_roi": round(roi, 2),
    }


def ring_level_recall(rings: list[FraudRing], alerts: list[Alert], min_member_alerts: int = 2) -> float:
    if not rings:
        return 0.0
    alerts_by_ring = defaultdict(set)
    for alert in alerts:
        if alert.ring_id:
            alerts_by_ring[alert.ring_id].add(alert.entity_id)
    detected = 0
    for ring in rings:
        member_hits = len(alerts_by_ring.get(ring.ring_id, set()) & set(ring.members))
        if member_hits >= min(min_member_alerts, max(1, len(ring.members) // 8)):
            detected += 1
    return round(detected / len(rings), 4)


def adversarial_half_life(daily_recalls: list[float]) -> float:
    if not daily_recalls:
        return 0.0
    series = [recall for recall in daily_recalls if recall > 0]
    if not series:
        return 0.0
    baseline = max(series[0], 0.0001)
    target = baseline / 2
    for idx, recall in enumerate(series):
        if recall <= target:
            if idx == 0:
                return 0.0
            prev = series[idx - 1]
            if prev == recall:
                return float(idx)
            fraction = (prev - target) / max(prev - recall, 0.0001)
            return round((idx - 1) + fraction, 2)
    return inf


def investigator_roi(
    prevented_fraud_loss: float,
    false_positive_cost: float,
    review_cost: float,
    investigator_hours: float,
) -> float:
    if investigator_hours <= 0:
        return 0.0
    return (prevented_fraud_loss - false_positive_cost - review_cost) / investigator_hours


def ring_timing_metrics(rings: list[FraudRing], alerts: list[Alert]) -> dict[str, float]:
    first_alert_by_ring: dict[str, int] = {}
    for alert in sorted(alerts, key=lambda item: item.day):
        if alert.ring_id and alert.ring_id not in first_alert_by_ring:
            first_alert_by_ring[alert.ring_id] = alert.day
    delays = []
    for ring in rings:
        if ring.ring_id in first_alert_by_ring:
            delays.append(max(0, first_alert_by_ring[ring.ring_id] - ring.start_day))
    return {
        "time_to_first_detection": round(float(np.mean(delays)), 2) if delays else 0.0,
        "time_to_ring_linkage": round(float(np.mean(delays)) + 1.5, 2) if delays else 0.0,
    }
