from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .model import CandidateState, TrendConfig

_REQUIRED_OHLC = {"open", "high", "low", "close"}


@dataclass
class _Candidate:
    side: str
    state: CandidateState = CandidateState.NEUTRAL
    first_pos: int | None = None
    first_value: float = math.nan
    second_pos: int | None = None
    second_value: float = math.nan
    neckline_pos: int | None = None
    neckline_value: float = math.nan
    double_observed_pos: int | None = None
    bos_pos: int | None = None
    bos_extreme: float = math.nan
    retest_pos: int | None = None
    pullback_pos: int | None = None
    pullback_value: float = math.nan
    confirm_pos: int | None = None

    def reset(self) -> None:
        replacement = _Candidate(self.side)
        self.__dict__.update(replacement.__dict__)


def _validate_ohlc(frame: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(_REQUIRED_OHLC - set(frame.columns))
    if missing:
        raise ValueError(f"OHLC frame missing columns: {missing}")
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise TypeError("OHLC frame index must be a DatetimeIndex")
    if frame.index.has_duplicates:
        raise ValueError("OHLC frame contains duplicate timestamps")
    out = frame.sort_index().copy()
    for column in sorted(_REQUIRED_OHLC):
        out[column] = pd.to_numeric(out[column], errors="raise")
    invalid = (
        ~np.isfinite(out[list(sorted(_REQUIRED_OHLC))]).all(axis=1)
        | out["high"].lt(out[["open", "close", "low"]].max(axis=1))
        | out["low"].gt(out[["open", "close", "high"]].min(axis=1))
    )
    if invalid.any():
        raise ValueError("OHLC frame contains invalid bars")
    return out


def average_true_range(frame: pd.DataFrame, length: int = 20) -> pd.Series:
    if length < 2:
        raise ValueError("ATR length must be at least two")
    bars = _validate_ohlc(frame)
    prior_close = bars["close"].shift(1)
    true_range = pd.concat(
        [
            bars["high"] - bars["low"],
            (bars["high"] - prior_close).abs(),
            (bars["low"] - prior_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.rolling(length, min_periods=length).mean().rename("atr")


def confirmed_swings(
    frame: pd.DataFrame,
    config: TrendConfig = TrendConfig(),
) -> pd.DataFrame:
    bars = _validate_ohlc(frame)
    highs = bars["high"].to_numpy(dtype=float)
    lows = bars["low"].to_numpy(dtype=float)
    rows: list[dict[str, Any]] = []
    stop = len(bars) - config.swing_right
    for pivot_pos in range(config.swing_left, stop):
        observed_pos = pivot_pos + config.swing_right
        pivot_low = lows[pivot_pos]
        pivot_high = highs[pivot_pos]
        left_low = lows[pivot_pos - config.swing_left : pivot_pos]
        right_low = lows[pivot_pos + 1 : pivot_pos + 1 + config.swing_right]
        left_high = highs[pivot_pos - config.swing_left : pivot_pos]
        right_high = highs[pivot_pos + 1 : pivot_pos + 1 + config.swing_right]
        if np.all(pivot_low < left_low) and np.all(pivot_low < right_low):
            rows.append(
                {
                    "kind": "LOW",
                    "pivot_pos": pivot_pos,
                    "observed_pos": observed_pos,
                    "pivot_timestamp": bars.index[pivot_pos],
                    "observed_timestamp": bars.index[observed_pos],
                    "value": float(pivot_low),
                }
            )
        if np.all(pivot_high > left_high) and np.all(pivot_high > right_high):
            rows.append(
                {
                    "kind": "HIGH",
                    "pivot_pos": pivot_pos,
                    "observed_pos": observed_pos,
                    "pivot_timestamp": bars.index[pivot_pos],
                    "observed_timestamp": bars.index[observed_pos],
                    "value": float(pivot_high),
                }
            )
    columns = [
        "kind",
        "pivot_pos",
        "observed_pos",
        "pivot_timestamp",
        "observed_timestamp",
        "value",
    ]
    return pd.DataFrame(rows, columns=columns)


def _qualifying_pair(
    current: dict[str, Any],
    prior_extremes: list[dict[str, Any]],
    opposite_extremes: list[dict[str, Any]],
    *,
    atr: float,
    side: str,
    config: TrendConfig,
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    if not np.isfinite(atr) or atr <= 0.0:
        return None
    for prior in reversed(prior_extremes):
        separation = int(current["pivot_pos"]) - int(prior["pivot_pos"])
        if separation < config.min_separation_bars:
            continue
        if separation > config.max_separation_bars:
            break
        if abs(float(current["value"]) - float(prior["value"])) > (
            config.double_tolerance_atr * atr
        ):
            continue
        between = [
            item
            for item in opposite_extremes
            if int(prior["pivot_pos"])
            < int(item["pivot_pos"])
            < int(current["pivot_pos"])
        ]
        if not between:
            continue
        if side == "BULL":
            neckline = max(between, key=lambda item: float(item["value"]))
        else:
            neckline = min(between, key=lambda item: float(item["value"]))
        return prior, neckline
    return None


def _start_candidate(
    current: dict[str, Any],
    prior: dict[str, Any],
    neckline: dict[str, Any],
    *,
    side: str,
    observed_pos: int,
) -> _Candidate:
    return _Candidate(
        side=side,
        state=CandidateState.DOUBLE_EXTREME,
        first_pos=int(prior["pivot_pos"]),
        first_value=float(prior["value"]),
        second_pos=int(current["pivot_pos"]),
        second_value=float(current["value"]),
        neckline_pos=int(neckline["pivot_pos"]),
        neckline_value=float(neckline["value"]),
        double_observed_pos=observed_pos,
    )


def _first_extreme(current: dict[str, Any], side: str) -> _Candidate:
    return _Candidate(
        side=side,
        state=CandidateState.FIRST_EXTREME,
        first_pos=int(current["pivot_pos"]),
        first_value=float(current["value"]),
    )


def _snapshot(candidate: _Candidate, prefix: str) -> dict[str, object]:
    return {
        f"{prefix}_state": candidate.state.value,
        f"{prefix}_first_pos": candidate.first_pos,
        f"{prefix}_first_value": candidate.first_value,
        f"{prefix}_second_pos": candidate.second_pos,
        f"{prefix}_second_value": candidate.second_value,
        f"{prefix}_neckline": candidate.neckline_value,
        f"{prefix}_bos_extreme": candidate.bos_extreme,
        f"{prefix}_retest_pos": candidate.retest_pos,
        f"{prefix}_pullback_pos": candidate.pullback_pos,
        f"{prefix}_pullback_value": candidate.pullback_value,
        f"{prefix}_confirm_pos": candidate.confirm_pos,
    }


def _process_low_swing(
    swing: dict[str, Any],
    *,
    observed_pos: int,
    atr: float,
    bull: _Candidate,
    lows: list[dict[str, Any]],
    highs: list[dict[str, Any]],
    config: TrendConfig,
    events: list[str],
) -> _Candidate:
    if bull.state in {CandidateState.NEUTRAL, CandidateState.FIRST_EXTREME}:
        pair = _qualifying_pair(
            swing,
            lows,
            highs,
            atr=atr,
            side="BULL",
            config=config,
        )
        if pair is None:
            return _first_extreme(swing, "BULL")
        prior, neckline = pair
        events.append("BULL_DOUBLE_BOTTOM")
        return _start_candidate(
            swing,
            prior,
            neckline,
            side="BULL",
            observed_pos=observed_pos,
        )
    if bull.state in {CandidateState.BOS, CandidateState.RETEST}:
        after_retest = bull.retest_pos is not None and int(swing["pivot_pos"]) >= bull.retest_pos
        above_bottoms = float(swing["value"]) > max(
            bull.first_value,
            bull.second_value,
        )
        if after_retest and above_bottoms:
            bull.state = CandidateState.PULLBACK_CONFIRMED
            bull.pullback_pos = int(swing["pivot_pos"])
            bull.pullback_value = float(swing["value"])
            events.append("BULL_HIGHER_LOW")
    return bull


def _process_high_swing(
    swing: dict[str, Any],
    *,
    observed_pos: int,
    atr: float,
    bear: _Candidate,
    lows: list[dict[str, Any]],
    highs: list[dict[str, Any]],
    config: TrendConfig,
    events: list[str],
) -> _Candidate:
    if bear.state in {CandidateState.NEUTRAL, CandidateState.FIRST_EXTREME}:
        pair = _qualifying_pair(
            swing,
            highs,
            lows,
            atr=atr,
            side="BEAR",
            config=config,
        )
        if pair is None:
            return _first_extreme(swing, "BEAR")
        prior, neckline = pair
        events.append("BEAR_DOUBLE_TOP")
        return _start_candidate(
            swing,
            prior,
            neckline,
            side="BEAR",
            observed_pos=observed_pos,
        )
    if bear.state in {CandidateState.BOS, CandidateState.RETEST}:
        after_retest = bear.retest_pos is not None and int(swing["pivot_pos"]) >= bear.retest_pos
        below_tops = float(swing["value"]) < min(
            bear.first_value,
            bear.second_value,
        )
        if after_retest and below_tops:
            bear.state = CandidateState.PULLBACK_CONFIRMED
            bear.pullback_pos = int(swing["pivot_pos"])
            bear.pullback_value = float(swing["value"])
            events.append("BEAR_LOWER_HIGH")
    return bear
