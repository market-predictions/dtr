from __future__ import annotations

import pandas as pd

from .shadow_common import (
    EXECUTION_TICK,
    SESSION_TIMEZONE,
    TARGET_RR,
    ShadowExecutionConfig,
    _adverse_price,
    _base_identity,
    _window_end,
    normalize_bar,
    normalize_event,
)


def simulate_event(
    event: pd.Series | dict[str, object],
    source: pd.DataFrame,
    cfg: ShadowExecutionConfig,
) -> dict[str, object]:
    identity = _base_identity(event)
    if identity["instrument"] != cfg.instrument:
        raise ValueError("event instrument does not match shadow configuration")
    if str(event["status"]) != "SIGNAL":
        raise ValueError("only SIGNAL events may enter the baseline")
    normalized = normalize_event(event)
    entry_time = pd.Timestamp(event["entry_timestamp"])
    if entry_time.tzinfo is None:
        raise ValueError("entry timestamp must be timezone-aware")
    entry_time = entry_time.tz_convert(SESSION_TIMEZONE)
    window_end = _window_end(event["trade_date"], identity["execution_window"])
    if not entry_time < window_end:
        raise ValueError("entry timestamp must precede window end")
    path = source[
        (source["timestamp"] >= entry_time) & (source["timestamp"] <= window_end)
    ].copy()
    bars: dict[pd.Timestamp, dict[str, object]] = {}
    for _, row in path.iterrows():
        timestamp = pd.Timestamp(row["timestamp"])
        bars[timestamp] = normalize_bar(
            row,
            direction=int(normalized["direction"]),
            entry_minute=timestamp == entry_time,
        )
    entry_row = bars.get(entry_time)
    if entry_row is None:
        return {
            **identity,
            **normalized,
            "status": "BLOCKED",
            "reason": "MISSING_ENTRY_MINUTE",
        }
    if int(entry_row["is_active_quote"]) <= 0:
        return {
            **identity,
            **normalized,
            "status": "BLOCKED",
            "reason": "INACTIVE_ENTRY_MINUTE",
        }
    direction = int(normalized["direction"])
    entry_raw = float(entry_row["open"])
    entry_price = _adverse_price(
        entry_raw,
        direction=direction,
        ticks=cfg.entry_slippage_ticks,
        entry=True,
    )
    stop_price = float(normalized["event_stop"])
    raw_through_stop = entry_raw <= stop_price if direction > 0 else entry_raw >= stop_price
    risk_points = entry_price - stop_price if direction > 0 else stop_price - entry_price
    if raw_through_stop or risk_points <= 0:
        return {
            **identity,
            **normalized,
            "status": "BLOCKED",
            "reason": "ENTRY_GAP_THROUGH_STOP",
        }
    if risk_points <= float(EXECUTION_TICK):
        return {
            **identity,
            **normalized,
            "status": "BLOCKED",
            "reason": "EXECUTED_RISK_TOO_SMALL",
        }
    target_price = entry_price + direction * risk_points * float(TARGET_RR)

    def finish(
        *,
        reason: str,
        exit_time: pd.Timestamp,
        exit_raw: float,
        exit_price: float,
        collision: bool = False,
        gap_minutes: int = 0,
    ) -> dict[str, object]:
        gross_points = direction * (exit_price - entry_price)
        gross_r = gross_points / risk_points
        commission_dollars = 2.0 * cfg.commission_per_side
        commission_r = commission_dollars / (risk_points * cfg.point_value)
        return {
            **identity,
            **normalized,
            "status": "EXITED",
            "reason": reason,
            "entry_timestamp": entry_time.isoformat(),
            "entry_price_raw": entry_raw,
            "entry_price": entry_price,
            "stop_price": stop_price,
            "target_price": target_price,
            "exit_timestamp": exit_time.isoformat(),
            "exit_price_raw": exit_raw,
            "exit_price": exit_price,
            "gross_points": gross_points,
            "gross_r": gross_r,
            "commission_dollars": commission_dollars,
            "commission_r": commission_r,
            "net_r": gross_r - commission_r,
            "holding_minutes": int((exit_time - entry_time).total_seconds() // 60),
            "collision": collision,
            "gap_minutes": gap_minutes,
        }

    def market_exit(
        *,
        reason: str,
        exit_time: pd.Timestamp,
        exit_raw: float,
        slippage_ticks: float,
        gap_minutes: int = 0,
    ) -> dict[str, object]:
        exit_price = _adverse_price(
            exit_raw,
            direction=direction,
            ticks=slippage_ticks,
            entry=False,
        )
        return finish(
            reason=reason,
            exit_time=exit_time,
            exit_raw=exit_raw,
            exit_price=exit_price,
            gap_minutes=gap_minutes,
        )

    expected = pd.date_range(entry_time, window_end, freq="1min", inclusive="left")
    inactive_run = 0
    stale_unsafe = False
    for timestamp in expected:
        row = bars.get(pd.Timestamp(timestamp))
        if row is None:
            future = [
                (time, bar)
                for time, bar in bars.items()
                if time > timestamp
                and time <= window_end
                and int(bar["is_active_quote"]) > 0
            ]
            next_pair = min(future, key=lambda item: item[0]) if future else None
            if stale_unsafe:
                if next_pair is None:
                    return {
                        **identity,
                        **normalized,
                        "status": "UNRESOLVED",
                        "reason": "UNRESOLVED_STALE_EXIT",
                    }
                next_time, next_bar = next_pair
                missing = int((next_time - timestamp).total_seconds() // 60)
                return market_exit(
                    reason="STALE_ACTIVITY_LIQUIDATION",
                    exit_time=next_time,
                    exit_raw=float(next_bar["open"]),
                    slippage_ticks=cfg.market_exit_slippage_ticks,
                    gap_minutes=inactive_run + missing,
                )
            if next_pair is None:
                return {
                    **identity,
                    **normalized,
                    "status": "UNRESOLVED",
                    "reason": "UNRESOLVED_DATA_EXIT",
                }
            next_time, next_bar = next_pair
            return market_exit(
                reason="DATA_GAP_LIQUIDATION",
                exit_time=next_time,
                exit_raw=float(next_bar["open"]),
                slippage_ticks=cfg.market_exit_slippage_ticks,
                gap_minutes=int((next_time - timestamp).total_seconds() // 60),
            )
        if int(row["is_active_quote"]) <= 0:
            inactive_run += 1
            stale_unsafe = inactive_run > cfg.maximum_consecutive_inactive_minutes
            continue
        if stale_unsafe:
            return market_exit(
                reason="STALE_ACTIVITY_LIQUIDATION",
                exit_time=pd.Timestamp(timestamp),
                exit_raw=float(row["open"]),
                slippage_ticks=cfg.market_exit_slippage_ticks,
                gap_minutes=inactive_run,
            )
        inactive_run = 0
        open_ = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        if direction > 0:
            stop_gap = open_ <= stop_price
            target_gap = open_ >= target_price
            stop_hit = low <= stop_price
            target_hit = high >= target_price
        else:
            stop_gap = open_ >= stop_price
            target_gap = open_ <= target_price
            stop_hit = high >= stop_price
            target_hit = low <= target_price
        if timestamp != entry_time and stop_gap:
            return market_exit(
                reason="STOP_GAP",
                exit_time=pd.Timestamp(timestamp),
                exit_raw=open_,
                slippage_ticks=cfg.stop_slippage_ticks,
            )
        if timestamp != entry_time and target_gap:
            return finish(
                reason="TARGET_GAP",
                exit_time=pd.Timestamp(timestamp),
                exit_raw=target_price,
                exit_price=target_price,
            )
        if stop_hit:
            stop_fill = _adverse_price(
                stop_price,
                direction=direction,
                ticks=cfg.stop_slippage_ticks,
                entry=False,
            )
            return finish(
                reason="STOP",
                exit_time=pd.Timestamp(timestamp),
                exit_raw=stop_price,
                exit_price=stop_fill,
                collision=bool(target_hit),
            )
        if target_hit:
            return finish(
                reason="TARGET",
                exit_time=pd.Timestamp(timestamp),
                exit_raw=target_price,
                exit_price=target_price,
            )
    time_row = bars.get(window_end)
    if stale_unsafe:
        if time_row is not None and int(time_row["is_active_quote"]) > 0:
            return market_exit(
                reason="STALE_ACTIVITY_LIQUIDATION",
                exit_time=window_end,
                exit_raw=float(time_row["open"]),
                slippage_ticks=cfg.market_exit_slippage_ticks,
                gap_minutes=inactive_run,
            )
        return {
            **identity,
            **normalized,
            "status": "UNRESOLVED",
            "reason": "UNRESOLVED_STALE_EXIT",
        }
    if time_row is None or int(time_row["is_active_quote"]) <= 0:
        return {
            **identity,
            **normalized,
            "status": "UNRESOLVED",
            "reason": "UNRESOLVED_TIME_EXIT",
        }
    return market_exit(
        reason="TIME_EXIT",
        exit_time=window_end,
        exit_raw=float(time_row["open"]),
        slippage_ticks=cfg.market_exit_slippage_ticks,
    )
