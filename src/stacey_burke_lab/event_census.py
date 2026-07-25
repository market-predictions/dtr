from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from stacey_burke_lab.fx_source import instrument, source_filename, write_json

NEW_YORK_TZ = "America/New_York"
LONDON_TZ = "Europe/London"


@dataclass(frozen=True)
class EventCensusDefinition:
    london_start_minute: int = 7 * 60
    london_end_minute: int = 10 * 60
    excursion_atr_fraction: float = 0.05
    reclaim_minutes: int = 15
    minimum_active_minutes: int = 171
    expected_session_minutes: int = 180
    atr_days: int = 20

    def validate(self) -> None:
        if not 0 <= self.london_start_minute < self.london_end_minute <= 24 * 60:
            raise ValueError("invalid London session bounds")
        if self.excursion_atr_fraction <= 0:
            raise ValueError("excursion_atr_fraction must be positive")
        if self.reclaim_minutes < 0:
            raise ValueError("reclaim_minutes must be non-negative")
        if not 0 < self.minimum_active_minutes <= self.expected_session_minutes:
            raise ValueError("invalid session coverage requirement")
        if self.atr_days < 2:
            raise ValueError("atr_days must be at least 2")


DEFAULT_DEFINITION = EventCensusDefinition()

EVENT_COLUMNS = (
    "event_id",
    "symbol",
    "factor_block",
    "trading_date",
    "london_date",
    "swept_side",
    "reversal_direction",
    "previous_day_high",
    "previous_day_low",
    "atr20",
    "excursion_threshold",
    "first_sweep_timestamp_utc",
    "reclaim_timestamp_utc",
    "reclaim_delay_minutes",
    "sweep_extreme",
    "excursion_price",
    "excursion_pips",
    "excursion_atr",
    "reclaim_close",
    "reclaim_distance_inside",
    "same_minute_reclaim",
    "active_minutes",
    "active_coverage_fraction",
    "source_partitions",
)

SESSION_BOOLEAN_COLUMNS = (
    "eligible",
    "high_swept",
    "high_reclaimed",
    "low_swept",
    "low_reclaimed",
    "ambiguous",
    "retained_event",
)


def _load_side(path: Path, *, suffix: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    frame = pd.read_csv(
        path,
        compression="gzip",
        usecols=(
            "timestamp_utc",
            "open",
            "high",
            "low",
            "close",
            "is_active_quote",
        ),
        dtype={"is_active_quote": "int8"},
    )
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="raise")
    rename = {
        column: f"{column}_{suffix}"
        for column in ("open", "high", "low", "close", "is_active_quote")
    }
    return frame.rename(columns=rename)


def load_midpoint_source(
    *,
    directory: Path,
    symbol: str,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    if end_year < start_year:
        raise ValueError("end_year must be greater than or equal to start_year")
    instrument(symbol)
    partitions: list[pd.DataFrame] = []
    for year in range(start_year, end_year + 1):
        label = str(year)
        bid = _load_side(
            directory / source_filename(symbol, "bid", label),
            suffix="bid",
        )
        ask = _load_side(
            directory / source_filename(symbol, "ask", label),
            suffix="ask",
        )
        merged = bid.merge(
            ask,
            on="timestamp_utc",
            how="inner",
            validate="one_to_one",
        )
        merged["source_partition"] = label
        partitions.append(merged)
    if not partitions:
        raise ValueError("no source partitions requested")
    frame = pd.concat(partitions, ignore_index=True)
    frame = frame.sort_values("timestamp_utc", kind="mergesort").reset_index(drop=True)
    if frame["timestamp_utc"].duplicated().any():
        raise ValueError("duplicate timestamps across source partitions")
    for column in ("open", "high", "low", "close"):
        frame[f"mid_{column}"] = (
            frame[f"{column}_bid"].astype("float64")
            + frame[f"{column}_ask"].astype("float64")
        ) / 2.0
    frame["active_both"] = (
        (frame["is_active_quote_bid"] == 1)
        & (frame["is_active_quote_ask"] == 1)
    )
    return frame.loc[
        :,
        [
            "timestamp_utc",
            "mid_open",
            "mid_high",
            "mid_low",
            "mid_close",
            "active_both",
            "source_partition",
        ],
    ]


def _assign_market_clocks(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    ny = result["timestamp_utc"].dt.tz_convert(NEW_YORK_TZ)
    ny_naive = ny.dt.tz_localize(None)
    after_close = (ny.dt.hour >= 17).astype("int8")
    result["trading_date"] = (
        ny_naive.dt.normalize() + pd.to_timedelta(after_close, unit="D")
    )

    london = result["timestamp_utc"].dt.tz_convert(LONDON_TZ)
    london_naive = london.dt.tz_localize(None)
    result["london_date"] = london_naive.dt.normalize()
    result["london_minute"] = london.dt.hour * 60 + london.dt.minute
    return result


def build_completed_day_references(
    frame: pd.DataFrame,
    *,
    atr_days: int,
) -> pd.DataFrame:
    if atr_days < 2:
        raise ValueError("atr_days must be at least 2")
    clocks = _assign_market_clocks(frame)
    active = clocks.loc[clocks["active_both"]].copy()
    if active.empty:
        raise ValueError("no synchronized active rows")

    grouped = active.groupby("trading_date", sort=True, observed=True)
    daily = grouped.agg(
        day_high=("mid_high", "max"),
        day_low=("mid_low", "min"),
        day_close=("mid_close", "last"),
        day_active_rows=("timestamp_utc", "size"),
    )
    previous_close = daily["day_close"].shift(1)
    daily["true_range"] = pd.concat(
        [
            daily["day_high"] - daily["day_low"],
            (daily["day_high"] - previous_close).abs(),
            (daily["day_low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    references = pd.DataFrame(index=daily.index)
    references["previous_day_high"] = daily["day_high"].shift(1)
    references["previous_day_low"] = daily["day_low"].shift(1)
    references["previous_day_close"] = daily["day_close"].shift(1)
    references["atr20"] = (
        daily["true_range"].rolling(atr_days, min_periods=atr_days).mean().shift(1)
    )
    references["previous_day_active_rows"] = daily["day_active_rows"].shift(1)
    return references


def _first_reclaim(
    session: pd.DataFrame,
    *,
    side: str,
    level: float,
    threshold: float,
    reclaim_minutes: int,
) -> dict[str, Any] | None:
    active = session.loc[session["active_both"]].copy()
    if side == "high":
        sweep_mask = active["mid_high"] >= level + threshold
    elif side == "low":
        sweep_mask = active["mid_low"] <= level - threshold
    else:
        raise ValueError(f"unsupported side: {side}")
    candidates = active.loc[sweep_mask]
    if candidates.empty:
        return None

    sweep = candidates.iloc[0]
    sweep_timestamp = sweep["timestamp_utc"]
    reclaim_deadline = sweep_timestamp + pd.Timedelta(minutes=reclaim_minutes)
    reclaim_window = active.loc[
        (active["timestamp_utc"] >= sweep_timestamp)
        & (active["timestamp_utc"] <= reclaim_deadline)
    ]
    if side == "high":
        reclaim_rows = reclaim_window.loc[reclaim_window["mid_close"] <= level]
        sweep_extreme = float(sweep["mid_high"])
        excursion = sweep_extreme - level
    else:
        reclaim_rows = reclaim_window.loc[reclaim_window["mid_close"] >= level]
        sweep_extreme = float(sweep["mid_low"])
        excursion = level - sweep_extreme
    if reclaim_rows.empty:
        return {
            "swept": True,
            "reclaimed": False,
            "sweep_timestamp": sweep_timestamp,
            "sweep_extreme": sweep_extreme,
            "excursion": float(excursion),
        }

    reclaim = reclaim_rows.iloc[0]
    reclaim_timestamp = reclaim["timestamp_utc"]
    delay = int((reclaim_timestamp - sweep_timestamp) / pd.Timedelta(minutes=1))
    return {
        "swept": True,
        "reclaimed": True,
        "sweep_timestamp": sweep_timestamp,
        "reclaim_timestamp": reclaim_timestamp,
        "reclaim_delay_minutes": delay,
        "sweep_extreme": sweep_extreme,
        "excursion": float(excursion),
        "reclaim_close": float(reclaim["mid_close"]),
        "same_minute_reclaim": delay == 0,
    }


def _candidate_status(candidate: dict[str, Any] | None) -> tuple[bool, bool]:
    if candidate is None:
        return False, False
    return bool(candidate["swept"]), bool(candidate.get("reclaimed", False))


def detect_pair_event_census(
    *,
    frame: pd.DataFrame,
    symbol: str,
    definition: EventCensusDefinition = DEFAULT_DEFINITION,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    definition.validate()
    item = instrument(symbol)
    clocks = _assign_market_clocks(frame)
    references = build_completed_day_references(clocks, atr_days=definition.atr_days)
    sessions = clocks.loc[
        (clocks["london_minute"] >= definition.london_start_minute)
        & (clocks["london_minute"] < definition.london_end_minute)
    ].copy()

    event_rows: list[dict[str, Any]] = []
    session_rows: list[dict[str, Any]] = []

    for london_date, session in sessions.groupby("london_date", sort=True, observed=True):
        session = session.sort_values("timestamp_utc", kind="mergesort")
        trading_dates = session["trading_date"].drop_duplicates()
        if len(trading_dates) != 1:
            session_rows.append(
                {
                    "symbol": item.symbol,
                    "factor_block": item.factor_block,
                    "london_date": london_date.date().isoformat(),
                    "eligible": False,
                    "exclusion_reason": "multiple_fx_trading_dates",
                    "synchronized_minutes": int(len(session)),
                    "active_minutes": int(session["active_both"].sum()),
                }
            )
            continue

        trading_date = trading_dates.iloc[0]
        active_minutes = int(session["active_both"].sum())
        base_session = {
            "symbol": item.symbol,
            "factor_block": item.factor_block,
            "london_date": london_date.date().isoformat(),
            "trading_date": trading_date.date().isoformat(),
            "synchronized_minutes": int(len(session)),
            "active_minutes": active_minutes,
            "active_coverage_fraction": active_minutes / definition.expected_session_minutes,
        }

        if trading_date not in references.index:
            session_rows.append(
                {
                    **base_session,
                    "eligible": False,
                    "exclusion_reason": "missing_reference_date",
                }
            )
            continue

        reference = references.loc[trading_date]
        previous_high = float(reference["previous_day_high"])
        previous_low = float(reference["previous_day_low"])
        atr20 = float(reference["atr20"])
        if (
            active_minutes < definition.minimum_active_minutes
            or not np.isfinite(previous_high)
            or not np.isfinite(previous_low)
            or not np.isfinite(atr20)
            or atr20 <= 0
            or previous_high <= previous_low
        ):
            reasons: list[str] = []
            if active_minutes < definition.minimum_active_minutes:
                reasons.append("insufficient_active_minutes")
            if not np.isfinite(previous_high) or not np.isfinite(previous_low):
                reasons.append("missing_previous_day_levels")
            if not np.isfinite(atr20) or atr20 <= 0:
                reasons.append("missing_or_invalid_atr20")
            if (
                np.isfinite(previous_high)
                and np.isfinite(previous_low)
                and previous_high <= previous_low
            ):
                reasons.append("invalid_previous_day_range")
            session_rows.append(
                {
                    **base_session,
                    "eligible": False,
                    "exclusion_reason": "|".join(reasons),
                }
            )
            continue

        threshold = definition.excursion_atr_fraction * atr20
        high_candidate = _first_reclaim(
            session,
            side="high",
            level=previous_high,
            threshold=threshold,
            reclaim_minutes=definition.reclaim_minutes,
        )
        low_candidate = _first_reclaim(
            session,
            side="low",
            level=previous_low,
            threshold=threshold,
            reclaim_minutes=definition.reclaim_minutes,
        )
        high_swept, high_reclaimed = _candidate_status(high_candidate)
        low_swept, low_reclaimed = _candidate_status(low_candidate)

        retained: tuple[str, dict[str, Any]] | None = None
        ambiguous = False
        reclaiming: list[tuple[str, dict[str, Any]]] = []
        if high_reclaimed and high_candidate is not None:
            reclaiming.append(("high", high_candidate))
        if low_reclaimed and low_candidate is not None:
            reclaiming.append(("low", low_candidate))
        if reclaiming:
            reclaiming.sort(key=lambda value: value[1]["reclaim_timestamp"])
            if (
                len(reclaiming) == 2
                and reclaiming[0][1]["reclaim_timestamp"]
                == reclaiming[1][1]["reclaim_timestamp"]
            ):
                ambiguous = True
            else:
                retained = reclaiming[0]

        session_record = {
            **base_session,
            "eligible": True,
            "exclusion_reason": "ambiguous_same_reclaim_timestamp" if ambiguous else "",
            "previous_day_high": previous_high,
            "previous_day_low": previous_low,
            "atr20": atr20,
            "excursion_threshold": threshold,
            "high_swept": high_swept,
            "high_reclaimed": high_reclaimed,
            "low_swept": low_swept,
            "low_reclaimed": low_reclaimed,
            "ambiguous": ambiguous,
            "retained_event": retained is not None,
        }

        if retained is not None:
            side, candidate = retained
            level = previous_high if side == "high" else previous_low
            direction = "short_reversal" if side == "high" else "long_reversal"
            reclaim_distance = (
                level - candidate["reclaim_close"]
                if side == "high"
                else candidate["reclaim_close"] - level
            )
            event_id = (
                f"{item.symbol}-{trading_date.date().isoformat()}-"
                f"{side}-{candidate['reclaim_timestamp'].isoformat()}"
            )
            source_partitions = ",".join(
                sorted(session["source_partition"].astype(str).unique())
            )
            event_rows.append(
                {
                    "event_id": event_id,
                    "symbol": item.symbol,
                    "factor_block": item.factor_block,
                    "trading_date": trading_date.date().isoformat(),
                    "london_date": london_date.date().isoformat(),
                    "swept_side": side,
                    "reversal_direction": direction,
                    "previous_day_high": previous_high,
                    "previous_day_low": previous_low,
                    "atr20": atr20,
                    "excursion_threshold": threshold,
                    "first_sweep_timestamp_utc": candidate["sweep_timestamp"].isoformat(),
                    "reclaim_timestamp_utc": candidate["reclaim_timestamp"].isoformat(),
                    "reclaim_delay_minutes": candidate["reclaim_delay_minutes"],
                    "sweep_extreme": candidate["sweep_extreme"],
                    "excursion_price": candidate["excursion"],
                    "excursion_pips": candidate["excursion"] / item.pip_size,
                    "excursion_atr": candidate["excursion"] / atr20,
                    "reclaim_close": candidate["reclaim_close"],
                    "reclaim_distance_inside": reclaim_distance,
                    "same_minute_reclaim": candidate["same_minute_reclaim"],
                    "active_minutes": active_minutes,
                    "active_coverage_fraction": base_session["active_coverage_fraction"],
                    "source_partitions": source_partitions,
                }
            )
            session_record["retained_event_id"] = event_id
        else:
            session_record["retained_event_id"] = ""

        session_rows.append(session_record)

    events = pd.DataFrame(event_rows, columns=EVENT_COLUMNS)
    session_audit = pd.DataFrame(session_rows)
    for column in SESSION_BOOLEAN_COLUMNS:
        if column not in session_audit:
            session_audit[column] = False
        else:
            session_audit[column] = session_audit[column].eq(True)
    eligible = (
        session_audit.loc[session_audit["eligible"]]
        if not session_audit.empty
        else session_audit
    )
    summary: dict[str, Any] = {
        "programme": "stacey_burke_conditional_sweep_reclaim_census_v1",
        "symbol": item.symbol,
        "factor_block": item.factor_block,
        "definition": asdict(definition),
        "performance_execution": False,
        "forward_returns_inspected": False,
        "sessions_total": int(len(session_audit)),
        "sessions_eligible": int(session_audit["eligible"].sum())
        if not session_audit.empty
        else 0,
        "sessions_ineligible": int((~session_audit["eligible"]).sum())
        if not session_audit.empty
        else 0,
        "sessions_ambiguous": int(eligible["ambiguous"].sum())
        if not eligible.empty
        else 0,
        "sessions_with_high_sweep": int(eligible["high_swept"].sum())
        if not eligible.empty
        else 0,
        "sessions_with_high_reclaim": int(eligible["high_reclaimed"].sum())
        if not eligible.empty
        else 0,
        "sessions_with_low_sweep": int(eligible["low_swept"].sum())
        if not eligible.empty
        else 0,
        "sessions_with_low_reclaim": int(eligible["low_reclaimed"].sum())
        if not eligible.empty
        else 0,
        "retained_events": int(len(events)),
        "same_minute_reclaims": int(events["same_minute_reclaim"].sum())
        if not events.empty
        else 0,
        "high_events": int((events["swept_side"] == "high").sum())
        if not events.empty
        else 0,
        "low_events": int((events["swept_side"] == "low").sum())
        if not events.empty
        else 0,
    }
    return events, session_audit, summary


def run_pair_census(
    *,
    directory: Path,
    symbol: str,
    start_year: int,
    end_year: int,
    output_directory: Path,
    definition: EventCensusDefinition = DEFAULT_DEFINITION,
) -> dict[str, Any]:
    frame = load_midpoint_source(
        directory=directory,
        symbol=symbol,
        start_year=start_year,
        end_year=end_year,
    )
    events, sessions, summary = detect_pair_event_census(
        frame=frame,
        symbol=symbol,
        definition=definition,
    )
    output_directory.mkdir(parents=True, exist_ok=True)
    normalized = symbol.upper()
    events.to_csv(
        output_directory / f"{normalized}_event_census.csv",
        index=False,
    )
    sessions.to_csv(
        output_directory / f"{normalized}_session_census.csv",
        index=False,
    )
    write_json(
        summary,
        output_directory / f"{normalized}_event_census_summary.json",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run the preregistered Stacey Burke event census without forward returns "
            "or strategy execution"
        )
    )
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2021)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    summary = run_pair_census(
        directory=args.data,
        symbol=args.symbol,
        start_year=args.start_year,
        end_year=args.end_year,
        output_directory=args.out,
    )
    print(
        f"{summary['symbol']}: {summary['retained_events']} retained events "
        f"from {summary['sessions_eligible']} eligible sessions"
    )


if __name__ == "__main__":
    main()
