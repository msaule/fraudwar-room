from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fraudwar.cli import main

if __name__ == "__main__":
    sys.argv = ["fraudwar", "run-all", *sys.argv[1:]]
    main()

