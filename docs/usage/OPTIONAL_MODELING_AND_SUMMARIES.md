# Optional Modeling and Case Summaries

FraudWar Room works without heavyweight machine-learning dependencies or API keys. The
optional integrations below are disabled by default.

## PyTorch Geometric GNN

Install:

```bash
pip install -e "backend[gnn]"
```

Check local availability:

```bash
python scripts/check_optional_features.py --gnn-smoke
```

Model class:

```python
from fraudwar.defenses.gnn import PyGGraphNeuralNetwork

model = PyGGraphNeuralNetwork(epochs=80)
model.fit(transactions)
scores = model.score(transactions)
```

The GNN uses account-level node features and account-account edges derived from shared
synthetic devices, IP clusters, and merchants. If PyTorch Geometric is not installed, the
class raises a clear `OptionalDependencyError`.

## Case Summary Drafting

Default behavior is deterministic local text. Provider calls are opt-in:

```bash
set FRAUDWAR_ENABLE_CASE_SUMMARIES=1
set FRAUDWAR_CASE_SUMMARY_PROVIDER=openai
set OPENAI_API_KEY=...
set FRAUDWAR_CASE_SUMMARY_MODEL=gpt-4.1-mini
```

Check configuration without making a provider call:

```bash
python scripts/check_optional_features.py
```

The adapter sends only bounded synthetic case fields and synthetic graph-neighbor IDs to the
provider. It does not send real customer, payment, or platform data. If the provider is not
configured or returns an error, FraudWar Room falls back to deterministic text.

Safety boundary:

> FraudWar Room uses synthetic data and abstract adversarial behavior for defensive research,
> analytics, and product testing. It is not a guide to committing fraud and must not
> be used to facilitate abuse.
