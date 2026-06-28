from __future__ import annotations

import json
from pathlib import Path

from fraudwar.reports.investigator_summary import summarize_case
from fraudwar.schemas.entities import SAFETY_DISCLAIMER


def build_after_action_report(run: dict) -> dict:
    metrics = run["metrics"]
    best = run.get("recommendation", "graph_feature_model + ring_priority investigation")
    graph = run.get("graph", {"nodes": [], "edges": []})
    cases = run.get("cases", [])
    rings = run.get("rings", [])
    top_cases = sorted(cases, key=lambda case: case.get("priority_score", 0), reverse=True)[:10]
    return {
        "title": "Fraud Run Memo",
        "disclaimer": SAFETY_DISCLAIMER,
        "run_id": run["run_id"],
        "executive_summary": {
            "recommended_defense": best,
            "net_fraud_loss": metrics["financial"]["fraud_dollars_missed"],
            "prevented_loss": metrics["financial"]["fraud_dollars_blocked"],
            "false_positive_cost": metrics["financial"]["false_positive_cost"],
            "investigator_roi": metrics["financial"]["investigator_roi"],
            "adversarial_half_life": metrics["adversarial"]["adversarial_half_life"],
            "top_risk": "adaptive recall decay under investigator capacity constraints",
        },
        "defense_comparison": run.get("defense_comparison", []),
        "entity_coverage": run.get("entities", {}),
        "active_rings": rings,
        "event_timeline": run.get("timeline", []),
        "case_queue": {
            "total_sampled_cases": len(cases),
            "top_cases": top_cases,
            "reviewed_cases": len([case for case in cases if case.get("status") == "reviewed"]),
            "queued_cases": len([case for case in cases if case.get("status") == "queued"]),
        },
        "investigator_summaries": [summarize_case(case) for case in top_cases[:5]],
        "graph_evidence": {
            "node_count": len(graph.get("nodes", [])),
            "edge_count": len(graph.get("edges", [])),
            "node_types": sorted({node.get("type", "entity") for node in graph.get("nodes", [])}),
            "edge_types": sorted({edge.get("type", "linked") for edge in graph.get("edges", [])}),
        },
        "operations": metrics["operations"],
        "financial_impact": metrics["financial"],
        "recall_under_drift": metrics["adversarial"],
        "strategy_diagnostics": metrics.get("strategy", {}),
        "methodology": {
            "data": "Synthetic closed-world payment network generated from a seed.",
            "labels": "Fraud labels are available for evaluation but represent synthetic ground truth only.",
            "adaptation": "Rings adapt through abstract simulator parameters after synthetic defensive friction.",
            "safety": "The report intentionally omits real-world operational fraud instructions.",
        },
        "recommendation": (
            f"Recommended defense: {best}. The choice is based on blocked loss, ring "
            "recall, review load, and recall decay in this generated run."
        ),
    }


def write_reports(run: dict, output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_after_action_report(run)
    json_path = output_dir / f"{run['run_id']}_after_action.json"
    md_path = output_dir / f"{run['run_id']}_after_action.md"
    html_path = output_dir / f"{run['run_id']}_after_action.html"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(report_to_markdown(report), encoding="utf-8")
    html_path.write_text(report_to_html(report), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path), "html": str(html_path)}


def report_to_markdown(report: dict) -> str:
    summary = report["executive_summary"]
    graph = report["graph_evidence"]
    operations = report["operations"]
    financial = report["financial_impact"]
    drift = report["recall_under_drift"]
    return f"""# {report["title"]}

> {report["disclaimer"]}

## Executive Summary

- Recommended defense: {summary["recommended_defense"]}
- Net fraud loss: ${summary["net_fraud_loss"]:,.2f}
- Prevented loss: ${summary["prevented_loss"]:,.2f}
- False-positive cost: ${summary["false_positive_cost"]:,.2f}
- Investigator ROI: ${summary["investigator_roi"]:,.2f} saved per investigator-hour
- Adversarial half-life: {summary["adversarial_half_life"]} simulation days
- Top risk: {summary["top_risk"]}

## Event Timeline

{_markdown_events(report["event_timeline"])}

## Active Rings

{_markdown_rings(report["active_rings"])}

## Defense Results

{_markdown_defenses(report["defense_comparison"])}

## Graph Evidence

- Nodes in dashboard graph: {graph["node_count"]}
- Edges in dashboard graph: {graph["edge_count"]}
- Node types: {", ".join(graph["node_types"])}
- Edge types: {", ".join(graph["edge_types"][:12])}

## Operations

- Cases opened: {operations.get("cases_opened", 0)}
- Cases reviewed: {operations.get("cases_reviewed", 0)}
- Backlog: {operations.get("backlog", 0)}
- Investigator hours used: {operations.get("investigator_hours_used", 0)}
- SLA missed: {operations.get("sla_missed", 0)}

## Financial Impact

- Attempted fraud: ${financial.get("fraud_dollars_attempted", 0):,.2f}
- Blocked fraud: ${financial.get("fraud_dollars_blocked", 0):,.2f}
- Missed fraud: ${financial.get("fraud_dollars_missed", 0):,.2f}
- False-positive cost: ${financial.get("false_positive_cost", 0):,.2f}
- Review cost: ${financial.get("review_cost", 0):,.2f}
- Net savings: ${financial.get("net_savings", 0):,.2f}

## Recall Under Drift

- Pre-adaptation recall: {drift.get("pre_adaptation_recall", 0)}
- Post-adaptation recall: {drift.get("post_adaptation_recall", 0)}
- Recall decay: {drift.get("recall_decay", 0)}
- Adversarial half-life: {drift.get("adversarial_half_life", 0)}
- Brittleness score: {drift.get("defense_brittleness_score", 0)}
- Robustness index: {drift.get("strategy_robustness_index", 0)}

## Recommendation

{report["recommendation"]}
"""


def report_to_html(report: dict) -> str:
    summary = report["executive_summary"]
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{report["title"]}</title>
  <style>
    body {{ margin: 0; background: #0e1117; color: #edf0f4; font-family: ui-sans-serif, system-ui, sans-serif; }}
    main {{ max-width: 1040px; margin: 0 auto; padding: 40px 24px; }}
    section {{ border: 1px solid #293241; background: #151a22; border-radius: 8px; padding: 20px; margin: 16px 0; }}
    h1, h2 {{ margin: 0 0 14px; }}
    .grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }}
    .metric {{ border: 1px solid #303949; padding: 14px; border-radius: 6px; }}
    .label {{ color: #a8b0bd; font-size: 13px; }}
    .value {{ font-size: 24px; margin-top: 6px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ border-bottom: 1px solid #293241; padding: 8px; text-align: left; }}
    th {{ color: #a8b0bd; }}
  </style>
</head>
<body>
  <main>
    <h1>{report["title"]}</h1>
    <p>{report["disclaimer"]}</p>
    <section>
      <h2>Executive Summary</h2>
      <div class="grid">
        <div class="metric"><div class="label">Prevented loss</div><div class="value">${summary["prevented_loss"]:,.0f}</div></div>
        <div class="metric"><div class="label">Net fraud loss</div><div class="value">${summary["net_fraud_loss"]:,.0f}</div></div>
        <div class="metric"><div class="label">Investigator ROI</div><div class="value">${summary["investigator_roi"]:,.0f}/hr</div></div>
        <div class="metric"><div class="label">False-positive cost</div><div class="value">${summary["false_positive_cost"]:,.0f}</div></div>
        <div class="metric"><div class="label">Adversarial half-life</div><div class="value">{summary["adversarial_half_life"]}</div></div>
        <div class="metric"><div class="label">Recommended defense</div><div class="value">{summary["recommended_defense"]}</div></div>
      </div>
    </section>
    <section>
      <h2>Recommendation</h2>
      <p>{report["recommendation"]}</p>
    </section>
    <section>
      <h2>Graph Evidence</h2>
      <p>{report["graph_evidence"]["node_count"]} nodes and {report["graph_evidence"]["edge_count"]} links across {", ".join(report["graph_evidence"]["node_types"])}.</p>
    </section>
    <section>
      <h2>Defense Results</h2>
      {_html_defense_table(report["defense_comparison"])}
    </section>
    <section>
      <h2>Operations</h2>
      <p>Cases opened: {report["operations"].get("cases_opened", 0)}. Backlog: {report["operations"].get("backlog", 0)}. Investigator hours: {report["operations"].get("investigator_hours_used", 0)}.</p>
    </section>
    <section>
      <h2>Recall Under Drift</h2>
      <p>Pre-adaptation recall: {report["recall_under_drift"].get("pre_adaptation_recall", 0)}. Post-adaptation recall: {report["recall_under_drift"].get("post_adaptation_recall", 0)}. Half-life: {report["recall_under_drift"].get("adversarial_half_life", 0)}.</p>
    </section>
  </main>
</body>
</html>"""


def _markdown_events(events: list[dict]) -> str:
    if not events:
        return "No timeline events recorded."
    return "\n".join(
        f"- Day {event.get('day')}: {event.get('title')} — {event.get('detail')}"
        for event in events[:12]
    )


def _markdown_rings(rings: list[dict]) -> str:
    if not rings:
        return "No active rings recorded."
    return "\n".join(
        f"- {ring.get('ring_id')}: {ring.get('ring_type')} with "
        f"{len(ring.get('members', []))} members, detected={ring.get('detected')}, "
        f"disrupted={ring.get('disrupted')}"
        for ring in rings[:12]
    )


def _markdown_defenses(defenses: list[dict]) -> str:
    if not defenses:
        return "No defense comparison recorded."
    return "\n".join(
        f"- {row.get('defense')}: precision={row.get('precision')}, "
        f"recall={row.get('recall')}, ring recall={row.get('ring_level_recall')}, "
        f"alerts={row.get('alerts')}"
        for row in defenses
    )


def _html_defense_table(defenses: list[dict]) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{row.get('defense')}</td>"
        f"<td>{row.get('precision')}</td>"
        f"<td>{row.get('recall')}</td>"
        f"<td>{row.get('ring_level_recall')}</td>"
        f"<td>{row.get('alerts')}</td>"
        "</tr>"
        for row in defenses
    )
    return (
        "<table><thead><tr><th>Defense</th><th>Precision</th><th>Recall</th>"
        "<th>Ring recall</th><th>Alerts</th></tr></thead><tbody>"
        f"{rows}</tbody></table>"
    )
