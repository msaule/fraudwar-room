from __future__ import annotations

from collections import defaultdict

from fraudwar.defenses.model import GraphFeatureModel
from fraudwar.schemas.entities import Transaction


def active_learning_scores(
    train: list[Transaction],
    test: list[Transaction],
    label_budget: int = 50,
) -> tuple[dict[str, float], dict[str, float]]:
    """Retrain a graph-feature model after simulated investigator labels.

    Labels are available because this is a synthetic benchmark. The policy selects uncertain
    and high-risk accounts from the first test window, adds their transactions to the training
    set, then scores the remaining window with the updated model.
    """

    if not test:
        return {}, {"label_budget_used": 0.0, "retraining_events": 0.0}
    days = sorted({tx.day for tx in test})
    split_day = days[len(days) // 2]
    first_window = [tx for tx in test if tx.day <= split_day]
    second_window = [tx for tx in test if tx.day > split_day]
    if not first_window or not second_window:
        model = GraphFeatureModel().fit(train)
        return model.score(test), {"label_budget_used": 0.0, "retraining_events": 0.0}

    first_model = GraphFeatureModel().fit(train)
    first_scores = first_model.score(first_window)
    selected_accounts = _select_label_accounts(first_scores, label_budget)
    labeled_transactions = [
        tx for tx in first_window if tx.account_id in selected_accounts
    ]
    updated_train = [*train, *labeled_transactions]
    second_model = GraphFeatureModel().fit(updated_train)
    second_scores = second_model.score(second_window)
    combined = {**first_scores, **second_scores}
    diagnostics = {
        "label_budget_used": float(len(selected_accounts)),
        "retraining_events": 1.0,
        "labeled_fraud_accounts": float(
            len({tx.account_id for tx in labeled_transactions if tx.fraud_label})
        ),
        "labeled_false_positive_accounts": float(
            len({tx.account_id for tx in labeled_transactions if not tx.fraud_label})
        ),
    }
    return combined, diagnostics


def _select_label_accounts(scores: dict[str, float], label_budget: int) -> set[str]:
    if label_budget <= 0:
        return set()
    uncertainty = sorted(scores.items(), key=lambda item: (abs(item[1] - 0.5), -item[1]))
    high_risk = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    selected: list[str] = []
    for account_id, _ in [*uncertainty[: label_budget // 2], *high_risk[: label_budget]]:
        if account_id not in selected:
            selected.append(account_id)
        if len(selected) >= label_budget:
            break
    return set(selected)


def account_label_summary(transactions: list[Transaction], account_ids: set[str]) -> dict[str, int]:
    grouped: dict[str, list[Transaction]] = defaultdict(list)
    for tx in transactions:
        if tx.account_id in account_ids:
            grouped[tx.account_id].append(tx)
    return {
        account_id: int(any(tx.fraud_label for tx in txs))
        for account_id, txs in grouped.items()
    }

