from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from dtr_lab.strategies.asia_sweep.fingerprint_holdout import (
    evaluate_final_holdout,
    write_final_holdout_outputs,
)
from dtr_lab.strategies.asia_sweep.fingerprint_holdout_contract import (
    load_frozen_bundle,
)


def _load_events(inputs: Path) -> pd.DataFrame:
    files = sorted(inputs.rglob("fingerprint_events.csv"))
    if len(files) != 2:
        raise ValueError(f"expected two holdout event ledgers, found {len(files)}")
    return pd.concat([pd.read_csv(path) for path in files], ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    events = _load_events(args.inputs)
    bundle = load_frozen_bundle(args.model)
    result = evaluate_final_holdout(events, bundle)
    payload = write_final_holdout_outputs(args.out, result)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
