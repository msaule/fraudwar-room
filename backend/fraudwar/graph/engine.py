from __future__ import annotations

from collections import Counter, defaultdict

import networkx as nx

from fraudwar.schemas.entities import (
    Account,
    AccountChange,
    Case,
    Chargeback,
    Dispute,
    FraudRing,
    Merchant,
    PaymentInstrument,
    Refund,
    SupportContact,
    Transaction,
)


def build_evidence_graph(
    accounts: list[Account],
    merchants: list[Merchant],
    transactions: list[Transaction],
    rings: list[FraudRing],
    payment_instruments: list[PaymentInstrument] | None = None,
    refunds: list[Refund] | None = None,
    chargebacks: list[Chargeback] | None = None,
    disputes: list[Dispute] | None = None,
    support_contacts: list[SupportContact] | None = None,
    account_changes: list[AccountChange] | None = None,
    cases: list[Case] | None = None,
    max_transactions: int = 5000,
) -> nx.Graph:
    graph = nx.Graph()
    for account in accounts:
        graph.add_node(
            account.account_id,
            kind="account",
            ring_id=account.fraud_ring_id,
            risk_segment=account.risk_segment,
        )
    for merchant in merchants:
        graph.add_node(merchant.merchant_id, kind="merchant", category=merchant.category)
    for payment in payment_instruments or []:
        graph.add_node(
            payment.payment_instrument_id,
            kind="payment_instrument",
            instrument_type=payment.instrument_type,
        )
        graph.add_edge(payment.account_id, payment.payment_instrument_id, edge_type="owns-payment-instrument")
    for ring in rings:
        graph.add_node(ring.ring_id, kind="ring", ring_type=ring.ring_type.value)
        for account_id in ring.members:
            graph.add_edge(ring.ring_id, account_id, edge_type="ring-member")
        for merchant_id in ring.merchants:
            graph.add_edge(ring.ring_id, merchant_id, edge_type="ring-merchant")
    for tx in transactions[:max_transactions]:
        graph.add_node(
            tx.transaction_id,
            kind="transaction",
            amount=tx.amount,
            fraud_label=tx.fraud_label,
            ring_id=tx.ring_id,
        )
        graph.add_node(tx.device_id, kind="device")
        graph.add_node(tx.ip_cluster_id, kind="ip_cluster")
        graph.add_edge(tx.account_id, tx.merchant_id, edge_type="transacted-with", amount=tx.amount)
        graph.add_edge(tx.account_id, tx.transaction_id, edge_type="initiated-transaction")
        graph.add_edge(tx.transaction_id, tx.merchant_id, edge_type="transaction-at-merchant")
        graph.add_edge(tx.transaction_id, tx.payment_instrument_id, edge_type="transaction-used-payment")
        graph.add_edge(tx.account_id, tx.device_id, edge_type="used-device")
        graph.add_edge(tx.account_id, tx.ip_cluster_id, edge_type="used-ip-cluster")
    for refund in refunds or []:
        graph.add_node(refund.refund_id, kind="refund", amount=refund.amount, ring_id=refund.ring_id)
        graph.add_edge(refund.transaction_id, refund.refund_id, edge_type="transaction-refunded")
        graph.add_edge(refund.account_id, refund.refund_id, edge_type="account-requested-refund")
    for chargeback in chargebacks or []:
        graph.add_node(
            chargeback.chargeback_id,
            kind="chargeback",
            amount=chargeback.amount,
            ring_id=chargeback.ring_id,
        )
        graph.add_edge(chargeback.transaction_id, chargeback.chargeback_id, edge_type="transaction-chargeback")
        graph.add_edge(chargeback.account_id, chargeback.chargeback_id, edge_type="account-filed-chargeback")
    for dispute in disputes or []:
        graph.add_node(dispute.dispute_id, kind="dispute", amount=dispute.amount, ring_id=dispute.ring_id)
        graph.add_edge(dispute.transaction_id, dispute.dispute_id, edge_type="transaction-disputed")
        graph.add_edge(dispute.account_id, dispute.dispute_id, edge_type="account-opened-dispute")
    for contact in support_contacts or []:
        graph.add_node(contact.support_contact_id, kind="support_contact", topic=contact.topic)
        graph.add_edge(contact.account_id, contact.support_contact_id, edge_type="account-contacted-support")
        if contact.linked_transaction_id:
            graph.add_edge(
                contact.linked_transaction_id,
                contact.support_contact_id,
                edge_type="support-linked-transaction",
            )
    for change in account_changes or []:
        graph.add_node(change.account_change_id, kind="account_change", change_type=change.change_type)
        graph.add_edge(change.account_id, change.account_change_id, edge_type="account-change")
        if change.device_id:
            graph.add_edge(change.account_change_id, change.device_id, edge_type="change-device")
        if change.ip_cluster_id:
            graph.add_edge(change.account_change_id, change.ip_cluster_id, edge_type="change-ip")
    for case in cases or []:
        graph.add_node(case.case_id, kind="case", ring_id=case.ring_id, priority_score=case.priority_score)
        for account_id in case.account_ids:
            graph.add_edge(case.case_id, account_id, edge_type="case-account")
        for merchant_id in case.merchant_ids:
            graph.add_edge(case.case_id, merchant_id, edge_type="case-merchant")
    return graph


def extract_account_graph_features(transactions: list[Transaction]) -> dict[str, dict[str, float]]:
    account_tx: dict[str, list[Transaction]] = defaultdict(list)
    device_accounts: dict[str, set[str]] = defaultdict(set)
    ip_accounts: dict[str, set[str]] = defaultdict(set)
    merchant_accounts: dict[str, set[str]] = defaultdict(set)
    for tx in transactions:
        account_tx[tx.account_id].append(tx)
        device_accounts[tx.device_id].add(tx.account_id)
        ip_accounts[tx.ip_cluster_id].add(tx.account_id)
        merchant_accounts[tx.merchant_id].add(tx.account_id)

    shared_device = Counter()
    shared_ip = Counter()
    merchant_degree = Counter()
    for accounts in device_accounts.values():
        if len(accounts) > 1:
            for account_id in accounts:
                shared_device[account_id] += len(accounts) - 1
    for accounts in ip_accounts.values():
        if len(accounts) > 1:
            for account_id in accounts:
                shared_ip[account_id] += len(accounts) - 1
    for accounts in merchant_accounts.values():
        for account_id in accounts:
            merchant_degree[account_id] += len(accounts)

    features = {}
    for account_id, txs in account_tx.items():
        total = len(txs)
        amount = sum(tx.amount for tx in txs)
        features[account_id] = {
            "tx_count": float(total),
            "total_amount": float(amount),
            "avg_amount": float(amount / total),
            "refund_ratio": sum(tx.refunded for tx in txs) / total,
            "chargeback_ratio": sum(tx.chargeback for tx in txs) / total,
            "shared_device_count": float(shared_device[account_id]),
            "shared_ip_count": float(shared_ip[account_id]),
            "merchant_neighbor_load": float(merchant_degree[account_id]),
            "merchant_diversity": float(len({tx.merchant_id for tx in txs})),
            "device_diversity": float(len({tx.device_id for tx in txs})),
        }
    return features


def graph_payload(graph: nx.Graph, limit_nodes: int = 240) -> dict[str, list[dict]]:
    def priority(item: tuple[str, dict]) -> tuple[int, int]:
        node_id, data = item
        kind = data.get("kind", "entity")
        rank = {
            "ring": 0,
            "account": 1,
            "merchant": 2,
            "case": 3,
            "transaction": 4,
            "payment_instrument": 5,
            "device": 6,
            "ip_cluster": 7,
            "refund": 8,
            "chargeback": 9,
            "dispute": 10,
            "support_contact": 11,
            "account_change": 12,
        }.get(kind, 5)
        ring_bonus = 0 if data.get("ring_id") else 1
        return (rank + ring_bonus, -graph.degree(node_id))

    by_type: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for node in graph.nodes(data=True):
        by_type[node[1].get("kind", "entity")].append(node)
    type_order = [
        "ring",
        "case",
        "account",
        "merchant",
        "transaction",
        "payment_instrument",
        "device",
        "ip_cluster",
        "refund",
        "chargeback",
        "dispute",
        "support_contact",
        "account_change",
    ]
    quotas = {
        "ring": 18,
        "case": 24,
        "account": 54,
        "merchant": 24,
        "transaction": 34,
        "payment_instrument": 22,
        "device": 18,
        "ip_cluster": 16,
        "refund": 10,
        "chargeback": 8,
        "dispute": 6,
        "support_contact": 4,
        "account_change": 2,
    }
    selected: list[tuple[str, dict]] = []
    seen: set[str] = set()
    for kind in type_order:
        for node_id, data in sorted(by_type.get(kind, []), key=priority)[: quotas.get(kind, 0)]:
            if node_id in seen:
                continue
            selected.append((node_id, data))
            seen.add(node_id)
            if len(selected) >= limit_nodes:
                break
        if len(selected) >= limit_nodes:
            break
    if len(selected) < limit_nodes:
        for node_id, data in sorted(graph.nodes(data=True), key=priority):
            if node_id in seen:
                continue
            selected.append((node_id, data))
            seen.add(node_id)
            if len(selected) >= limit_nodes:
                break
    nodes = selected
    included = {node_id for node_id, _ in nodes}
    edges = [
        {"source": u, "target": v, "type": data.get("edge_type", "linked")}
        for u, v, data in graph.edges(data=True)
        if u in included and v in included
    ][:420]
    return {
        "nodes": [
            {
                "id": node_id,
                "label": node_id,
                "type": data.get("kind", "entity"),
                "ring_id": data.get("ring_id"),
                "risk": data.get("priority_score") or data.get("amount") or data.get("risk_segment"),
            }
            for node_id, data in nodes
        ],
        "edges": edges,
    }
