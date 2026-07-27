from __future__ import annotations

import math

import numpy as np
import pandas as pd


def cluster_permutation_p_value(
    data: pd.DataFrame,
    *,
    treatment_column: str,
    outcome_column: str,
    observed_effect: float,
    seed: int,
    samples: int,
) -> float:
    """Permute treatment bundles between same-size clusters within strata."""
    if not math.isfinite(observed_effect):
        return math.nan
    if samples < 1:
        raise ValueError("samples must be positive")
    required = {
        "instrument",
        "month_id",
        "year",
        treatment_column,
        outcome_column,
    }
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"cluster permutation missing columns: {missing}")

    work = data.reset_index(drop=True).copy()
    work["cluster"] = (
        work["instrument"].astype(str) + "::" + work["month_id"].astype(str)
    )
    treatment = work[treatment_column].astype(bool).to_numpy()
    outcome = work[outcome_column].astype(float).to_numpy()
    bundles: list[tuple[list[np.ndarray], list[np.ndarray]]] = []
    for (_instrument, _year), stratum in work.groupby(
        ["instrument", "year"],
        sort=False,
    ):
        by_size: dict[int, list[np.ndarray]] = {}
        for _cluster, cluster in stratum.groupby("cluster", sort=False):
            ordered = cluster.sort_values("side") if "side" in cluster else cluster
            index = ordered.index.to_numpy(dtype=int)
            by_size.setdefault(len(index), []).append(index)
        for indexes in by_size.values():
            if len(indexes) < 2:
                continue
            vectors = [treatment[index].copy() for index in indexes]
            bundles.append((indexes, vectors))

    rng = np.random.default_rng(seed)
    exceed = 0
    valid = 0
    for _ in range(samples):
        permuted = treatment.copy()
        for indexes, vectors in bundles:
            order = rng.permutation(len(vectors))
            for target_position, vector_position in enumerate(order):
                permuted[indexes[target_position]] = vectors[vector_position]
        if permuted.sum() and (~permuted).sum():
            effect = outcome[permuted].mean() - outcome[~permuted].mean()
            exceed += int(effect >= observed_effect)
            valid += 1
    return math.nan if valid == 0 else (exceed + 1.0) / (valid + 1.0)
