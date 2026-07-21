from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from dtr_lab.research import (
    StrategyConfig,
    build_session_table,
    candidate_grid,
    evaluate_configs,
    load_zip,
    metrics,
    resample_5m,
    run_backtest,
)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("dataset")
    p.add_argument("--out", default="reports")
    p.add_argument(
        "--pack",
        choices=["baseline", "bos", "sweep", "regime", "timing", "risk", "exit"],
        default="baseline",
    )
    p.add_argument("--top", type=int, default=20)
    args = p.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    one = load_zip(args.dataset)
    bars = resample_5m(one)
    sessions = build_session_table(one, bars)
    base = StrategyConfig()
    train_end = pd.Timestamp("2024-07-01")
    validation_end = pd.Timestamp("2025-04-01")
    if args.pack == "baseline":
        trades, funnel = run_backtest(one, bars, sessions, base)
        trades.to_csv(out / "baseline_trades.csv", index=False)
        print(metrics(trades))
        print(funnel.as_dict())
        return
    configs = candidate_grid(base, args.pack)
    board = evaluate_configs(one, bars, sessions, configs, train_end, validation_end)
    board.to_csv(out / f"{args.pack}_leaderboard.csv", index=False)
    print(
        board.head(args.top)[
            [
                "name",
                "robust_score",
                "train_trades",
                "train_expectancy_r",
                "train_max_drawdown_r",
                "val_trades",
                "val_expectancy_r",
                "val_profit_factor",
                "val_max_drawdown_r",
                "val_net_r",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
