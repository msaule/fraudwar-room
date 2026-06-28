from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fraudwar.defenses.gnn import OptionalDependencyError, PyGGraphNeuralNetwork


def main() -> None:
    gnn_available = PyGGraphNeuralNetwork.is_available()
    summaries_enabled = os.getenv("FRAUDWAR_ENABLE_CASE_SUMMARIES") == "1"
    summary_provider = os.getenv("FRAUDWAR_CASE_SUMMARY_PROVIDER", "local")
    has_key = bool(os.getenv("OPENAI_API_KEY"))

    result = {
        "gnn": {
            "available": gnn_available,
            "install": 'pip install -e "backend[gnn]"',
        },
        "case_summaries": {
            "enabled": summaries_enabled,
            "provider": summary_provider,
            "api_key_configured": has_key,
            "safe_default": "deterministic local summaries",
        },
    }

    if "--gnn-smoke" in sys.argv:
        try:
            PyGGraphNeuralNetwork(epochs=1)
            result["gnn"]["smoke"] = "constructed"
        except OptionalDependencyError as exc:
            result["gnn"]["smoke"] = str(exc)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
