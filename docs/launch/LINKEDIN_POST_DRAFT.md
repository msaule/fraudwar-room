# LinkedIn Post Draft

I built FraudWar Room, a local simulator for testing fraud controls under drift.

Most fraud demos stop at a static classifier. This one generates a synthetic payment
network, opens cases, builds graph evidence, and tracks what happens when behavior changes
after the first round of defensive friction. The main outputs are loss, false-positive cost,
ring recall, recall decay, queue pressure, and investigator ROI.

The project includes a Python/FastAPI simulation engine, NetworkX graph features, detection
baselines, run memos, and a risk operations dashboard.
