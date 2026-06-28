from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from fraudwar.schemas.entities import SAFETY_DISCLAIMER


SYSTEM_PROMPT = (
    "You summarize synthetic defensive fraud-investigation cases for FraudWar Room. "
    "Use only the provided synthetic case data. Do not provide real-world fraud instructions, "
    "evasion guidance, platform targeting, credential theft, phishing, or operational abuse steps. "
    "Keep the summary concise and focused on defensive review."
)


def summarize_case(
    case: dict,
    graph_neighbors: list[str] | None = None,
    provider: str | None = None,
) -> dict[str, str | bool]:
    """Return a safe investigator summary.

    Provider calls are opt-in. Set `FRAUDWAR_ENABLE_CASE_SUMMARIES=1`,
    `FRAUDWAR_CASE_SUMMARY_PROVIDER=openai`, and `OPENAI_API_KEY` to use a remote
    drafting provider. Without those variables, this function returns deterministic
    local text.
    """

    selected_provider = (
        provider
        or os.getenv("FRAUDWAR_CASE_SUMMARY_PROVIDER")
        or "deterministic"
    ).lower()
    enabled = os.getenv("FRAUDWAR_ENABLE_CASE_SUMMARIES") == "1"
    fallback = _deterministic_summary(case, graph_neighbors)
    if not enabled or selected_provider == "deterministic":
        return fallback
    if selected_provider == "openai":
        try:
            return _openai_summary(case, graph_neighbors)
        except SummaryProviderError as exc:
            return {
                **fallback,
                "provider_enabled": False,
                "provider": "openai",
                "provider_error": str(exc),
            }
    return {
        **fallback,
        "provider_enabled": False,
        "provider": selected_provider,
        "provider_error": f"Unsupported summary provider: {selected_provider}",
    }


class SummaryProviderError(RuntimeError):
    """Raised when an optional summary provider cannot return a safe response."""


def _deterministic_summary(
    case: dict,
    graph_neighbors: list[str] | None = None,
) -> dict[str, str | bool]:
    neighbors = ", ".join((graph_neighbors or [])[:6]) or "no sampled neighbors"
    ring = case.get("ring_id") or "no linked ring"
    summary = (
        f"Case {case.get('case_id')} has priority {case.get('priority_score')} with "
        f"{ring}, exposure ${case.get('dollar_exposure', 0):,.2f}, and graph context: "
        f"{neighbors}. Recommended action: {case.get('recommended_action')}."
    )
    return {
        "provider_enabled": False,
        "provider": "deterministic",
        "summary": summary,
        "safety_note": "Synthetic case summary only; no real customer or fraud-enablement data.",
    }


def _openai_summary(case: dict, graph_neighbors: list[str] | None = None) -> dict[str, str | bool]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SummaryProviderError("OPENAI_API_KEY is not set.")
    model = os.getenv("FRAUDWAR_CASE_SUMMARY_MODEL", "gpt-4.1-mini")
    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "disclaimer": SAFETY_DISCLAIMER,
                        "case": _bounded_case(case),
                        "graph_neighbors": (graph_neighbors or [])[:8],
                        "requested_output": (
                            "Three short bullets: evidence, operational risk, recommended "
                            "defensive next step. Synthetic context only."
                        ),
                    },
                    separators=(",", ":"),
                ),
            },
        ],
        "max_output_tokens": 220,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SummaryProviderError(f"OpenAI request failed with HTTP {exc.code}: {detail[:240]}") from exc
    except urllib.error.URLError as exc:
        raise SummaryProviderError(f"OpenAI request failed: {exc}") from exc
    text = _extract_response_text(body)
    if not text:
        raise SummaryProviderError("OpenAI response did not include output text.")
    return {
        "provider_enabled": True,
        "provider": "openai",
        "summary": text.strip(),
        "safety_note": "Synthetic case summary only; no real customer or fraud-enablement data.",
    }


def _bounded_case(case: dict[str, Any]) -> dict[str, Any]:
    allowed = [
        "case_id",
        "day_opened",
        "account_ids",
        "merchant_ids",
        "ring_id",
        "priority_score",
        "dollar_exposure",
        "false_positive_risk",
        "recommended_action",
        "status",
        "review_hours",
    ]
    bounded = {key: case.get(key) for key in allowed if key in case}
    if "account_ids" in bounded:
        bounded["account_ids"] = bounded["account_ids"][:6]
    if "merchant_ids" in bounded:
        bounded["merchant_ids"] = bounded["merchant_ids"][:6]
    return bounded


def _extract_response_text(body: dict[str, Any]) -> str:
    if isinstance(body.get("output_text"), str):
        return body["output_text"]
    chunks: list[str] = []
    for item in body.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                chunks.append(content["text"])
    return "\n".join(chunks)
