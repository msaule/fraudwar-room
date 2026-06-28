from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


SAFETY_DISCLAIMER = (
    "FraudWar Room uses synthetic data and abstract adversarial behavior for defensive "
    "research, analytics, and portfolio demonstration. It is not a guide to committing "
    "fraud and must not be used to facilitate abuse."
)


class RingType(StrEnum):
    MULE_NETWORK = "mule_network"
    REFUND_ABUSE = "refund_abuse_ring"
    ACCOUNT_TAKEOVER = "account_takeover_cluster"
    SYNTHETIC_IDENTITY = "synthetic_identity_ring"
    COLLUSIVE_MERCHANT = "collusive_merchant_cluster"
    PROMO_ABUSE = "promo_bonus_abuse_ring"
    CHARGEBACK_ABUSE = "chargeback_abuse_cluster"


class AdaptationAction(StrEnum):
    LOWER_VELOCITY = "lower_velocity"
    SPLIT_CLUSTER = "split_cluster"
    ROTATE_SYNTHETIC_DEVICE = "rotate_synthetic_device_identifiers"
    DISTRIBUTE_VOLUME = "distribute_volume_across_more_accounts"
    SHIFT_CATEGORY = "shift_synthetic_merchant_category"
    REDUCE_REFUNDS = "reduce_refund_frequency"
    DELAY_ACTIVITY = "delay_activity"
    DECENTRALIZE_HUB = "decentralize_mule_hub"
    REDUCE_SHARED_INFRA = "reduce_shared_infrastructure"
    SMALLER_AMOUNTS = "use_smaller_transaction_amounts"
    DORMANCY = "increase_account_dormancy_before_activity"


class Customer(BaseModel):
    customer_id: str
    region: str
    legitimate_persona: str
    created_day: int
    risk_segment: str


class Account(BaseModel):
    account_id: str
    customer_id: str
    created_day: int
    region: str
    risk_segment: str
    account_age_days: int
    device_count: int
    payment_instrument_count: int
    merchant_diversity: int
    legitimate_persona: str
    fraud_ring_id: str | None = None


class PaymentInstrument(BaseModel):
    payment_instrument_id: str
    account_id: str
    instrument_type: str
    issuer_region: str
    created_day: int
    active: bool = True


class Device(BaseModel):
    device_id: str
    account_id: str | None
    device_family: str
    first_seen_day: int
    synthetic_cluster_id: str | None = None


class IpCluster(BaseModel):
    ip_cluster_id: str
    region: str
    first_seen_day: int
    account_count: int = 0


class MerchantCategory(BaseModel):
    category_id: str
    name: str
    baseline_refund_rate: float
    baseline_chargeback_rate: float


class Merchant(BaseModel):
    merchant_id: str
    category: str
    region: str
    normal_volume: float
    refund_rate: float
    chargeback_rate: float
    collusive_ring_id: str | None = None


class Transaction(BaseModel):
    transaction_id: str
    day: int
    account_id: str
    merchant_id: str
    payment_instrument_id: str
    device_id: str
    ip_cluster_id: str
    amount: float
    merchant_category: str
    region: str
    channel: str
    approved: bool
    refunded: bool
    chargeback: bool
    fraud_label: bool
    ring_id: str | None = None


class Refund(BaseModel):
    refund_id: str
    transaction_id: str
    account_id: str
    merchant_id: str
    day: int
    amount: float
    approved: bool
    fraud_label: bool
    ring_id: str | None = None


class Chargeback(BaseModel):
    chargeback_id: str
    transaction_id: str
    account_id: str
    merchant_id: str
    day: int
    amount: float
    status: str
    fraud_label: bool
    ring_id: str | None = None


class Dispute(BaseModel):
    dispute_id: str
    transaction_id: str
    account_id: str
    merchant_id: str
    day: int
    dispute_type: str
    amount: float
    status: str
    fraud_label: bool
    ring_id: str | None = None


class SupportContact(BaseModel):
    support_contact_id: str
    account_id: str
    day: int
    contact_type: str
    topic: str
    sentiment: str
    linked_transaction_id: str | None = None


class AccountChange(BaseModel):
    account_change_id: str
    account_id: str
    day: int
    change_type: str
    device_id: str | None = None
    ip_cluster_id: str | None = None
    ring_id: str | None = None


class FraudRing(BaseModel):
    ring_id: str
    ring_type: RingType
    start_day: int
    active: bool = True
    adaptation_strategy: str
    members: list[str]
    merchants: list[str]
    shared_devices: list[str]
    shared_ip_clusters: list[str]
    detected: bool = False
    disrupted: bool = False
    velocity_multiplier: float = 1.0
    amount_multiplier: float = 1.0
    refund_multiplier: float = 1.0
    shared_infra_multiplier: float = 1.0
    detection_memory: list[str] = Field(default_factory=list)


class Alert(BaseModel):
    alert_id: str
    day: int
    entity_id: str
    entity_type: str
    score: float
    reason: str
    dollar_exposure: float
    ring_id: str | None = None
    is_true_positive: bool = False


class Case(BaseModel):
    case_id: str
    day_opened: int
    alert_ids: list[str]
    account_ids: list[str]
    merchant_ids: list[str]
    ring_id: str | None
    priority_score: float
    dollar_exposure: float
    false_positive_risk: float
    recommended_action: str
    status: str = "queued"
    investigator_id: str | None = None
    review_hours: float = 0.0
    notes: str = ""


class Investigator(BaseModel):
    investigator_id: str
    cases_per_day: int
    hourly_cost: float = 65.0


class DefensePolicy(BaseModel):
    policy_id: str
    name: str
    threshold: float
    strategy: str
    alert_budget: int | None = None
    retraining_cadence_days: int | None = None


class MetricResult(BaseModel):
    metric_id: str
    run_id: str
    namespace: str
    name: str
    value: float | str


class AfterActionReport(BaseModel):
    report_id: str
    run_id: str
    format: str
    path: str
    generated_day: int


class AdaptationEvent(BaseModel):
    event_id: str
    day: int
    ring_id: str
    observed_outcome: str
    action: AdaptationAction
    rationale: str


class SimulationRun(BaseModel):
    run_id: str
    experiment_id: str
    seed: int
    days: int
    defense_name: str
    disclaimer: str = SAFETY_DISCLAIMER
