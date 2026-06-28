from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass

import numpy as np

from fraudwar.schemas.entities import (
    Account,
    AccountChange,
    Chargeback,
    Customer,
    Device,
    Dispute,
    FraudRing,
    IpCluster,
    Merchant,
    MerchantCategory,
    PaymentInstrument,
    Refund,
    RingType,
    SupportContact,
    Transaction,
)


PERSONAS = [
    "normal_consumer",
    "high_spend_traveler",
    "small_business_buyer",
    "seasonal_shopper",
    "refund_heavy_legitimate",
    "new_account_legitimate_growth",
    "subscription_heavy_user",
    "cross_border_legitimate_user",
]
CATEGORIES = [
    "electronics",
    "travel",
    "apparel",
    "home",
    "digital_goods",
    "marketplace",
    "grocery",
    "subscription",
    "luxury",
]
REGIONS = ["NA", "EU", "LATAM", "APAC"]
CHANNELS = ["web", "mobile", "in_app", "api"]
RING_TYPES = list(RingType)


@dataclass(frozen=True)
class SyntheticWorld:
    customers: list[Customer]
    accounts: list[Account]
    payment_instruments: list[PaymentInstrument]
    devices: list[Device]
    ip_clusters: list[IpCluster]
    merchant_categories: list[MerchantCategory]
    merchants: list[Merchant]
    rings: list[FraudRing]
    transactions: list[Transaction]
    refunds: list[Refund]
    chargebacks: list[Chargeback]
    disputes: list[Dispute]
    support_contacts: list[SupportContact]
    account_changes: list[AccountChange]

    def as_dict(self) -> dict[str, list[dict]]:
        return {
            "customers": [c.model_dump() for c in self.customers],
            "accounts": [a.model_dump() for a in self.accounts],
            "payment_instruments": [p.model_dump() for p in self.payment_instruments],
            "devices": [d.model_dump() for d in self.devices],
            "ip_clusters": [i.model_dump() for i in self.ip_clusters],
            "merchant_categories": [c.model_dump() for c in self.merchant_categories],
            "merchants": [m.model_dump() for m in self.merchants],
            "rings": [r.model_dump() for r in self.rings],
            "transactions": [t.model_dump() for t in self.transactions],
            "refunds": [r.model_dump() for r in self.refunds],
            "chargebacks": [c.model_dump() for c in self.chargebacks],
            "disputes": [d.model_dump() for d in self.disputes],
            "support_contacts": [s.model_dump() for s in self.support_contacts],
            "account_changes": [a.model_dump() for a in self.account_changes],
        }


def generate_world(
    seed: int = 42,
    accounts: int = 10_000,
    merchants: int = 500,
    transactions: int = 100_000,
    rings: int = 10,
    days: int = 30,
) -> SyntheticWorld:
    """Generate a closed-world synthetic payment network.

    Ring behavior is abstract and parameterized. The generator deliberately avoids real-world
    operational detail and produces labels only for defensive evaluation.
    """

    rng = np.random.default_rng(seed)
    random.seed(seed)
    merchant_rows = _generate_merchants(rng, merchants)
    category_rows = _generate_merchant_categories()
    account_rows = _generate_accounts(rng, accounts, days)
    customer_rows = _generate_customers(account_rows)
    ring_rows = _generate_rings(rng, ring_count=rings, accounts=account_rows, merchants=merchant_rows)
    by_account_ring = {member: ring.ring_id for ring in ring_rows for member in ring.members}
    account_rows = [
        account.model_copy(update={"fraud_ring_id": by_account_ring.get(account.account_id)})
        for account in account_rows
    ]
    merchant_map = {merchant.merchant_id: merchant for merchant in merchant_rows}
    ring_map = {ring.ring_id: ring for ring in ring_rows}
    tx_rows = _generate_transactions(
        rng,
        n=transactions,
        days=days,
        accounts=account_rows,
        merchants=merchant_rows,
        merchant_map=merchant_map,
        ring_map=ring_map,
    )
    payment_rows = _generate_payment_instruments(account_rows)
    device_rows = _generate_devices(account_rows, tx_rows)
    ip_rows = _generate_ip_clusters(tx_rows)
    refund_rows = _generate_refunds(tx_rows)
    chargeback_rows = _generate_chargebacks(tx_rows)
    dispute_rows = _generate_disputes(tx_rows)
    support_rows = _generate_support_contacts(rng, tx_rows, account_rows)
    change_rows = _generate_account_changes(rng, account_rows, tx_rows, days)
    return SyntheticWorld(
        customers=customer_rows,
        accounts=account_rows,
        payment_instruments=payment_rows,
        devices=device_rows,
        ip_clusters=ip_rows,
        merchant_categories=category_rows,
        merchants=merchant_rows,
        rings=ring_rows,
        transactions=tx_rows,
        refunds=refund_rows,
        chargebacks=chargeback_rows,
        disputes=dispute_rows,
        support_contacts=support_rows,
        account_changes=change_rows,
    )


def _generate_customers(accounts: list[Account]) -> list[Customer]:
    return [
        Customer(
            customer_id=account.customer_id,
            region=account.region,
            legitimate_persona=account.legitimate_persona,
            created_day=account.created_day,
            risk_segment=account.risk_segment,
        )
        for account in accounts
    ]


def _generate_merchant_categories() -> list[MerchantCategory]:
    return [
        MerchantCategory(
            category_id=f"cat_{category}",
            name=category,
            baseline_refund_rate=0.08 if category in {"apparel", "marketplace"} else 0.03,
            baseline_chargeback_rate=0.013 if category in {"digital_goods", "travel"} else 0.006,
        )
        for category in CATEGORIES
    ]


def _generate_accounts(rng: np.random.Generator, n: int, days: int) -> list[Account]:
    rows = []
    for i in range(n):
        persona = str(rng.choice(PERSONAS, p=[0.45, 0.08, 0.08, 0.12, 0.06, 0.07, 0.08, 0.06]))
        account_age = int(rng.integers(0, 900))
        rows.append(
            Account(
                account_id=f"acct_{i:06d}",
                customer_id=f"cust_{i:06d}",
                created_day=max(-account_age, int(rng.integers(-900, days))),
                region=str(rng.choice(REGIONS, p=[0.52, 0.24, 0.12, 0.12])),
                risk_segment=str(rng.choice(["low", "medium", "high"], p=[0.74, 0.22, 0.04])),
                account_age_days=account_age,
                device_count=max(1, int(rng.poisson(1.4))),
                payment_instrument_count=max(1, int(rng.poisson(1.2))),
                merchant_diversity=max(1, int(rng.poisson(8))),
                legitimate_persona=persona,
            )
        )
    return rows


def _generate_merchants(rng: np.random.Generator, n: int) -> list[Merchant]:
    rows = []
    for i in range(n):
        category = str(rng.choice(CATEGORIES))
        base_refund = 0.03 if category not in {"apparel", "marketplace"} else 0.08
        base_cb = 0.006 if category not in {"digital_goods", "travel"} else 0.013
        rows.append(
            Merchant(
                merchant_id=f"merch_{i:05d}",
                category=category,
                region=str(rng.choice(REGIONS, p=[0.50, 0.25, 0.12, 0.13])),
                normal_volume=float(rng.lognormal(8.1, 0.9)),
                refund_rate=float(min(0.30, rng.beta(2, 30) + base_refund / 2)),
                chargeback_rate=float(min(0.12, rng.beta(1.5, 150) + base_cb / 2)),
            )
        )
    return rows


def _generate_rings(
    rng: np.random.Generator,
    ring_count: int,
    accounts: list[Account],
    merchants: list[Merchant],
) -> list[FraudRing]:
    rows = []
    used: set[str] = set()
    account_ids = [account.account_id for account in accounts]
    merchant_ids = [merchant.merchant_id for merchant in merchants]
    for i in range(ring_count):
        ring_type = RING_TYPES[i % len(RING_TYPES)]
        remaining = [account_id for account_id in account_ids if account_id not in used]
        if not remaining:
            break
        max_size = max(4, min(80, len(remaining)))
        min_size = min(14, max_size)
        size = int(rng.integers(min_size, max_size + 1))
        sample_size = min(len(remaining), size * 2)
        members = [aid for aid in rng.choice(remaining, size=sample_size, replace=False)][:size]
        used.update(members)
        linked_merchants = [str(mid) for mid in rng.choice(merchant_ids, size=int(rng.integers(2, 8)), replace=False)]
        rows.append(
            FraudRing(
                ring_id=f"ring_{i:03d}",
                ring_type=ring_type,
                start_day=int(rng.integers(0, 10)),
                adaptation_strategy=str(
                    rng.choice(["conserve_margin", "reduce_attention", "fragment_network", "slow_burn"])
                ),
                members=members,
                merchants=linked_merchants,
                shared_devices=[f"ring_dev_{i:03d}_{j}" for j in range(int(rng.integers(2, 7)))],
                shared_ip_clusters=[f"ring_ip_{i:03d}_{j}" for j in range(int(rng.integers(1, 5)))],
            )
        )
    return rows


def _generate_transactions(
    rng: np.random.Generator,
    n: int,
    days: int,
    accounts: list[Account],
    merchants: list[Merchant],
    merchant_map: dict[str, Merchant],
    ring_map: dict[str, FraudRing],
) -> list[Transaction]:
    rows: list[Transaction] = []
    accounts_by_ring: dict[str, list[Account]] = defaultdict(list)
    for account in accounts:
        if account.fraud_ring_id:
            accounts_by_ring[account.fraud_ring_id].append(account)
    benign_accounts = [account for account in accounts if not account.fraud_ring_id]
    merchant_ids = [merchant.merchant_id for merchant in merchants]
    volumes = np.array([merchant.normal_volume for merchant in merchants], dtype=float)
    merchant_prob = volumes / volumes.sum()

    fraud_share = min(0.08, 0.018 + len(ring_map) / max(len(accounts), 1))
    for i in range(n):
        is_fraud = bool(rng.random() < fraud_share and ring_map)
        day = int(rng.integers(0, days))
        if is_fraud:
            ring = ring_map[str(rng.choice(list(ring_map.keys())))]
            account = rng.choice(accounts_by_ring[ring.ring_id])
            merchant_id = str(rng.choice(ring.merchants if rng.random() < 0.64 else merchant_ids))
            merchant = merchant_map[merchant_id]
            amount = _fraud_amount(rng, ring.ring_type) * ring.amount_multiplier
            refunded, chargeback = _fraud_outcomes(rng, ring.ring_type, ring.refund_multiplier)
            device_id = str(rng.choice(ring.shared_devices)) if rng.random() < 0.55 else f"dev_{account.account_id}_{rng.integers(0, 4)}"
            ip_id = str(rng.choice(ring.shared_ip_clusters)) if rng.random() < 0.50 else f"ip_{account.region}_{rng.integers(0, 9000)}"
            approved = bool(rng.random() > 0.08)
            ring_id: str | None = ring.ring_id
        else:
            account = rng.choice(benign_accounts)
            merchant = merchants[int(rng.choice(len(merchants), p=merchant_prob))]
            merchant_id = merchant.merchant_id
            amount = _benign_amount(rng, account.legitimate_persona)
            refund_bonus = 0.12 if account.legitimate_persona == "refund_heavy_legitimate" else 0.0
            refunded = bool(rng.random() < min(0.42, merchant.refund_rate + refund_bonus))
            chargeback = bool(rng.random() < merchant.chargeback_rate)
            device_id = f"dev_{account.account_id}_{rng.integers(0, max(1, account.device_count))}"
            ip_id = f"ip_{account.region}_{rng.integers(0, 9000)}"
            approved = bool(rng.random() > 0.015)
            ring_id = None
        rows.append(
            Transaction(
                transaction_id=f"txn_{i:08d}",
                day=day,
                account_id=account.account_id,
                merchant_id=merchant_id,
                payment_instrument_id=f"pi_{account.account_id}_{rng.integers(0, max(1, account.payment_instrument_count))}",
                device_id=device_id,
                ip_cluster_id=ip_id,
                amount=round(float(amount), 2),
                merchant_category=merchant.category,
                region=account.region,
                channel=str(rng.choice(CHANNELS)),
                approved=approved,
                refunded=refunded,
                chargeback=chargeback,
                fraud_label=is_fraud,
                ring_id=ring_id,
            )
        )
    return rows


def _generate_payment_instruments(accounts: list[Account]) -> list[PaymentInstrument]:
    rows: list[PaymentInstrument] = []
    instrument_types = ["card", "bank_account", "wallet"]
    for account in accounts:
        for idx in range(account.payment_instrument_count):
            rows.append(
                PaymentInstrument(
                    payment_instrument_id=f"pi_{account.account_id}_{idx}",
                    account_id=account.account_id,
                    instrument_type=instrument_types[idx % len(instrument_types)],
                    issuer_region=account.region,
                    created_day=max(account.created_day, account.created_day + idx * 12),
                )
            )
    return rows


def _generate_devices(accounts: list[Account], transactions: list[Transaction]) -> list[Device]:
    account_region = {account.account_id: account.region for account in accounts}
    account_devices = {(tx.account_id, tx.device_id): tx for tx in transactions}
    rows: list[Device] = []
    for (account_id, device_id), tx in sorted(account_devices.items()):
        rows.append(
            Device(
                device_id=device_id,
                account_id=account_id,
                device_family="synthetic_shared" if device_id.startswith("ring_dev_") else "consumer_device",
                first_seen_day=tx.day,
                synthetic_cluster_id=f"dev_cluster_{account_region.get(account_id, 'NA')}",
            )
        )
    return rows


def _generate_ip_clusters(transactions: list[Transaction]) -> list[IpCluster]:
    grouped: dict[str, list[Transaction]] = defaultdict(list)
    for tx in transactions:
        grouped[tx.ip_cluster_id].append(tx)
    rows = []
    for ip_id, txs in sorted(grouped.items()):
        rows.append(
            IpCluster(
                ip_cluster_id=ip_id,
                region=txs[0].region,
                first_seen_day=min(tx.day for tx in txs),
                account_count=len({tx.account_id for tx in txs}),
            )
        )
    return rows


def _generate_refunds(transactions: list[Transaction]) -> list[Refund]:
    rows = []
    for idx, tx in enumerate(tx for tx in transactions if tx.refunded):
        rows.append(
            Refund(
                refund_id=f"refund_{idx:08d}",
                transaction_id=tx.transaction_id,
                account_id=tx.account_id,
                merchant_id=tx.merchant_id,
                day=min(tx.day + 1, tx.day + (idx % 4)),
                amount=round(tx.amount * (0.35 + (idx % 5) * 0.12), 2),
                approved=tx.approved,
                fraud_label=tx.fraud_label,
                ring_id=tx.ring_id,
            )
        )
    return rows


def _generate_chargebacks(transactions: list[Transaction]) -> list[Chargeback]:
    rows = []
    for idx, tx in enumerate(tx for tx in transactions if tx.chargeback):
        rows.append(
            Chargeback(
                chargeback_id=f"chargeback_{idx:08d}",
                transaction_id=tx.transaction_id,
                account_id=tx.account_id,
                merchant_id=tx.merchant_id,
                day=tx.day + 5 + (idx % 12),
                amount=tx.amount,
                status="lost" if tx.fraud_label else "represented",
                fraud_label=tx.fraud_label,
                ring_id=tx.ring_id,
            )
        )
    return rows


def _generate_disputes(transactions: list[Transaction]) -> list[Dispute]:
    dispute_txs = [tx for tx in transactions if tx.chargeback or (tx.refunded and tx.fraud_label)]
    rows = []
    for idx, tx in enumerate(dispute_txs):
        rows.append(
            Dispute(
                dispute_id=f"dispute_{idx:08d}",
                transaction_id=tx.transaction_id,
                account_id=tx.account_id,
                merchant_id=tx.merchant_id,
                day=tx.day + 3 + (idx % 8),
                dispute_type="chargeback" if tx.chargeback else "refund_review",
                amount=tx.amount,
                status="open" if idx % 3 else "closed",
                fraud_label=tx.fraud_label,
                ring_id=tx.ring_id,
            )
        )
    return rows


def _generate_support_contacts(
    rng: np.random.Generator,
    transactions: list[Transaction],
    accounts: list[Account],
) -> list[SupportContact]:
    rows = []
    support_topics = ["refund_status", "payment_decline", "account_update", "merchant_question"]
    account_ids = [account.account_id for account in accounts]
    sampled_transactions = [tx for tx in transactions if tx.refunded or tx.chargeback]
    for idx, tx in enumerate(sampled_transactions[: max(50, len(sampled_transactions) // 2)]):
        rows.append(
            SupportContact(
                support_contact_id=f"support_{idx:08d}",
                account_id=tx.account_id,
                day=tx.day + 1,
                contact_type=str(rng.choice(["chat", "email", "phone"], p=[0.62, 0.30, 0.08])),
                topic="refund_status" if tx.refunded else "payment_decline",
                sentiment=str(rng.choice(["neutral", "frustrated", "calm"], p=[0.58, 0.24, 0.18])),
                linked_transaction_id=tx.transaction_id,
            )
        )
    for idx in range(max(10, len(accounts) // 100)):
        rows.append(
            SupportContact(
                support_contact_id=f"support_benign_{idx:08d}",
                account_id=str(rng.choice(account_ids)),
                day=int(rng.integers(0, 30)),
                contact_type="chat",
                topic=str(rng.choice(support_topics)),
                sentiment="neutral",
            )
        )
    return rows


def _generate_account_changes(
    rng: np.random.Generator,
    accounts: list[Account],
    transactions: list[Transaction],
    days: int,
) -> list[AccountChange]:
    tx_by_account: dict[str, list[Transaction]] = defaultdict(list)
    for tx in transactions:
        tx_by_account[tx.account_id].append(tx)
    rows = []
    for idx, account in enumerate(accounts):
        if rng.random() > (0.10 if account.fraud_ring_id else 0.035):
            continue
        tx = tx_by_account.get(account.account_id, [None])[0]
        low_day = min(max(0, account.created_day), max(0, days - 1))
        rows.append(
            AccountChange(
                account_change_id=f"acct_change_{idx:08d}",
                account_id=account.account_id,
                day=int(rng.integers(low_day, max(low_day + 1, days))),
                change_type=str(rng.choice(["device_added", "payment_instrument_added", "profile_update"])),
                device_id=tx.device_id if tx else None,
                ip_cluster_id=tx.ip_cluster_id if tx else None,
                ring_id=account.fraud_ring_id,
            )
        )
    return rows


def _benign_amount(rng: np.random.Generator, persona: str) -> float:
    if persona == "high_spend_traveler":
        return rng.lognormal(5.4, 0.75)
    if persona == "small_business_buyer":
        return rng.lognormal(5.0, 0.85)
    if persona == "subscription_heavy_user":
        return rng.lognormal(3.4, 0.35)
    return rng.lognormal(4.0, 0.70)


def _fraud_amount(rng: np.random.Generator, ring_type: RingType) -> float:
    if ring_type in {RingType.COLLUSIVE_MERCHANT, RingType.MULE_NETWORK}:
        return rng.lognormal(5.3, 0.65)
    if ring_type in {RingType.PROMO_ABUSE, RingType.REFUND_ABUSE}:
        return rng.lognormal(3.9, 0.55)
    return rng.lognormal(4.8, 0.75)


def _fraud_outcomes(
    rng: np.random.Generator,
    ring_type: RingType,
    refund_multiplier: float,
) -> tuple[bool, bool]:
    refund_base = {
        RingType.REFUND_ABUSE: 0.55,
        RingType.COLLUSIVE_MERCHANT: 0.18,
        RingType.PROMO_ABUSE: 0.22,
    }.get(ring_type, 0.08)
    cb_base = {
        RingType.CHARGEBACK_ABUSE: 0.48,
        RingType.ACCOUNT_TAKEOVER: 0.22,
        RingType.SYNTHETIC_IDENTITY: 0.16,
    }.get(ring_type, 0.08)
    refunded = bool(rng.random() < min(0.90, refund_base * refund_multiplier))
    chargeback = bool(rng.random() < cb_base)
    return refunded, chargeback
