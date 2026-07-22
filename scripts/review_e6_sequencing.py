# ruff: noqa
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import run_e6_sequencing as run


def no_overlap(frame: pd.DataFrame, by_session: bool) -> bool:
    groups = frame.groupby("session") if by_session else [("all", frame)]
    for _, group in groups:
        next_free = pd.Timestamp.min
        for row in group.sort_values(["entry_time", "signal_id"]).itertuples(index=False):
            if row.entry_time < next_free:
                return False
            next_free = row.exit_time
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--signals", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    signals = run.load_signals(args.signals)
    names = ("S0_GLOBAL", "S1_FIRST_PER_ETH_DATE", "S2_COOLDOWN_60", "S3_SESSION_SLEEVES")
    arms = {name: run.sequence(signals, name)[0] for name in names}
    published = pd.read_csv(args.results / "sequencing_results.csv").set_index("arm")
    for name, frame in arms.items():
        rebuilt = run.metrics(name, frame)
        for key in ("trades", "portfolio_net_r", "raw_expectancy_r", "portfolio_max_drawdown_r", "portfolio_return_dd"):
            if not np.isclose(float(rebuilt[key]), float(published.loc[name, key]), atol=1e-9, rtol=0.0):
                raise AssertionError(f"{name} {key} mismatch")
    if not all(no_overlap(arms[name], False) for name in names[:3]):
        raise AssertionError("Global overlap found")
    if not no_overlap(arms["S3_SESSION_SLEEVES"], True):
        raise AssertionError("Within-sleeve overlap found")
    if arms["S1_FIRST_PER_ETH_DATE"].groupby("eth_market_date").size().max() != 1:
        raise AssertionError("S1 daily contract failed")
    s2 = arms["S2_COOLDOWN_60"].sort_values(["entry_time", "signal_id"])
    previous_exit = None
    for row in s2.itertuples(index=False):
        if previous_exit is not None and row.entry_time < previous_exit + pd.Timedelta(minutes=60):
            raise AssertionError("S2 cooldown failed")
        previous_exit = row.exit_time
    paired = run.inference({name: run.date_returns(name, frame) for name, frame in arms.items()}, 20260723)
    if not (paired["incremental_net_r"] < 0).all():
        raise AssertionError("Independent inference direction changed")
    review = {
        "decision": "INDEPENDENT_REVIEW_PASS",
        "metrics_reconstructed": list(arms),
        "sequencing_contracts_verified": True,
        "independent_inference": paired.to_dict(orient="records"),
        "conclusion": "Retain S0 global sequencing.",
    }
    args.output.write_text(json.dumps(review, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
