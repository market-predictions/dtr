from __future__ import annotations

import numpy as np
import pandas as pd

from dtr_lab.research.uncertainty import block_bootstrap_mean, sign_flip_p_value, trade_bootstrap_mean


def test_trade_bootstrap_is_deterministic() -> None:
    first = trade_bootstrap_mean([1.0, -0.5, 0.25, 0.75], iterations=2_000, seed=7)
    second = trade_bootstrap_mean([1.0, -0.5, 0.25, 0.75], iterations=2_000, seed=7)
    assert first == second
    assert first.lo95 <= first.estimate <= first.hi95


def test_block_bootstrap_resamples_whole_blocks() -> None:
    frame = pd.DataFrame({"pnl_r": [1.0, 1.0, -1.0, -1.0], "month": [1, 1, 2, 2]})
    result = block_bootstrap_mean(
        frame,
        value_column="pnl_r",
        block_column="month",
        iterations=2_000,
        seed=11,
    )
    assert result.estimate == 0.0
    assert result.lo95 <= -1.0
    assert result.hi95 >= 1.0


def test_sign_flip_detects_strong_positive_sample() -> None:
    p_value = sign_flip_p_value(np.full(20, 0.5), iterations=10_000, seed=19)
    assert p_value < 0.001
