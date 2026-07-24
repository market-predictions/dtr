from __future__ import annotations

import numpy as np
import pandas as pd

from stoic_123_lab.reporting import date_block_bootstrap


def _reference_bootstrap(
    trades: pd.DataFrame,
    *,
    iterations: int,
    seed: int,
) -> dict[str, float | int]:
    work = trades.copy()
    work["block"] = pd.to_datetime(work["entry_time"]).dt.normalize()
    grouped = work.groupby("block", sort=True)["pnl_r"]
    block_sums = grouped.sum().to_numpy(float)
    block_counts = grouped.size().to_numpy(np.int64)
    rng = np.random.default_rng(seed)
    means = np.empty(iterations)
    for iteration in range(iterations):
        selected = rng.integers(0, len(block_sums), size=len(block_sums))
        means[iteration] = block_sums[selected].sum() / block_counts[selected].sum()
    return {
        "blocks": len(block_sums),
        "observed_expectancy_r": float(work["pnl_r"].mean()),
        "lo95_expectancy_r": float(np.quantile(means, 0.025)),
        "hi95_expectancy_r": float(np.quantile(means, 0.975)),
        "prob_expectancy_positive": float(np.mean(means > 0)),
    }


def test_batched_bootstrap_is_exactly_equal_to_reference_loop() -> None:
    trades = pd.DataFrame(
        {
            "entry_time": pd.to_datetime(
                [
                    "2026-01-02 14:30",
                    "2026-01-02 15:00",
                    "2026-01-05 14:30",
                    "2026-01-06 14:30",
                    "2026-01-06 15:00",
                ]
            ),
            "pnl_r": [1.0, -0.25, -1.0, 2.0, 0.5],
        }
    )
    expected = _reference_bootstrap(trades, iterations=2_500, seed=12345)
    observed = date_block_bootstrap(
        trades,
        iterations=2_500,
        seed=12345,
        batch_size=257,
    )
    assert observed == expected


def test_bootstrap_rejects_invalid_batch_size() -> None:
    trades = pd.DataFrame(
        {
            "entry_time": pd.to_datetime(["2026-01-02 14:30"]),
            "pnl_r": [1.0],
        }
    )
    try:
        date_block_bootstrap(trades, batch_size=0)
    except ValueError as error:
        assert "batch_size" in str(error)
    else:
        raise AssertionError("invalid batch_size did not fail")
