from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

import numpy as np
import pandas as pd

from .model import CandidateState, DEFAULT_TREND_CONFIG, TrendConfig, TrendDirection
from .structure_common import (
    _Candidate,
    _process_high_swing,
    _process_low_swing,
    _snapshot,
    _validate_ohlc,
    average_true_range,
    confirmed_swings,
)


def build_structure_ledger(
    frame: pd.DataFrame,
    config: TrendConfig = DEFAULT_TREND_CONFIG,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    bars = _validate_ohlc(frame)
    bars["atr"] = average_true_range(bars, config.atr_length)
    swings = confirmed_swings(bars, config)
    by_observed_pos: defaultdict[int, list[dict[str, Any]]] = defaultdict(list)
    for item in swings.to_dict(orient="records"):
        by_observed_pos[int(item["observed_pos"])].append(item)

    confirmed_lows: list[dict[str, Any]] = []
    confirmed_highs: list[dict[str, Any]] = []
    bull = _Candidate("BULL")
    bear = _Candidate("BEAR")
    direction = TrendDirection.NONE
    structural_floor = math.nan
    structural_ceiling = math.nan
    rows: list[dict[str, object]] = []

    for position, (_timestamp, bar) in enumerate(bars.iterrows()):
        atr = float(bar["atr"]) if np.isfinite(bar["atr"]) else math.nan
        events: list[str] = []

        for swing in by_observed_pos.get(position, []):
            if swing["kind"] == "LOW":
                bull = _process_low_swing(
                    swing,
                    observed_pos=position,
                    atr=atr,
                    bull=bull,
                    lows=confirmed_lows,
                    highs=confirmed_highs,
                    config=config,
                    events=events,
                )
                confirmed_lows.append(swing)
            else:
                bear = _process_high_swing(
                    swing,
                    observed_pos=position,
                    atr=atr,
                    bear=bear,
                    lows=confirmed_lows,
                    highs=confirmed_highs,
                    config=config,
                    events=events,
                )
                confirmed_highs.append(swing)

        if np.isfinite(atr) and atr > 0.0:
            buffer = config.break_buffer_atr * atr
            band = config.retest_band_atr * atr

            if bull.state not in {
                CandidateState.NEUTRAL,
                CandidateState.FIRST_EXTREME,
                CandidateState.TREND_CONFIRMED,
            }:
                bottom = min(bull.first_value, bull.second_value)
                if float(bar["close"]) < bottom - buffer:
                    bull.reset()
                    events.append("BULL_CANDIDATE_INVALIDATED")
            if bear.state not in {
                CandidateState.NEUTRAL,
                CandidateState.FIRST_EXTREME,
                CandidateState.TREND_CONFIRMED,
            }:
                top = max(bear.first_value, bear.second_value)
                if float(bar["close"]) > top + buffer:
                    bear.reset()
                    events.append("BEAR_CANDIDATE_INVALIDATED")

            if (
                bull.state == CandidateState.DOUBLE_EXTREME
                and bull.double_observed_pos is not None
                and position - bull.double_observed_pos > config.max_bos_wait_bars
            ):
                bull.reset()
                events.append("BULL_BOS_TIMEOUT")
            if (
                bear.state == CandidateState.DOUBLE_EXTREME
                and bear.double_observed_pos is not None
                and position - bear.double_observed_pos > config.max_bos_wait_bars
            ):
                bear.reset()
                events.append("BEAR_BOS_TIMEOUT")
            if (
                bull.state == CandidateState.BOS
                and bull.bos_pos is not None
                and position - bull.bos_pos > config.max_retest_wait_bars
            ):
                bull.reset()
                events.append("BULL_RETEST_TIMEOUT")
            if (
                bear.state == CandidateState.BOS
                and bear.bos_pos is not None
                and position - bear.bos_pos > config.max_retest_wait_bars
            ):
                bear.reset()
                events.append("BEAR_RETEST_TIMEOUT")
            if (
                bull.state == CandidateState.PULLBACK_CONFIRMED
                and bull.pullback_pos is not None
                and position - (bull.pullback_pos + config.swing_right)
                > config.max_continuation_wait_bars
            ):
                bull.reset()
                events.append("BULL_CONTINUATION_TIMEOUT")
            if (
                bear.state == CandidateState.PULLBACK_CONFIRMED
                and bear.pullback_pos is not None
                and position - (bear.pullback_pos + config.swing_right)
                > config.max_continuation_wait_bars
            ):
                bear.reset()
                events.append("BEAR_CONTINUATION_TIMEOUT")

            if (
                bull.state == CandidateState.DOUBLE_EXTREME
                and float(bar["close"]) > bull.neckline_value + buffer
            ):
                bull.state = CandidateState.BOS
                bull.bos_pos = position
                bull.bos_extreme = float(bar["high"])
                events.append("BULL_BOS")
            if (
                bear.state == CandidateState.DOUBLE_EXTREME
                and float(bar["close"]) < bear.neckline_value - buffer
            ):
                bear.state = CandidateState.BOS
                bear.bos_pos = position
                bear.bos_extreme = float(bar["low"])
                events.append("BEAR_BOS")

            bull_retest = (
                bull.state == CandidateState.BOS
                and bull.bos_pos is not None
                and position > bull.bos_pos
                and float(bar["low"]) <= bull.neckline_value + band
                and float(bar["high"]) >= bull.neckline_value - band
            )
            if bull_retest:
                bull.state = CandidateState.RETEST
                bull.retest_pos = position
                events.append("BULL_RETEST")
            bear_retest = (
                bear.state == CandidateState.BOS
                and bear.bos_pos is not None
                and position > bear.bos_pos
                and float(bar["low"]) <= bear.neckline_value + band
                and float(bar["high"]) >= bear.neckline_value - band
            )
            if bear_retest:
                bear.state = CandidateState.RETEST
                bear.retest_pos = position
                events.append("BEAR_RETEST")

            bull_confirmed = (
                bull.state == CandidateState.PULLBACK_CONFIRMED
                and float(bar["close"]) > bull.bos_extreme + buffer
            )
            bear_confirmed = (
                bear.state == CandidateState.PULLBACK_CONFIRMED
                and float(bar["close"]) < bear.bos_extreme - buffer
            )
            if bull_confirmed and bear_confirmed:
                direction = TrendDirection.AMBIGUOUS_SHOCK
                structural_floor = math.nan
                structural_ceiling = math.nan
                bull.reset()
                bear.reset()
                events.append("AMBIGUOUS_SHOCK")
            elif bull_confirmed:
                bull.state = CandidateState.TREND_CONFIRMED
                bull.confirm_pos = position
                direction = TrendDirection.BULL
                structural_floor = bull.pullback_value
                structural_ceiling = math.nan
                bear.reset()
                events.append("BULL_TREND_CONFIRMED")
            elif bear_confirmed:
                bear.state = CandidateState.TREND_CONFIRMED
                bear.confirm_pos = position
                direction = TrendDirection.BEAR
                structural_ceiling = bear.pullback_value
                structural_floor = math.nan
                bull.reset()
                events.append("BEAR_TREND_CONFIRMED")

            if (
                direction == TrendDirection.BULL
                and np.isfinite(structural_floor)
                and float(bar["close"]) < structural_floor - buffer
            ):
                direction = TrendDirection.NONE
                structural_floor = math.nan
                if bull.state == CandidateState.TREND_CONFIRMED:
                    bull.reset()
                events.append("BULL_TREND_INVALIDATED")
            elif (
                direction == TrendDirection.BEAR
                and np.isfinite(structural_ceiling)
                and float(bar["close"]) > structural_ceiling + buffer
            ):
                direction = TrendDirection.NONE
                structural_ceiling = math.nan
                if bear.state == CandidateState.TREND_CONFIRMED:
                    bear.reset()
                events.append("BEAR_TREND_INVALIDATED")

        row: dict[str, object] = {
            "atr": atr,
            "confirmed_direction": direction.value,
            "structural_floor": structural_floor,
            "structural_ceiling": structural_ceiling,
            "events": ";".join(events),
        }
        row.update(_snapshot(bull, "bull"))
        row.update(_snapshot(bear, "bear"))
        rows.append(row)

    ledger = pd.DataFrame(rows, index=bars.index)
    ledger.index.name = bars.index.name
    return ledger, swings
