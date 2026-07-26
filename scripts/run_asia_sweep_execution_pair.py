from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from dtr_lab.strategies.asia_sweep.execution_simulator import (
    simulate_pair_execution,
)


def _single_file(directory: Path, name: str) -> Path:
    files = sorted(directory.rglob(name))
    if len(files) != 1:
        raise ValueError(f"expected one {name} below {directory}, found {len(files)}")
    return files[0]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--symbol", choices=("EURUSD", "GBPUSD"), required=True)
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2019)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    event_path = _single_file(args.events, "fingerprint_events.csv")
    prediction_path = _single_file(args.predictions, "predictions_T5_hgb.csv")
    events = pd.read_csv(event_path)
    predictions = pd.read_csv(prediction_path)
    orders = simulate_pair_execution(
        events,
        predictions,
        args.data,
        symbol=args.symbol,
        start_year=args.start_year,
        end_year=args.end_year,
    )
    args.out.mkdir(parents=True, exist_ok=True)
    output_path = args.out / "execution_orders.csv"
    orders.to_csv(output_path, index=False)
    payload = {
        "programme": "ASIAN_SWEEP_EXECUTION_V2",
        "stage": f"PAIR_DISCOVERY_{args.start_year}_{args.end_year}",
        "symbol": args.symbol,
        "event_ledger_sha256": _sha256(event_path),
        "prediction_ledger_sha256": _sha256(prediction_path),
        "order_rows": int(len(orders)),
        "filled_rows": int(orders["filled"].astype(bool).sum()),
        "output_sha256": _sha256(output_path),
    }
    (args.out / "pair_execution_summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
