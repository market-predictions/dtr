from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from dtr_lab.strategies.asia_sweep.staged_reversal import (
    POLICY_ORDER,
    build_pair_staged_policy_ledger,
    prepare_policy_candidates,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--t0-predictions", type=Path, required=True)
    parser.add_argument("--t2-predictions", type=Path, required=True)
    parser.add_argument("--t3-predictions", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def _normalize_geometry_columns(candidates: pd.DataFrame) -> pd.DataFrame:
    result = candidates.copy()
    if "asian_midpoint" not in result.columns:
        for candidate in ("asian_midpoint_x", "asian_midpoint_y"):
            if candidate in result.columns:
                result["asian_midpoint"] = result[candidate]
                break
    if "asian_midpoint" not in result.columns:
        raise ValueError("staged candidates are missing Asian midpoint geometry")
    return result


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    t0 = pd.read_csv(args.t0_predictions)
    t2 = pd.read_csv(args.t2_predictions)
    t3 = pd.read_csv(args.t3_predictions)
    landmark_ledger = pd.read_csv(args.ledger)
    frames: list[pd.DataFrame] = []
    policy_counts: dict[str, int] = {}
    for policy in POLICY_ORDER:
        candidates = prepare_policy_candidates(
            t0,
            t2,
            landmark_ledger,
            symbol=args.symbol,
            policy=policy,
        )
        candidates = _normalize_geometry_columns(candidates)
        trades = build_pair_staged_policy_ledger(
            candidates,
            policy,
            args.data,
            symbol=args.symbol.upper(),
            t0_predictions=t0,
            t2_predictions=t2,
            t3_predictions=t3,
        )
        frames.append(trades)
        policy_counts[policy] = int(len(trades))
    ledger = pd.concat(frames, ignore_index=True)
    ledger.to_csv(args.out / "staged_reversal_trades.csv", index=False)
    summary = {
        "symbol": args.symbol.upper(),
        "policy_trade_counts": policy_counts,
        "rows": int(len(ledger)),
        "years": sorted(ledger["year"].unique().astype(int).tolist()),
    }
    (args.out / "pair_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
