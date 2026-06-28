from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fraudwar.arena.environment import run_experiment

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    run_experiment(
        "static-vs-adaptive",
        seed=42,
        output_dir=root / "data" / "demo",
        accounts=350,
        merchants=45,
        transactions=1500,
        rings=4,
        days=20,
    )
    print(root / "data" / "demo")
