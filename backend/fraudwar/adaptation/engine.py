from __future__ import annotations

import itertools
from collections import Counter

from fraudwar.schemas.entities import AdaptationAction, AdaptationEvent, Case, FraudRing


ACTION_CYCLE = [
    AdaptationAction.LOWER_VELOCITY,
    AdaptationAction.SPLIT_CLUSTER,
    AdaptationAction.REDUCE_REFUNDS,
    AdaptationAction.SMALLER_AMOUNTS,
    AdaptationAction.REDUCE_SHARED_INFRA,
    AdaptationAction.DELAY_ACTIVITY,
]


def adapt_rings(rings: list[FraudRing], reviewed_cases: list[Case], day: int) -> tuple[list[FraudRing], list[AdaptationEvent]]:
    cases_by_ring = Counter(case.ring_id for case in reviewed_cases if case.ring_id and case.status == "reviewed")
    events: list[AdaptationEvent] = []
    cycle = itertools.cycle(ACTION_CYCLE)
    adapted: list[FraudRing] = []
    for ring in rings:
        friction = cases_by_ring.get(ring.ring_id, 0)
        if friction <= 0 or not ring.active:
            adapted.append(ring)
            continue
        action = next(cycle)
        update = {}
        if action == AdaptationAction.LOWER_VELOCITY:
            update["velocity_multiplier"] = max(0.35, ring.velocity_multiplier * 0.82)
        elif action == AdaptationAction.REDUCE_REFUNDS:
            update["refund_multiplier"] = max(0.35, ring.refund_multiplier * 0.76)
        elif action == AdaptationAction.SMALLER_AMOUNTS:
            update["amount_multiplier"] = max(0.50, ring.amount_multiplier * 0.84)
        elif action == AdaptationAction.REDUCE_SHARED_INFRA:
            update["shared_infra_multiplier"] = max(0.40, ring.shared_infra_multiplier * 0.72)
        if friction >= 4:
            update["detected"] = True
        if friction >= 8:
            update["disrupted"] = True
            update["active"] = False
        memory = [*ring.detection_memory, f"day {day}: {friction} reviewed synthetic cases"]
        update["detection_memory"] = memory[-8:]
        new_ring = ring.model_copy(update=update)
        adapted.append(new_ring)
        events.append(
            AdaptationEvent(
                event_id=f"adapt_{day}_{ring.ring_id}_{len(events)}",
                day=day,
                ring_id=ring.ring_id,
                observed_outcome="synthetic investigator friction observed",
                action=action,
                rationale="Abstract closed-world adaptation after defensive friction; not a real-world evasion playbook.",
            )
        )
    return adapted, events

