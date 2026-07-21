from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from dtr_lab.research import build_session_table, load_zip, resample_5m
from dtr_lab.research.continuation import evaluate_continuation_baselines


def _attribution(trades: pd.DataFrame, column: str) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame(columns=[column])
    from dtr_lab.research.engine import metrics

    return pd.DataFrame(
        [{column: key, **metrics(group)} for key, group in trades.groupby(column)]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the unfiltered continuation baselines")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--out", type=Path, default=Path("reports/continuation_baseline"))
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    one_minute = load_zip(args.dataset)
    bars = resample_5m(one_minute)
    sessions = build_session_table(one_minute, bars)
    leaderboard, trades_by_name, funnels = evaluate_continuation_baselines(
        one_minute, bars, sessions
    )
    leaderboard.to_csv(args.out / "leaderboard.csv", index=False)
    for name, trades in trades_by_name.items():
        directory = args.out / name
        directory.mkdir(parents=True, exist_ok=True)
        trades.to_csv(directory / "trades.csv", index=False)
        pd.DataFrame([funnels[name].as_dict()]).to_csv(directory / "funnel.csv", index=False)
        _attribution(trades, "session").to_csv(directory / "by_session.csv", index=False)
        _attribution(trades, "day_of_week").to_csv(directory / "by_weekday.csv", index=False)
        _attribution(trades, "direction").to_csv(directory / "by_direction.csv", index=False)
        _attribution(trades, "exit_reason").to_csv(directory / "by_exit_reason.csv", index=False)
    print(leaderboard.to_string(index=False))


if __name__ == "__main__":
    main()
