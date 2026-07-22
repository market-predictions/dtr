from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class IntervalEstimate:
    estimate: float
    lo95: float
    hi95: float
    iterations: int
    seed: int

    def as_dict(self) -> dict[str, float | int]:
        return {
            "estimate": self.estimate,
            "lo95": self.lo95,
            "hi95": self.hi95,
            "iterations": self.iterations,
            "seed": self.seed,
        }


def _percentile_interval(
    samples: np.ndarray, estimate: float, iterations: int, seed: int
) -> IntervalEstimate:
    return IntervalEstimate(
        estimate=float(estimate),
        lo95=float(np.quantile(samples, 0.025)),
        hi95=float(np.quantile(samples, 0.975)),
        iterations=int(iterations),
        seed=int(seed),
    )


def trade_bootstrap_mean(
    values: Iterable[float], *, iterations: int = 20_000, seed: int = 20260722
) -> IntervalEstimate:
    array = np.asarray(list(values), dtype=float)
    if array.size == 0:
        raise ValueError("At least one value is required")
    rng = np.random.default_rng(seed)
    draws = rng.choice(array, size=(iterations, array.size), replace=True).mean(axis=1)
    return _percentile_interval(draws, float(array.mean()), iterations, seed)


def block_bootstrap_mean(
    frame: pd.DataFrame,
    *,
    value_column: str,
    block_column: str,
    iterations: int = 20_000,
    seed: int = 20260722,
) -> IntervalEstimate:
    if frame.empty:
        raise ValueError("At least one observation is required")
    if value_column not in frame or block_column not in frame:
        raise ValueError("Missing value or block column")
    groups = [
        group[value_column].to_numpy(float)
        for _, group in frame.groupby(block_column, sort=True)
    ]
    if not groups:
        raise ValueError("At least one block is required")
    rng = np.random.default_rng(seed)
    samples = np.empty(iterations, dtype=float)
    block_count = len(groups)
    for i in range(iterations):
        selected = rng.integers(0, block_count, size=block_count)
        values = np.concatenate([groups[index] for index in selected])
        samples[i] = float(values.mean())
    return _percentile_interval(samples, float(frame[value_column].mean()), iterations, seed)


def sign_flip_p_value(
    values: Iterable[float], *, iterations: int = 100_000, seed: int = 20260722
) -> float:
    array = np.asarray(list(values), dtype=float)
    if array.size == 0:
        raise ValueError("At least one value is required")
    observed = float(array.mean())
    rng = np.random.default_rng(seed)
    exceed = 0
    batch = 2_000
    completed = 0
    while completed < iterations:
        n = min(batch, iterations - completed)
        signs = rng.choice(np.array([-1.0, 1.0]), size=(n, array.size))
        means = (signs * array).mean(axis=1)
        exceed += int(np.sum(means >= observed))
        completed += n
    return float((exceed + 1) / (iterations + 1))


def familywise_max_t_p_value(
    candidate_returns: np.ndarray,
    *,
    selected_index: int,
    iterations: int = 20_000,
    seed: int = 20260722,
) -> float:
    """Centered max-t bootstrap across aligned candidate return columns.

    This requires an aligned observation matrix. It is intentionally not applied when
    candidate trade sets cannot be represented on a common sampling unit.
    """
    matrix = np.asarray(candidate_returns, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] < 2 or matrix.shape[1] < 1:
        raise ValueError("candidate_returns must be a 2D observation-by-candidate matrix")
    if not 0 <= selected_index < matrix.shape[1]:
        raise ValueError("selected_index out of range")
    means = np.nanmean(matrix, axis=0)
    std = np.nanstd(matrix, axis=0, ddof=1)
    counts = np.sum(np.isfinite(matrix), axis=0)
    se = std / np.sqrt(counts)
    observed_t = means[selected_index] / se[selected_index]
    centered = matrix - means
    rng = np.random.default_rng(seed)
    exceed = 0
    for _ in range(iterations):
        indexes = rng.integers(0, matrix.shape[0], size=matrix.shape[0])
        sample = centered[indexes]
        sample_mean = np.nanmean(sample, axis=0)
        sample_std = np.nanstd(sample, axis=0, ddof=1)
        sample_count = np.sum(np.isfinite(sample), axis=0)
        sample_t = sample_mean / (sample_std / np.sqrt(sample_count))
        if np.nanmax(sample_t) >= observed_t:
            exceed += 1
    return float((exceed + 1) / (iterations + 1))
