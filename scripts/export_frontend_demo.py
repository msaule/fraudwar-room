from pathlib import Path
import json
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fraudwar.arena.environment import run_experiment


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    run = run_experiment(
        "static-vs-adaptive",
        seed=42,
        output_dir=root / "data" / "demo",
        accounts=350,
        merchants=45,
        transactions=1500,
        rings=4,
        days=20,
    )
    source = root / "data" / "demo" / f"{run['run_id']}.json"
    target = root / "frontend" / "src" / "data" / "demo-run.json"
    target.write_text(json.dumps(json.loads(source.read_text(encoding="utf-8")), indent=2), encoding="utf-8")
    shutil.copyfile(source, root / "data" / "generated" / f"{run['run_id']}.json")
    print(target)
