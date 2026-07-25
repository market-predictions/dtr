from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from dtr_lab.strategies.asia_sweep.fingerprint_modeling import (
    run_development_models,
    write_development_outputs,
)


def _load_events(inputs: Path) -> pd.DataFrame:
    files = sorted(inputs.rglob("fingerprint_events.csv"))
    if len(files) != 2:
        raise ValueError(f"expected two fingerprint event ledgers, found {len(files)}: {files}")
    frames = [pd.read_csv(path) for path in files]
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    events = _load_events(args.inputs)
    outputs = run_development_models(events)
    decision = write_development_outputs(args.out, outputs)
    print(json.dumps(decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
