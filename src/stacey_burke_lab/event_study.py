from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from stacey_burke_lab.event_census import (
    DEFAULT_DEFINITION,
    _assign_market_clocks,
    detect_pair_event_census,
    load_midpoint_source,
)
from stacey_burke_lab.fx_source import instrument, write_json

FROZEN_DISCOVERY_CENSUS_COUNTS = {
    "EURUSD": 277,
    "GBPUSD": 294,
    "USDCHF": 313,
    "AUDUSD": 215,
    "NZDUSD": 177,
    "USDCAD": 162,
    "USDJPY": 173,
    "EURJPY": 252,
    "GBPJPY": 254,
    "EURGBP": 306,
}
FROZEN_DISCOVERY_LEDGER_SHA256 = (
    "862ec9c28f6e8450b59f6a34da2571a4a3c25075013f11492be8cfc946653533"
)


@dataclass(frozen=True)
class ControlledStudyDefinition:
    forward_minutes: int = 60
    pre_return_minutes: int = 15
    realized_vol_minutes: int = 60
    controls_per_event: int = 5
    london_bucket_minutes: int = 15

    def validate(self) -> None:
        if self.forward_minutes <= 0:
            raise ValueError("forward_minutes must be positive")
        if self.pre_return_minutes <= 0:
            raise ValueError("pre_return_minutes must be positive")
        if self.realized_vol_minutes <= 1:
            raise ValueError("realized_vol_minutes must exceed one minute")
        if self.controls_per_event <= 0:
            raise ValueError("controls_per_event must be positive")
        if self.london_bucket_minutes <= 0 or 60 % self.london_bucket_minutes:
            raise ValueError("london_bucket_minutes must divide one hour")


DEFAULT_STUDY_DEFINITION = ControlledStudyDefinition()


def _exact_values(series: pd.Series, timestamps: pd.DatetimeIndex) -> np.ndarray:
    return series.reindex(timestamps).to_numpy(dtype="float64")


def _build_observations(
    *,
    frame: pd.DataFrame,
    sessions: pd.DataFrame,
    definition: ControlledStudyDefinition,
) -> pd.DataFrame:
    definition.validate()
    work = _assign_market_clocks(frame).sort_values("timestamp_utc", kind="mergesort")
    if work["timestamp_utc"].duplicated().any():
        raise ValueError("duplicate timestamps in midpoint source")

    index = pd.DatetimeIndex(work["timestamp_utc"])
    active_close = pd.Series(
        np.where(work["active_both"], work["mid_close"], np.nan),
        index=index,
        dtype="float64",
    )
    previous_close = _exact_values(active_close, index - pd.Timedelta(minutes=1))
    current_close = active_close.to_numpy(dtype="float64")
    log_return_1m = np.full(len(work), np.nan, dtype="float64")
    valid_return = (
        np.isfinite(current_close)
        & np.isfinite(previous_close)
        & (current_close > 0)
        & (previous_close > 0)
    )
    log_return_1m[valid_return] = np.log(
        current_close[valid_return] / previous_close[valid_return]
    )
    realized_vol = (
        pd.Series(log_return_1m**2, index=index)
        .rolling(
            f"{definition.realized_vol_minutes}min",
            min_periods=definition.realized_vol_minutes,
        )
        .sum()
        .pow(0.5)
        .to_numpy(dtype="float64")
    )
    lag_close = _exact_values(
        active_close,
        index - pd.Timedelta(minutes=definition.pre_return_minutes),
    )
    pre_return = np.full(len(work), np.nan, dtype="float64")
    valid_pre = (
        np.isfinite(current_close)
        & np.isfinite(lag_close)
        & (current_close > 0)
        & (lag_close > 0)
    )
    pre_return[valid_pre] = np.log(current_close[valid_pre] / lag_close[valid_pre])
    forward_close = _exact_values(
        active_close,
        index + pd.Timedelta(minutes=definition.forward_minutes),
    )

    observations = work.loc[
        :,
        [
            "timestamp_utc",
            "mid_close",
            "active_both",
            "london_date",
            "london_minute",
            "source_partition",
        ],
    ].copy()
    observations["pre_return_15m"] = pre_return
    observations["realized_vol_60m"] = realized_vol
    observations["forward_close_60m"] = forward_close
    observations["london_date_key"] = observations["london_date"].dt.date.astype(str)
    observations["year"] = observations["london_date"].dt.year.astype("int16")
    observations["weekday"] = observations["london_date"].dt.weekday.astype("int8")
    observations["london_bucket"] = (
        observations["london_minute"] // definition.london_bucket_minutes
    ).astype("int16")

    session_columns = [
        "london_date",
        "eligible",
        "ambiguous",
        "retained_event",
        "atr20",
    ]
    session_map = sessions.loc[:, session_columns].copy()
    session_map["london_date_key"] = session_map["london_date"].astype(str)
    session_map = session_map.drop(columns="london_date")
    observations = observations.merge(
        session_map,
        on="london_date_key",
        how="left",
        validate="many_to_one",
    )
    for column in ("eligible", "ambiguous", "retained_event"):
        observations[column] = observations[column].eq(True)
    return observations


def _event_observations(
    *,
    events: pd.DataFrame,
    observations: pd.DataFrame,
    analysis_start_year: int,
    analysis_end_year: int,
    definition: ControlledStudyDefinition,
) -> tuple[pd.DataFrame, dict[str, int]]:
    selected = events.loc[
        events["london_date"].astype(str).str[:4].astype(int).between(
            analysis_start_year,
            analysis_end_year,
        )
    ].copy()
    selected["reclaim_timestamp"] = pd.to_datetime(
        selected["reclaim_timestamp_utc"],
        utc=True,
        errors="raise",
    )
    observation_columns = [
        "timestamp_utc",
        "mid_close",
        "pre_return_15m",
        "realized_vol_60m",
        "forward_close_60m",
        "year",
        "weekday",
        "london_bucket",
        "london_date_key",
    ]
    selected = selected.merge(
        observations.loc[:, observation_columns],
        left_on="reclaim_timestamp",
        right_on="timestamp_utc",
        how="left",
        validate="one_to_one",
    )
    source_close_error = (
        selected["mid_close"] - selected["reclaim_close"].astype(float)
    ).abs()
    if bool((source_close_error > 1e-10).fillna(False).any()):
        raise RuntimeError("event reclaim close does not match midpoint source")

    selected["direction_sign"] = np.where(
        selected["reversal_direction"] == "long_reversal",
        1.0,
        -1.0,
    )
    selected["event_outcome_atr"] = selected["direction_sign"] * (
        selected["forward_close_60m"] - selected["mid_close"]
    ) / selected["atr20"].astype(float)
    selected["observable"] = (
        np.isfinite(selected["pre_return_15m"])
        & np.isfinite(selected["realized_vol_60m"])
        & np.isfinite(selected["event_outcome_atr"])
        & (selected["atr20"].astype(float) > 0)
    )
    counts = {
        "census_events": int(len(selected)),
        "unobservable_events": int((~selected["observable"]).sum()),
        "observable_events": int(selected["observable"].sum()),
    }
    return selected.loc[selected["observable"]].copy(), counts


def _control_candidates(
    observations: pd.DataFrame,
    *,
    analysis_start_year: int,
    analysis_end_year: int,
) -> pd.DataFrame:
    candidates = observations.loc[
        observations["year"].between(analysis_start_year, analysis_end_year)
        & observations["eligible"]
        & ~observations["ambiguous"]
        & ~observations["retained_event"]
        & observations["active_both"]
        & observations["london_minute"].between(420, 599)
        & np.isfinite(observations["pre_return_15m"])
        & np.isfinite(observations["realized_vol_60m"])
        & np.isfinite(observations["forward_close_60m"])
        & np.isfinite(observations["atr20"])
        & (observations["atr20"] > 0)
    ].copy()
    candidates["raw_forward_change"] = (
        candidates["forward_close_60m"] - candidates["mid_close"]
    )
    return candidates


def _nearest_distinct_date_controls(
    *,
    event: pd.Series,
    candidates: pd.DataFrame,
    definition: ControlledStudyDefinition,
) -> pd.DataFrame:
    stratum = candidates.loc[
        (candidates["year"] == int(event["year"]))
        & (candidates["weekday"] == int(event["weekday"]))
        & (candidates["london_bucket"] == int(event["london_bucket"]))
        & (candidates["london_date_key"] != str(event["london_date_key"]))
    ].copy()
    if stratum.empty:
        return stratum

    feature_columns = ("pre_return_15m", "realized_vol_60m")
    scales = stratum.loc[:, feature_columns].std(ddof=0).to_numpy(dtype="float64")
    scales = np.where(np.isfinite(scales) & (scales > 1e-12), scales, 1.0)
    event_features = event.loc[list(feature_columns)].to_numpy(dtype="float64")
    candidate_features = stratum.loc[:, feature_columns].to_numpy(dtype="float64")
    stratum["match_distance"] = np.sqrt(
        np.square((candidate_features - event_features) / scales).sum(axis=1)
    )
    stratum = stratum.sort_values(
        ["match_distance", "timestamp_utc"],
        kind="mergesort",
    )
    stratum = stratum.drop_duplicates("london_date_key", keep="first")
    return stratum.head(definition.controls_per_event).copy()


def match_pair_events(
    *,
    events: pd.DataFrame,
    candidates: pd.DataFrame,
    symbol: str,
    definition: ControlledStudyDefinition = DEFAULT_STUDY_DEFINITION,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    definition.validate()
    matched_rows: list[dict[str, Any]] = []
    control_rows: list[dict[str, Any]] = []
    unmatched = 0

    for _, event in events.sort_values("reclaim_timestamp", kind="mergesort").iterrows():
        controls = _nearest_distinct_date_controls(
            event=event,
            candidates=candidates,
            definition=definition,
        )
        if len(controls) < definition.controls_per_event:
            unmatched += 1
            continue
        controls = controls.copy()
        controls["control_outcome_atr"] = float(event["direction_sign"]) * (
            controls["raw_forward_change"] / controls["atr20"].astype(float)
        )
        if not np.isfinite(controls["control_outcome_atr"]).all():
            unmatched += 1
            continue

        control_mean = float(controls["control_outcome_atr"].mean())
        effect = float(event["event_outcome_atr"]) - control_mean
        matched_rows.append(
            {
                "event_id": event["event_id"],
                "symbol": symbol,
                "factor_block": event["factor_block"],
                "london_date": event["london_date_key"],
                "reclaim_timestamp_utc": event["reclaim_timestamp"].isoformat(),
                "reversal_direction": event["reversal_direction"],
                "swept_side": event["swept_side"],
                "atr20": float(event["atr20"]),
                "pre_return_15m": float(event["pre_return_15m"]),
                "realized_vol_60m": float(event["realized_vol_60m"]),
                "event_outcome_atr": float(event["event_outcome_atr"]),
                "control_mean_outcome_atr": control_mean,
                "effect_atr": effect,
                "maximum_match_distance": float(controls["match_distance"].max()),
                "mean_match_distance": float(controls["match_distance"].mean()),
                "controls": definition.controls_per_event,
            }
        )
        for rank, (_, control) in enumerate(controls.iterrows(), start=1):
            control_rows.append(
                {
                    "event_id": event["event_id"],
                    "symbol": symbol,
                    "factor_block": event["factor_block"],
                    "event_london_date": event["london_date_key"],
                    "control_rank": rank,
                    "control_timestamp_utc": control["timestamp_utc"].isoformat(),
                    "control_london_date": control["london_date_key"],
                    "year": int(control["year"]),
                    "weekday": int(control["weekday"]),
                    "london_bucket": int(control["london_bucket"]),
                    "pre_return_15m": float(control["pre_return_15m"]),
                    "realized_vol_60m": float(control["realized_vol_60m"]),
                    "control_atr20": float(control["atr20"]),
                    "control_outcome_atr": float(control["control_outcome_atr"]),
                    "match_distance": float(control["match_distance"]),
                }
            )

    matched = pd.DataFrame(matched_rows)
    controls = pd.DataFrame(control_rows)
    summary: dict[str, Any] = {
        "programme": "stacey_burke_controlled_event_study_v1",
        "symbol": symbol,
        "factor_block": instrument(symbol).factor_block,
        "definition": asdict(definition),
        "performance_execution": False,
        "strategy_pnl_calculated": False,
        "events_observable": int(len(events)),
        "events_matched": int(len(matched)),
        "events_unmatched": int(unmatched),
        "controls": int(len(controls)),
        "mean_event_outcome_atr": (
            float(matched["event_outcome_atr"].mean()) if not matched.empty else None
        ),
        "mean_control_outcome_atr": (
            float(matched["control_mean_outcome_atr"].mean()) if not matched.empty else None
        ),
        "mean_effect_atr": float(matched["effect_atr"].mean()) if not matched.empty else None,
    }
    return matched, controls, summary


def run_pair_controlled_study(
    *,
    directory: Path,
    symbol: str,
    load_start_year: int,
    load_end_year: int,
    analysis_start_year: int,
    analysis_end_year: int,
    output_directory: Path,
    enforce_frozen_discovery_count: bool,
    definition: ControlledStudyDefinition = DEFAULT_STUDY_DEFINITION,
) -> dict[str, Any]:
    normalized = symbol.upper()
    frame = load_midpoint_source(
        directory=directory,
        symbol=normalized,
        start_year=load_start_year,
        end_year=load_end_year,
    )
    census_events, sessions, census_summary = detect_pair_event_census(
        frame=frame,
        symbol=normalized,
        definition=DEFAULT_DEFINITION,
    )
    selected_census_count = int(
        census_events["london_date"].astype(str).str[:4].astype(int).between(
            analysis_start_year,
            analysis_end_year,
        ).sum()
    )
    if enforce_frozen_discovery_count:
        expected = FROZEN_DISCOVERY_CENSUS_COUNTS[normalized]
        if selected_census_count != expected:
            raise RuntimeError(
                f"{normalized} census drift: expected {expected}, observed {selected_census_count}"
            )

    observations = _build_observations(
        frame=frame,
        sessions=sessions,
        definition=definition,
    )
    observable_events, observability = _event_observations(
        events=census_events,
        observations=observations,
        analysis_start_year=analysis_start_year,
        analysis_end_year=analysis_end_year,
        definition=definition,
    )
    candidates = _control_candidates(
        observations,
        analysis_start_year=analysis_start_year,
        analysis_end_year=analysis_end_year,
    )
    matched, controls, summary = match_pair_events(
        events=observable_events,
        candidates=candidates,
        symbol=normalized,
        definition=definition,
    )
    summary.update(
        {
            "load_start_year": load_start_year,
            "load_end_year": load_end_year,
            "analysis_start_year": analysis_start_year,
            "analysis_end_year": analysis_end_year,
            "frozen_discovery_census_enforced": enforce_frozen_discovery_count,
            "frozen_aggregate_census_ledger_sha256": FROZEN_DISCOVERY_LEDGER_SHA256,
            "census_events_selected": selected_census_count,
            "census_sessions_eligible": int(census_summary["sessions_eligible"]),
            "control_candidate_minutes": int(len(candidates)),
            **observability,
        }
    )

    output_directory.mkdir(parents=True, exist_ok=True)
    matched.to_csv(
        output_directory / f"{normalized}_controlled_event_study_events.csv",
        index=False,
    )
    controls.to_csv(
        output_directory / f"{normalized}_controlled_event_study_controls.csv",
        index=False,
    )
    write_json(
        summary,
        output_directory / f"{normalized}_controlled_event_study_summary.json",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the frozen Stacey Burke matched-control event study"
    )
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--load-start-year", type=int, required=True)
    parser.add_argument("--load-end-year", type=int, required=True)
    parser.add_argument("--analysis-start-year", type=int, required=True)
    parser.add_argument("--analysis-end-year", type=int, required=True)
    parser.add_argument("--enforce-frozen-discovery-count", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    summary = run_pair_controlled_study(
        directory=args.data,
        symbol=args.symbol,
        load_start_year=args.load_start_year,
        load_end_year=args.load_end_year,
        analysis_start_year=args.analysis_start_year,
        analysis_end_year=args.analysis_end_year,
        output_directory=args.out,
        enforce_frozen_discovery_count=args.enforce_frozen_discovery_count,
    )
    print(
        f"{summary['symbol']}: {summary['events_matched']} matched events, "
        f"mean effect {summary['mean_effect_atr']} ATR"
    )


if __name__ == "__main__":
    main()
