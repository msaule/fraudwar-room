from __future__ import annotations

from collections import defaultdict

from fraudwar.graph.engine import extract_account_graph_features
from fraudwar.schemas.entities import Alert, Transaction


class RulesEngine:
    name = "rules_baseline"

    def score(self, transactions: list[Transaction]) -> dict[str, float]:
        features = extract_account_graph_features(transactions)
        scores = {}
        for account_id, row in features.items():
            score = 0.0
            score += min(0.30, row["refund_ratio"] * 0.55)
            score += min(0.28, row["chargeback_ratio"] * 0.90)
            score += min(0.18, row["shared_device_count"] / 80)
            score += min(0.16, row["shared_ip_count"] / 90)
            score += 0.12 if row["avg_amount"] > 320 else 0.0
            score += 0.08 if row["tx_count"] > 20 else 0.0
            scores[account_id] = min(0.99, score)
        return scores

    def generate_alerts(self, transactions: list[Transaction], threshold: float = 0.42) -> list[Alert]:
        scores = self.score(transactions)
        grouped: dict[str, list[Transaction]] = defaultdict(list)
        for tx in transactions:
            grouped[tx.account_id].append(tx)
        alerts: list[Alert] = []
        for account_id, score in scores.items():
            if score < threshold:
                continue
            txs = grouped[account_id]
            fraud_txs = [tx for tx in txs if tx.fraud_label]
            exposure = sum(tx.amount for tx in txs)
            reason = "refund/chargeback velocity and shared infrastructure"
            alerts.append(
                Alert(
                    alert_id=f"alert_rules_{account_id}",
                    day=max(tx.day for tx in txs),
                    entity_id=account_id,
                    entity_type="account",
                    score=round(score, 4),
                    reason=reason,
                    dollar_exposure=round(exposure, 2),
                    ring_id=fraud_txs[0].ring_id if fraud_txs else None,
                    is_true_positive=bool(fraud_txs),
                )
            )
        return alerts

