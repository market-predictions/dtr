from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from dtr_lab.strategies.asia_sweep.continuation_geometry import (
    build_pair_continuation_geometry,
    prepare_continuation_events,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--levels", type=Path, required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    predictions = pd.read_csv(args.predictions)
    landmark_ledger = pd.read_csv(args.ledger)
    levels = pd.read_csv(args.levels)
    events = prepare_continuation_events(
        predictions,
        landmark_ledger,
        symbol=args.symbol,
    )
    geometry = build_pair_continuation_geometry(
        events,
        levels,
        args.data,
        symbol=args.symbol,
    )
    geometry.to_csv(args.out / "continuation_geometry.csv", index=False)
    summary = {
        "symbol": args.symbol.upper(),
        "events": int(events["event_id"].nunique()),
        "selected_continuation_events": int(
            events["decision"].eq("CONTINUATION").sum()
        ),
        "geometry_rows": int(len(geometry)),
        "objectives": sorted(geometry["objective"].unique().tolist()),
        "years": sorted(geometry["year"].unique().astype(int).tolist()),
    }
    (args.out / "pair_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
