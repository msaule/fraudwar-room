from __future__ import annotations


def threshold_for_alert_budget(
    scores: dict[str, float],
    alert_budget: int,
    floor: float = 0.20,
    ceiling: float = 0.92,
) -> tuple[float, dict[str, float]]:
    """Pick a threshold that respects a review budget while preserving high scores."""

    if not scores:
        return ceiling, {"selected_threshold": ceiling, "score_population": 0.0}
    ordered = sorted(scores.values(), reverse=True)
    if alert_budget <= 0:
        threshold = ceiling
    elif alert_budget >= len(ordered):
        threshold = max(floor, min(ordered))
    else:
        threshold = ordered[alert_budget - 1]
    threshold = min(ceiling, max(floor, float(threshold)))
    projected_alerts = sum(1 for score in scores.values() if score >= threshold)
    return threshold, {
        "selected_threshold": round(threshold, 4),
        "score_population": float(len(scores)),
        "projected_alerts": float(projected_alerts),
        "alert_budget": float(alert_budget),
    }

