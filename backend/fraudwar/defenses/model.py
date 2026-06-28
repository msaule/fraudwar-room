from __future__ import annotations

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from fraudwar.graph.engine import extract_account_graph_features
from fraudwar.schemas.entities import Transaction


FEATURE_COLUMNS = [
    "tx_count",
    "total_amount",
    "avg_amount",
    "refund_ratio",
    "chargeback_ratio",
    "shared_device_count",
    "shared_ip_count",
    "merchant_neighbor_load",
    "merchant_diversity",
    "device_diversity",
]


class TransactionModel:
    name = "supervised_transaction_model"

    def __init__(self) -> None:
        self.model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=400, class_weight="balanced"))

    def fit(self, transactions: list[Transaction]) -> "TransactionModel":
        x, y, _ = _matrix(transactions, graph_features=False)
        self.model.fit(x, y)
        return self

    def score(self, transactions: list[Transaction]) -> dict[str, float]:
        x, _, account_ids = _matrix(transactions, graph_features=False)
        probs = self.model.predict_proba(x)[:, 1]
        return dict(zip(account_ids, probs.tolist(), strict=False))


class GraphFeatureModel:
    name = "graph_feature_model"

    def __init__(self) -> None:
        self.model = HistGradientBoostingClassifier(max_iter=120, learning_rate=0.08, l2_regularization=0.05)

    def fit(self, transactions: list[Transaction]) -> "GraphFeatureModel":
        x, y, _ = _matrix(transactions, graph_features=True)
        self.model.fit(x, y)
        return self

    def score(self, transactions: list[Transaction]) -> dict[str, float]:
        x, _, account_ids = _matrix(transactions, graph_features=True)
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(x)[:, 1]
        else:
            probs = self.model.predict(x)
        return dict(zip(account_ids, probs.tolist(), strict=False))


def _matrix(
    transactions: list[Transaction],
    graph_features: bool,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    rows = extract_account_graph_features(transactions)
    labels = {}
    for tx in transactions:
        labels[tx.account_id] = max(labels.get(tx.account_id, 0), int(tx.fraud_label))
    columns = FEATURE_COLUMNS if graph_features else FEATURE_COLUMNS[:5]
    account_ids = sorted(rows)
    x = np.array([[rows[account_id].get(col, 0.0) for col in columns] for account_id in account_ids], dtype=float)
    y = np.array([labels.get(account_id, 0) for account_id in account_ids], dtype=int)
    if len(set(y.tolist())) < 2:
        y[0] = 1 - y[0]
    return x, y, account_ids

