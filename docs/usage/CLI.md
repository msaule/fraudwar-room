# CLI

Run from the repository root:

```bash
pip install -e "backend[dev]"
python scripts/generate_world.py
python scripts/run_experiment.py static-vs-adaptive
python scripts/run_all_experiments.py
python scripts/export_demo_reports.py
```

Installed command:

```bash
fraudwar list-experiments
fraudwar run static-vs-adaptive
fraudwar run-all
fraudwar serve
```

`generate_world.py` defaults to the portfolio-scale synthetic world of 10,000 accounts,
500 merchants, 100,000 transactions, and 10 rings. The dashboard demo export intentionally
uses a smaller run so UI checks remain fast.

Optional GNN and LLM setup is documented in
`docs/usage/OPTIONAL_GNN_AND_LLM.md`.
