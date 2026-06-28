from __future__ import annotations

from collections import deque

from fraudwar.schemas.entities import Alert, Case, Investigator


def create_cases(alerts: list[Alert], strategy: str = "ring_priority") -> list[Case]:
    cases: list[Case] = []
    for i, alert in enumerate(alerts):
        ring_bonus = 0.20 if alert.ring_id and strategy in {"ring_priority", "balanced"} else 0.0
        dollar_bonus = min(0.18, alert.dollar_exposure / 20000) if strategy == "dollar_risk" else 0.0
        priority = min(0.99, alert.score + ring_bonus + dollar_bonus)
        cases.append(
            Case(
                case_id=f"case_{i:05d}_{alert.entity_id}",
                day_opened=alert.day,
                alert_ids=[alert.alert_id],
                account_ids=[alert.entity_id] if alert.entity_type == "account" else [],
                merchant_ids=[alert.entity_id] if alert.entity_type == "merchant" else [],
                ring_id=alert.ring_id,
                priority_score=round(priority, 4),
                dollar_exposure=alert.dollar_exposure,
                false_positive_risk=round(1.0 - alert.score, 4),
                recommended_action=_recommended_action(alert, priority),
                notes="Synthetic evidence bundle generated for defensive simulation.",
            )
        )
    return sorted(cases, key=lambda c: (c.priority_score, c.dollar_exposure), reverse=True)


def process_queue(
    cases: list[Case],
    investigators: list[Investigator],
    review_hours_per_case: float = 0.75,
) -> tuple[list[Case], dict[str, float]]:
    capacity = sum(inv.cases_per_day for inv in investigators)
    queue = deque(cases)
    processed: list[Case] = []
    investigator_cycle = list(investigators) or [Investigator(investigator_id="inv_000", cases_per_day=999)]
    i = 0
    while queue and len(processed) < capacity:
        case = queue.popleft()
        investigator = investigator_cycle[i % len(investigator_cycle)]
        case.status = "reviewed"
        case.investigator_id = investigator.investigator_id
        case.review_hours = review_hours_per_case
        processed.append(case)
        i += 1
    metrics = {
        "cases_opened": float(len(cases)),
        "cases_reviewed": float(len(processed)),
        "backlog": float(len(queue)),
        "investigator_hours_used": round(len(processed) * review_hours_per_case, 2),
        "sla_missed": float(max(0, len(queue) - capacity)),
    }
    return processed + list(queue), metrics


def _recommended_action(alert: Alert, priority: float) -> str:
    if alert.ring_id and priority > 0.70:
        return "link to ring and escalate synthetic disruption review"
    if priority > 0.62:
        return "hold transaction/account for synthetic investigator review"
    return "monitor with no customer-impacting action"

