from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

ObservationUnit = Literal["session", "date"]


@dataclass(frozen=True)
class FamilywiseResult:
    selected_candidate: str
    selected_mean: float
    selected_t: float
    max_t_p_value: float
    best_mean_p_value: float
    iterations: int
    seed: int

    def as_dict(self) -> dict[str, object]:
        return {
            "selected_candidate": self.selected_candidate,
            "selected_mean": self.selected_mean,
            "selected_t": self.selected_t,
            "max_t_p_value": self.max_t_p_value,
            "best_mean_p_value": self.best_mean_p_value,
            "iterations": self.iterations,
            "seed": self.seed,
        }


@dataclass(frozen=True)
class ReselectionResult:
    selected_candidate: str
    selected_frequency: float
    winner_change_probability: float
    effective_selected_candidates: float
    iterations: int
    seed: int
    frequencies: dict[str, float]

    def as_dict(self) -> dict[str, object]:
        return {
            "selected_candidate": self.selected_candidate,
            "selected_frequency": self.selected_frequency,
            "winner_change_probability": self.winner_change_probability,
            "effective_selected_candidates": self.effective_selected_candidates,
            "iterations": self.iterations,
            "seed": self.seed,
            "frequencies": self.frequencies,
        }


def _require_trade_columns(trades: pd.DataFrame) -> None:
    required = {"candidate_id", "session_date", "session", "pnl_r"}
    missing = required.difference(trades.columns)
    if missing:
        raise ValueError(f"Missing candidate trade columns: {sorted(missing)}")


def align_candidate_returns(
    trades: pd.DataFrame,
    *,
    candidate_ids: Iterable[str] | None = None,
    observation_unit: ObservationUnit = "session",
) -> pd.DataFrame:
    """Align candidate returns and assign zero where a candidate takes no trade."""

    _require_trade_columns(trades)
    if observation_unit not in ("session", "date"):
        raise ValueError(f"Unknown observation unit: {observation_unit}")

    work = trades.copy()
    work["candidate_id"] = work["candidate_id"].astype(str)
    work["session_date"] = pd.to_datetime(work["session_date"]).dt.normalize()
    candidates = sorted(
        set(str(value) for value in candidate_ids)
        if candidate_ids is not None
        else set(work["candidate_id"])
    )
    if not candidates:
        raise ValueError("At least one candidate is required")

    if observation_unit == "session":
        index_columns = ["session_date", "session"]
    else:
        index_columns = ["session_date"]

    observations = work[index_columns].drop_duplicates().sort_values(index_columns)
    grouped = (
        work.groupby([*index_columns, "candidate_id"], sort=True, as_index=False)["pnl_r"]
        .sum()
        .pivot(index=index_columns, columns="candidate_id", values="pnl_r")
        .reindex(columns=candidates, fill_value=0.0)
        .fillna(0.0)
        .sort_index()
    )

    full_index = pd.MultiIndex.from_frame(observations) if len(index_columns) > 1 else pd.Index(
        observations[index_columns[0]], name=index_columns[0]
    )
    return grouped.reindex(full_index, fill_value=0.0).astype(float)


def candidate_stream_hashes(matrix: pd.DataFrame) -> dict[str, str]:
    """Hash each aligned return stream with its observation index."""

    index_payload = [tuple(value) if isinstance(value, tuple) else value for value in matrix.index]
    hashes: dict[str, str] = {}
    for column in matrix.columns:
        payload = {
            "candidate_id": str(column),
            "index": [str(value) for value in index_payload],
            "returns": [float(value) for value in matrix[column].to_numpy(float)],
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        hashes[str(column)] = hashlib.sha256(encoded).hexdigest()
    return hashes


def _date_groups(index: pd.Index) -> list[np.ndarray]:
    if isinstance(index, pd.MultiIndex):
        dates = pd.to_datetime(index.get_level_values("session_date")).normalize()
    else:
        dates = pd.to_datetime(index).normalize()
    groups: list[np.ndarray] = []
    for date in pd.Index(dates).unique():
        groups.append(np.flatnonzero(dates == date))
    return groups


def _studentized_means(values: np.ndarray) -> np.ndarray:
    means = np.mean(values, axis=0)
    std = np.std(values, axis=0, ddof=1)
    se = std / np.sqrt(values.shape[0])
    return np.divide(means, se, out=np.zeros_like(means), where=se > 0)


def familywise_selection_test(
    matrix: pd.DataFrame,
    *,
    selected_candidate: str,
    iterations: int = 20_000,
    seed: int = 20260722,
) -> FamilywiseResult:
    """Joint market-date block max-t and best-mean tests under a centered null."""

    if matrix.shape[0] < 2 or matrix.shape[1] < 1:
        raise ValueError("Matrix must contain at least two observations and one candidate")
    if selected_candidate not in matrix.columns:
        raise ValueError("Selected candidate is not present in matrix")
    if iterations < 1:
        raise ValueError("iterations must be positive")

    values = matrix.to_numpy(float)
    means = np.mean(values, axis=0)
    observed_t = _studentized_means(values)
    selected_index = list(matrix.columns).index(selected_candidate)
    centered = values - means
    groups = _date_groups(matrix.index)
    rng = np.random.default_rng(seed)
    max_t_exceed = 0
    max_mean_exceed = 0
    observed_selected_t = float(observed_t[selected_index])
    observed_best_mean = float(np.max(means))

    for _ in range(iterations):
        chosen = rng.integers(0, len(groups), size=len(groups))
        row_indexes = np.concatenate([groups[index] for index in chosen])
        sample = centered[row_indexes]
        if float(np.max(_studentized_means(sample))) >= observed_selected_t:
            max_t_exceed += 1
        if float(np.max(np.mean(sample, axis=0))) >= observed_best_mean:
            max_mean_exceed += 1

    return FamilywiseResult(
        selected_candidate=selected_candidate,
        selected_mean=float(means[selected_index]),
        selected_t=observed_selected_t,
        max_t_p_value=float((max_t_exceed + 1) / (iterations + 1)),
        best_mean_p_value=float((max_mean_exceed + 1) / (iterations + 1)),
        iterations=iterations,
        seed=seed,
    )


def bootstrap_reselection(
    matrix: pd.DataFrame,
    *,
    selected_candidate: str,
    iterations: int = 20_000,
    seed: int = 20260723,
) -> ReselectionResult:
    """Reselect the highest-mean candidate under joint market-date block resampling."""

    if selected_candidate not in matrix.columns:
        raise ValueError("Selected candidate is not present in matrix")
    if matrix.shape[0] < 2 or matrix.shape[1] < 1:
        raise ValueError("Matrix must contain at least two observations and one candidate")
    groups = _date_groups(matrix.index)
    values = matrix.to_numpy(float)
    columns = [str(column) for column in matrix.columns]
    counts = np.zeros(len(columns), dtype=int)
    rng = np.random.default_rng(seed)

    for _ in range(iterations):
        chosen = rng.integers(0, len(groups), size=len(groups))
        row_indexes = np.concatenate([groups[index] for index in chosen])
        winner = int(np.argmax(np.mean(values[row_indexes], axis=0)))
        counts[winner] += 1

    frequencies_array = counts / iterations
    positive = frequencies_array[frequencies_array > 0]
    entropy = -float(np.sum(positive * np.log(positive)))
    frequencies = {
        candidate: float(frequency)
        for candidate, frequency in zip(columns, frequencies_array, strict=True)
    }
    selected_frequency = frequencies[selected_candidate]
    return ReselectionResult(
        selected_candidate=selected_candidate,
        selected_frequency=selected_frequency,
        winner_change_probability=1.0 - selected_frequency,
        effective_selected_candidates=float(np.exp(entropy)),
        iterations=iterations,
        seed=seed,
        frequencies=frequencies,
    )


def duplicate_stream_groups(matrix: pd.DataFrame) -> list[list[str]]:
    """Return groups of candidates with exactly identical aligned return streams."""

    by_hash: dict[str, list[str]] = {}
    for candidate, digest in candidate_stream_hashes(matrix).items():
        by_hash.setdefault(digest, []).append(candidate)
    return sorted(
        [sorted(group) for group in by_hash.values() if len(group) > 1],
        key=lambda group: (len(group), group),
        reverse=True,
    )
