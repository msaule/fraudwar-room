from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import numpy as np

from fraudwar.graph.engine import extract_account_graph_features
from fraudwar.schemas.entities import Transaction


class OptionalDependencyError(RuntimeError):
    """Raised when an optional model backend is requested without its dependencies."""


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


@dataclass
class GNNTrainingDiagnostics:
    epochs: int
    node_count: int
    edge_count: int
    positive_labels: int
    backend: str = "torch_geometric"


class PyGGraphNeuralNetwork:
    """Optional PyTorch Geometric account-level GCN defense.

    This is a real GNN implementation path, but it is deliberately optional because PyTorch
    and PyTorch Geometric are heavyweight dependencies for the default local run. Install the
    `gnn` extra to use it:

    ```bash
    pip install -e "backend[gnn]"
    ```
    """

    name = "pyg_gcn_account_model"

    def __init__(self, epochs: int = 80, learning_rate: float = 0.01, hidden_channels: int = 16):
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.hidden_channels = hidden_channels
        self.account_ids: list[str] = []
        self.model = None
        self.diagnostics: GNNTrainingDiagnostics | None = None

    @staticmethod
    def is_available() -> bool:
        try:
            import torch  # noqa: F401
            from torch_geometric.data import Data  # noqa: F401
            from torch_geometric.nn import GCNConv  # noqa: F401
        except Exception:
            return False
        return True

    def fit(self, transactions: list[Transaction]) -> "PyGGraphNeuralNetwork":
        torch, Data, GCNConv = _import_pyg()
        x, y, edge_index, account_ids = _build_graph_tensors(transactions, torch, Data)
        data = Data(x=x, edge_index=edge_index, y=y)
        model = _AccountGCN(
            GCNConv=GCNConv,
            in_channels=x.shape[1],
            hidden_channels=self.hidden_channels,
        )
        optimizer = torch.optim.Adam(model.parameters(), lr=self.learning_rate, weight_decay=5e-4)
        loss_fn = torch.nn.BCEWithLogitsLoss(pos_weight=_positive_weight(y, torch))
        model.train()
        for _ in range(self.epochs):
            optimizer.zero_grad()
            logits = model(data.x, data.edge_index).view(-1)
            loss = loss_fn(logits, data.y.float())
            loss.backward()
            optimizer.step()
        self.model = model
        self.account_ids = account_ids
        self.diagnostics = GNNTrainingDiagnostics(
            epochs=self.epochs,
            node_count=len(account_ids),
            edge_count=int(edge_index.shape[1]),
            positive_labels=int(y.sum().item()),
        )
        return self

    def score(self, transactions: list[Transaction]) -> dict[str, float]:
        if self.model is None:
            raise RuntimeError("PyGGraphNeuralNetwork must be fit before score.")
        torch, Data, _ = _import_pyg()
        x, _, edge_index, account_ids = _build_graph_tensors(transactions, torch, Data)
        data = Data(x=x, edge_index=edge_index)
        self.model.eval()
        with torch.no_grad():
            logits = self.model(data.x, data.edge_index).view(-1)
            probs = torch.sigmoid(logits).cpu().numpy().tolist()
        return dict(zip(account_ids, probs, strict=False))


class GNNStretchModel(PyGGraphNeuralNetwork):
    """Backward-compatible name for the optional PyG GCN defense."""


def _import_pyg():
    try:
        import torch
        from torch_geometric.data import Data
        from torch_geometric.nn import GCNConv
    except Exception as exc:
        raise OptionalDependencyError(
            "PyTorch Geometric GNN support is optional. Install with "
            '`pip install -e "backend[gnn]"` to enable PyGGraphNeuralNetwork.'
        ) from exc
    return torch, Data, GCNConv


def _build_graph_tensors(transactions: list[Transaction], torch, Data):
    del Data
    features = extract_account_graph_features(transactions)
    labels = {}
    for tx in transactions:
        labels[tx.account_id] = max(labels.get(tx.account_id, 0), int(tx.fraud_label))
    account_ids = sorted(features)
    if not account_ids:
        raise ValueError("Cannot build a GNN graph without transactions.")
    raw_x = np.array(
        [[features[account_id].get(column, 0.0) for column in FEATURE_COLUMNS] for account_id in account_ids],
        dtype=np.float32,
    )
    scale = np.maximum(raw_x.std(axis=0), 1e-6)
    x = torch.tensor((raw_x - raw_x.mean(axis=0)) / scale, dtype=torch.float32)
    y = torch.tensor([labels.get(account_id, 0) for account_id in account_ids], dtype=torch.float32)
    account_index = {account_id: idx for idx, account_id in enumerate(account_ids)}
    edges = _account_edges(transactions, account_index)
    if not edges:
        edges = [(idx, idx) for idx in range(len(account_ids))]
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    return x, y, edge_index, account_ids


def _account_edges(transactions: list[Transaction], account_index: dict[str, int]) -> list[tuple[int, int]]:
    device_accounts: dict[str, set[str]] = defaultdict(set)
    ip_accounts: dict[str, set[str]] = defaultdict(set)
    merchant_accounts: dict[str, set[str]] = defaultdict(set)
    for tx in transactions:
        device_accounts[tx.device_id].add(tx.account_id)
        ip_accounts[tx.ip_cluster_id].add(tx.account_id)
        merchant_accounts[tx.merchant_id].add(tx.account_id)
    edges: set[tuple[int, int]] = set()
    for groups in [device_accounts, ip_accounts, merchant_accounts]:
        for account_ids in groups.values():
            if len(account_ids) < 2 or len(account_ids) > 80:
                continue
            indexed = [account_index[account_id] for account_id in account_ids if account_id in account_index]
            for left in indexed:
                for right in indexed:
                    if left != right:
                        edges.add((left, right))
    for idx in range(len(account_index)):
        edges.add((idx, idx))
    return sorted(edges)


def _positive_weight(y, torch):
    positives = float(y.sum().item())
    negatives = max(1.0, float(y.shape[0]) - positives)
    if positives <= 0:
        return torch.tensor(1.0)
    return torch.tensor(negatives / positives, dtype=torch.float32)


class _AccountGCN:
    def __new__(cls, GCNConv, in_channels: int, hidden_channels: int):
        torch, _, _ = _import_pyg()

        class AccountGCN(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.conv1 = GCNConv(in_channels, hidden_channels)
                self.conv2 = GCNConv(hidden_channels, 1)

            def forward(self, x, edge_index):
                x = self.conv1(x, edge_index).relu()
                x = self.conv2(x, edge_index)
                return x

        return AccountGCN()
