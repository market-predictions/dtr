from __future__ import annotations

import argparse
import json
from pathlib import Path

from dtr_lab.strategies.asia_sweep.extended_target_modeling_v2 import (
    aggregate_extended_summaries,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    decision = aggregate_extended_summaries(args.inputs, args.out)
    print(json.dumps(decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
