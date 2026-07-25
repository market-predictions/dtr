from __future__ import annotations

import argparse
import json
from pathlib import Path

from dtr_lab.strategies.asia_sweep.amsterdam_window_gate import (
    build_decision,
    write_decision,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    decision, matched = build_decision(args.inputs)
    write_decision(args.out, decision, matched)
    print(json.dumps(decision, indent=2, sort_keys=True))
    if not bool(decision["passed"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
