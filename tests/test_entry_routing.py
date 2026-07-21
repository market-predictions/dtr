from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from dtr_lab.research import engine as base
from dtr_lab.research.entry_routing import (
    EntryRouteConfig,
    PreparedEntryRouting,
    _fixed_stop,
    _signal_config_signature,
    _simulate_fixed_stop_trade_np,
    compare_entry_route_portfolios,
    route_signal,
    simulate_entry_route,
)


def _bars(
    open_price: list[float],
    high: list[float],
    low: list[float],
    close: list[float],
    *,
    epoch: list[int] | None = None,
    reset: list[bool] | None = None,
) -> pd.DataFrame:
    timestamp = pd.date_range("2025-01-02 09:00", periods=len(open_price), freq="5min")
    epoch = epoch or [0] * len(open_price)
    reset = reset or [False] * len(open_price)
    return pd.DataFrame(
        {
            "timestamp": timestamp,
            "bar_end": timestamp + pd.Timedelta(minutes=5),
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "atr14": np.ones(len(open_price)),
            "state_epoch_end": epoch,
            "contains_reset_gap": reset,
        }
    )


def _one_minute(bars: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for row in bars.itertuples(index=False):
        for minute in range(5):
            rows.append(
                {
                    "timestamp": pd.Timestamp(row.timestamp) + pd.Timedelta(minutes=minute),
                    "open": float(row.open),
                    "high": float(row.high),
                    "low": float(row.low),
                    "close": float(row.close),
                    "gap_type": "NONE",
                    "gap_reset_state": False,
                    "gap_reject_trade_bridge": False,
                }
            )
    return pd.DataFrame(rows)


def _signal(direction: int, bars: pd.DataFrame, entry: int = 0) -> base.CandidateSignal:
    return base.CandidateSignal(
        session="NEW_YORK_9AM",
        session_date=pd.Timestamp("2025-01-02"),
        direction=direction,
        sweep_index=0,
        entry_index=entry,
        entry_time=pd.Timestamp(bars.iloc[entry]["bar_end"]),
        entry_price_raw=float(bars.iloc[entry]["close"]),
        sweep_extreme=95.0 if direction > 0 else 105.0,
        range_high=104.0,
        range_low=96.0,
        pivot=100.0,
        sweep_score=3,
        day_of_week=3,
    )


def _cfg(**kwargs: object) -> base.StrategyConfig:
    defaults = {
        "name": "fixture",
        "entry_mode": "break_close",
        "stop_buffer_ticks": 2,
        "stop_atr_frac": 0.0,
        "time_close_mode": "none",
        "max_hold_bars": 4,
        "slippage_ticks_each_side": 0.0,
        "commission_per_side": 0.0,
        "tick_size": 0.25,
    }
    defaults.update(kwargs)
    return base.StrategyConfig(**defaults)


def test_break_close_route_is_identity() -> None:
    bars = _bars([100.0], [102.0], [99.0], [101.0])
    signal = _signal(1, bars)
    routed, decision = route_signal(
        _one_minute(bars), bars, signal, _cfg(), EntryRouteConfig("base", "break_close")
    )

    assert routed is signal
    assert decision.filled
    assert decision.reason == "BREAK_CLOSE"
    assert decision.latency_minutes == 0
    assert decision.price_improvement_ticks == 0.0


def test_bullish_pullback_waits_for_causal_response_close() -> None:
    bars = _bars(
        [101.0, 100.5, 99.8],
        [102.0, 101.0, 101.5],
        [100.5, 99.5, 99.5],
        [101.0, 99.8, 101.0],
    )
    signal = _signal(1, bars)
    routed, decision = route_signal(
        _one_minute(bars),
        bars,
        signal,
        _cfg(),
        EntryRouteConfig("pullback", "first_pullback", max_extension_risk=10.0),
    )

    assert routed is not None
    assert decision.touch_index == 1
    assert routed.entry_index == 2
    assert routed.entry_price_raw == 101.0
    assert decision.reason == "PULLBACK_RESPONSE"
    assert decision.latency_minutes == 10


def test_bearish_pullback_is_symmetric() -> None:
    bars = _bars(
        [99.0, 99.5, 100.2],
        [99.5, 100.5, 100.5],
        [98.0, 99.0, 98.5],
        [99.0, 100.2, 99.0],
    )
    signal = _signal(-1, bars)
    routed, decision = route_signal(
        _one_minute(bars),
        bars,
        signal,
        _cfg(),
        EntryRouteConfig("pullback", "first_pullback", max_extension_risk=10.0),
    )

    assert routed is not None
    assert decision.touch_index == 1
    assert routed.entry_index == 2
    assert routed.entry_price_raw == 99.0
    assert decision.reason == "PULLBACK_RESPONSE"


def test_pullback_no_touch_expires() -> None:
    bars = _bars(
        [101.0, 102.0, 103.0],
        [102.0, 103.0, 104.0],
        [100.5, 101.5, 102.5],
        [101.0, 102.5, 103.5],
    )
    routed, decision = route_signal(
        _one_minute(bars),
        bars,
        _signal(1, bars),
        _cfg(),
        EntryRouteConfig(
            "pullback", "first_pullback", expiry_bars=2, max_extension_risk=10.0
        ),
    )

    assert routed is None
    assert decision.reason == "NO_TOUCH_EXPIRED"


def test_pullback_invalidates_before_response() -> None:
    bars = _bars(
        [101.0, 100.5],
        [102.0, 101.0],
        [100.5, 94.0],
        [101.0, 100.5],
    )
    routed, decision = route_signal(
        _one_minute(bars),
        bars,
        _signal(1, bars),
        _cfg(),
        EntryRouteConfig("pullback", "first_pullback", max_extension_risk=10.0),
    )

    assert routed is None
    assert decision.reason == "INVALIDATED"


def test_reset_terminates_pullback_state() -> None:
    bars = _bars(
        [101.0, 100.5],
        [102.0, 101.0],
        [100.5, 99.5],
        [101.0, 100.5],
        epoch=[0, 1],
        reset=[False, True],
    )
    routed, decision = route_signal(
        _one_minute(bars),
        bars,
        _signal(1, bars),
        _cfg(),
        EntryRouteConfig("pullback", "first_pullback", max_extension_risk=10.0),
    )

    assert routed is None
    assert decision.reason == "RESET"


def test_hybrid_selection_is_fixed_at_signal_time() -> None:
    near = _bars([100.0], [101.0], [99.0], [100.2])
    far = _bars([100.0], [102.0], [99.0], [101.0])
    route = EntryRouteConfig("hybrid", "hybrid", hybrid_extension_atr=0.35)

    _, near_decision = route_signal(_one_minute(near), near, _signal(1, near), _cfg(), route)
    _, far_decision = route_signal(_one_minute(far), far, _signal(1, far), _cfg(), route)

    assert near_decision.route_selected == "break_close"
    assert far_decision.route_selected == "first_pullback"


def test_fixed_stop_simulator_matches_base_for_break_close() -> None:
    bars = _bars(
        [101.0, 101.0],
        [102.0, 104.0],
        [100.5, 100.5],
        [101.0, 103.0],
    )
    one = _one_minute(bars)
    signal = _signal(1, bars)
    cfg = _cfg(tp1_rr=1.0, runner_rr=2.0, tp1_fraction=0.5)
    arrays = base.prepare_market_arrays(one)
    stop = _fixed_stop(signal, bars, cfg)

    expected = base._simulate_trade_np(*arrays, bars, signal, cfg)
    actual = _simulate_fixed_stop_trade_np(*arrays, signal, cfg, stop)

    assert expected is not None and actual is not None
    assert actual.entry_price == expected.entry_price
    assert actual.stop_price == expected.stop_price
    assert actual.exit_time == expected.exit_time
    assert actual.exit_reason == expected.exit_reason
    assert actual.pnl_r == pytest.approx(expected.pnl_r)
    assert actual.pnl_dollars == pytest.approx(expected.pnl_dollars)
    assert actual.mfe_r == pytest.approx(expected.mfe_r)
    assert actual.mae_r == pytest.approx(expected.mae_r)


def test_prepared_context_rejects_signal_config_change() -> None:
    cfg = _cfg()
    prepared = PreparedEntryRouting(
        signals=(),
        sessions=0,
        signal_config_signature=_signal_config_signature(cfg),
    )
    with pytest.raises(ValueError, match="signal config"):
        simulate_entry_route(
            pd.DataFrame({"timestamp": []}),
            pd.DataFrame(),
            _cfg(pivot_len=2),
            EntryRouteConfig("base", "break_close"),
            prepared,
            market_arrays=(
                np.array([], dtype=np.int64),
                np.array([]),
                np.array([]),
                np.array([]),
                np.array([]),
            ),
        )


def _portfolio_row(
    session: str,
    date: str,
    direction: int,
    entry_time: str,
    pnl_r: float,
) -> dict[str, object]:
    return {
        "session": session,
        "session_date": date,
        "direction": direction,
        "entry_time": entry_time,
        "pnl_r": pnl_r,
    }


def test_compare_portfolios_attributes_removed_and_added() -> None:
    reference = pd.DataFrame(
        [
            _portfolio_row("A", "2025-01-01", 1, "2025-01-01 10:00", 1.0),
            _portfolio_row("A", "2025-01-02", -1, "2025-01-02 10:00", -1.0),
        ]
    )
    candidate = pd.DataFrame(
        [
            _portfolio_row("A", "2025-01-02", -1, "2025-01-02 10:00", -1.0),
            _portfolio_row("B", "2025-01-03", 1, "2025-01-03 11:00", 0.5),
        ]
    )

    summary, attribution = compare_entry_route_portfolios(reference, candidate)

    assert summary == {"retained": 1, "removed": 1, "added": 1}
    assert set(attribution["status"]) == {"removed", "added"}
