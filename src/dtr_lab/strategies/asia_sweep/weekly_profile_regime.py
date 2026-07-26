from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

AMSTERDAM_TZ = "Europe/Amsterdam"
DEVELOPMENT_YEARS = tuple(range(2015, 2020))
PAIRS = ("EURUSD", "GBPUSD")

H1_TARGETS = (
    "EXT_OPPOSITE_BOUNDARY_1100",
    "EXT_FIXED_2R_1100",
    "EXT_OPPOSING_LIQUIDITY_1400",
    "EXT_FIXED_3R_1200",
    "EXT_FIXED_4R_1400",
)
H2_TARGETS = (
    "EXT_FIXED_2R_1100",
    "EXT_OPPOSITE_BOUNDARY_1100",
    "EXT_FIXED_3R_1200",
    "EXT_OPPOSING_LIQUIDITY_1400",
    "EXT_FIXED_4R_1400",
)


@dataclass(frozen=True)
class MechanismGate:
    min_events: int
    min_positives: int
    min_pair_events: int
    min_absolute_lift: float
    min_relative_lift: float


GATES = {
    "H1_HTF_TREND_RESUMPTION": MechanismGate(150, 30, 50, 0.05, 1.25),
    "H2_WEEKLY_RETRACE_CONTINUATION": MechanismGate(120, 25, 40, 0.04, 1.20),
}


def prepare_midpoint_minutes(bars: pd.DataFrame) -> pd.DataFrame:
    required = {
        "open_bid",
        "high_bid",
        "low_bid",
        "close_bid",
        "open_ask",
        "high_ask",
        "low_ask",
        "close_ask",
        "active",
    }
    missing = sorted(required - set(bars.columns))
    if missing:
        raise ValueError(f"missing BID/ASK minute columns: {missing}")
    if not isinstance(bars.index, pd.DatetimeIndex):
        raise TypeError("BID/ASK minute index must be a DatetimeIndex")
    if bars.index.tz is None:
        raise ValueError("BID/ASK minute index must be timezone aware")
    out = pd.DataFrame(index=bars.index)
    for field in ("open", "high", "low", "close"):
        out[f"{field}_mid"] = 0.5 * (
            pd.to_numeric(bars[f"{field}_bid"], errors="raise")
            + pd.to_numeric(bars[f"{field}_ask"], errors="raise")
        )
    out["active"] = bars["active"].astype(bool)
    return out.sort_index()


def build_daily_context(minutes: pd.DataFrame) -> pd.DataFrame:
    required = {"open_mid", "high_mid", "low_mid", "close_mid", "active"}
    missing = sorted(required - set(minutes.columns))
    if missing:
        raise ValueError(f"missing midpoint minute columns: {missing}")
    active = minutes.loc[minutes["active"].astype(bool)].copy()
    local_index = active.index.tz_convert(AMSTERDAM_TZ)
    active["trade_date"] = local_index.date
    daily = active.groupby("trade_date", sort=True).agg(
        open=("open_mid", "first"),
        high=("high_mid", "max"),
        low=("low_mid", "min"),
        close=("close_mid", "last"),
        active_minutes=("close_mid", "size"),
    )
    daily = daily.loc[daily["active_minutes"] >= 1200].copy()
    previous_close = daily["close"].shift(1)
    daily["true_range"] = np.maximum.reduce(
        [
            (daily["high"] - daily["low"]).to_numpy(float),
            (daily["high"] - previous_close).abs().to_numpy(float),
            (daily["low"] - previous_close).abs().to_numpy(float),
        ]
    )
    daily["atr20"] = daily["true_range"].rolling(20, min_periods=20).mean().shift(1)
    daily["sma20"] = daily["close"].rolling(20, min_periods=20).mean().shift(1)
    daily["d20_return_atr"] = (
        daily["close"].shift(1) - daily["close"].shift(21)
    ) / daily["atr20"]
    daily["close_vs_sma20_atr"] = (
        daily["close"].shift(1) - daily["sma20"]
    ) / daily["atr20"]
    daily["sma20_slope_5d_atr"] = (
        daily["sma20"] - daily["sma20"].shift(5)
    ) / (5.0 * daily["atr20"])
    path20 = daily["close"].diff().abs().rolling(20, min_periods=20).sum().shift(1)
    daily["efficiency20"] = (
        (daily["close"].shift(1) - daily["close"].shift(21)).abs() / path20
    )

    dates = pd.to_datetime(pd.Index(daily.index))
    week_start = dates - pd.to_timedelta(dates.weekday, unit="D")
    weekly_source = daily.assign(week_start=week_start.to_numpy())
    weekly = weekly_source.groupby("week_start", sort=True).agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
    )
    weekly["return"] = weekly["close"] - weekly["open"]
    weekly["close_location"] = (weekly["close"] - weekly["low"]) / (
        weekly["high"] - weekly["low"]
    ).replace(0.0, np.nan)
    prior_week = weekly[["return", "close_location"]].shift(1)
    prior_return = prior_week["return"].to_dict()
    prior_location = prior_week["close_location"].to_dict()
    daily["week_start"] = week_start.to_numpy()
    daily["prior_week_return"] = daily["week_start"].map(prior_return)
    daily["prior_week_close_location"] = daily["week_start"].map(prior_location)
    daily["prior_week_return_atr"] = daily["prior_week_return"] / daily["atr20"]

    trend = daily.apply(_structural_trend_from_row, axis=1, result_type="expand")
    trend.columns = [
        "structural_trend",
        "structural_trend_strength",
        "structural_trend_score",
    ]
    return pd.concat([daily, trend], axis=1)


def _structural_trend_from_row(row: pd.Series) -> tuple[str, str, int]:
    values = (
        row.get("d20_return_atr"),
        row.get("close_vs_sma20_atr"),
        row.get("sma20_slope_5d_atr"),
    )
    if any(not np.isfinite(value) for value in values):
        return "NEUTRAL", "WARMUP", 0
    score = 0
    score += 1 if values[0] > 0.50 else -1 if values[0] < -0.50 else 0
    score += 1 if values[1] > 0.25 else -1 if values[1] < -0.25 else 0
    score += 1 if values[2] > 0.01 else -1 if values[2] < -0.01 else 0
    direction = "UP" if score >= 2 else "DOWN" if score <= -2 else "NEUTRAL"
    if direction == "NEUTRAL":
        return direction, "NEUTRAL", score
    strong = (
        abs(float(values[0])) >= 1.50
        and np.isfinite(row.get("efficiency20"))
        and float(row["efficiency20"]) >= 0.35
    )
    return direction, "STRONG" if strong else "MODERATE", score


def classify_weekly_phase(
    *,
    structural_trend: str,
    weekday: int,
    current_week_direction: str,
    countertrend_excursion_atr: float,
    withtrend_excursion_atr: float,
    recovery_from_countertrend_extreme_atr: float,
) -> str:
    if structural_trend == "NEUTRAL":
        return "WEEKLY_ROTATION"
    counter_direction = "DOWN" if structural_trend == "UP" else "UP"
    if (
        weekday <= 1
        and current_week_direction == counter_direction
        and countertrend_excursion_atr >= 0.20
    ):
        return "EARLY_WEEK_COUNTERTREND_RETRACE"
    if (
        weekday <= 2
        and withtrend_excursion_atr >= 0.35
        and countertrend_excursion_atr < 0.20
    ):
        return "EARLY_WEEK_TREND_EXTENSION"
    if (
        weekday <= 2
        and countertrend_excursion_atr >= 0.35
        and recovery_from_countertrend_extreme_atr >= 0.20
    ):
        return "MIDWEEK_TREND_RESUMPTION"
    if (
        weekday >= 2
        and countertrend_excursion_atr >= 0.75
        and current_week_direction == counter_direction
    ):
        return "MIDWEEK_REVERSAL_OR_TRANSITION"
    if (
        weekday >= 3
        and max(countertrend_excursion_atr, withtrend_excursion_atr) >= 0.75
    ):
        return "LATE_WEEK_EXPANSION"
    return "WEEKLY_ROTATION"


def classify_trade_role(
    *,
    structural_trend: str,
    trade_direction: str,
    weekday: int,
    current_week_direction: str,
    countertrend_excursion_atr: float,
    withtrend_excursion_atr: float,
) -> str:
    if structural_trend == "NEUTRAL":
        return "ROTATION_OR_AMBIGUOUS"
    aligns = trade_direction == structural_trend
    opposes = trade_direction != structural_trend
    counter_direction = "DOWN" if structural_trend == "UP" else "UP"
    if (
        weekday <= 2
        and aligns
        and countertrend_excursion_atr >= 0.35
        and withtrend_excursion_atr < 0.75
    ):
        return "HTF_TREND_RESUMPTION"
    if (
        weekday <= 1
        and opposes
        and current_week_direction == counter_direction
        and countertrend_excursion_atr >= 0.20
        and withtrend_excursion_atr < 0.50
    ):
        return "WEEKLY_RETRACE_CONTINUATION"
    if (
        weekday <= 2
        and aligns
        and withtrend_excursion_atr >= 0.35
        and countertrend_excursion_atr < 0.20
    ):
        return "EARLY_WEEK_TREND_EXTENSION"
    if opposes and withtrend_excursion_atr >= 0.75:
        return "EXHAUSTION_REVERSAL"
    if aligns and (withtrend_excursion_atr >= 0.75 or weekday >= 3):
        return "MATURE_TREND_EXTENSION"
    return "ROTATION_OR_AMBIGUOUS"


def _safe_ratio(numerator: float, denominator: float) -> float:
    if not np.isfinite(numerator) or not np.isfinite(denominator) or denominator <= 0.0:
        return math.nan
    return float(numerator / denominator)


def _event_context(
    minutes: pd.DataFrame,
    daily: pd.DataFrame,
    *,
    entry_time: pd.Timestamp,
    side: str,
) -> dict[str, Any]:
    local_time = entry_time.tz_convert(AMSTERDAM_TZ)
    trade_date = local_time.date()
    if trade_date not in daily.index:
        raise ValueError(f"missing daily context for {trade_date}")
    day = daily.loc[trade_date]
    atr = float(day["atr20"])
    structural = str(day["structural_trend"])
    week_start_local = local_time.normalize() - pd.Timedelta(days=local_time.weekday())
    week_start_utc = week_start_local.tz_convert("UTC")
    path = minutes.loc[week_start_utc:entry_time]
    path = path.loc[(path.index < entry_time) & path["active"].astype(bool)]
    if path.empty or not np.isfinite(atr) or atr <= 0.0:
        raise ValueError(f"insufficient causal weekly context for {entry_time.isoformat()}")

    week_open = float(path.iloc[0]["open_mid"])
    current = float(path.iloc[-1]["close_mid"])
    week_high = float(path["high_mid"].max())
    week_low = float(path["low_mid"].min())
    price_vs_open = (current - week_open) / atr
    current_direction = (
        "UP"
        if price_vs_open >= 0.15
        else "DOWN"
        if price_vs_open <= -0.15
        else "FLAT"
    )

    if structural == "UP":
        withtrend = max(0.0, (week_high - week_open) / atr)
        countertrend = max(0.0, (week_open - week_low) / atr)
        recovery = max(0.0, (current - week_low) / atr)
    elif structural == "DOWN":
        withtrend = max(0.0, (week_open - week_low) / atr)
        countertrend = max(0.0, (week_high - week_open) / atr)
        recovery = max(0.0, (week_high - current) / atr)
    else:
        withtrend = math.nan
        countertrend = math.nan
        recovery = math.nan

    local_path_index = path.index.tz_convert(AMSTERDAM_TZ)
    monday_mask = np.asarray(local_path_index.date) == week_start_local.date()
    monday = path.loc[monday_mask]
    monday_high = float(monday["high_mid"].max()) if len(monday) else math.nan
    monday_low = float(monday["low_mid"].min()) if len(monday) else math.nan
    trade_direction = "UP" if side == "DOWN" else "DOWN"
    weekday = int(local_time.weekday())
    phase = classify_weekly_phase(
        structural_trend=structural,
        weekday=weekday,
        current_week_direction=current_direction,
        countertrend_excursion_atr=countertrend,
        withtrend_excursion_atr=withtrend,
        recovery_from_countertrend_extreme_atr=recovery,
    )
    role = classify_trade_role(
        structural_trend=structural,
        trade_direction=trade_direction,
        weekday=weekday,
        current_week_direction=current_direction,
        countertrend_excursion_atr=countertrend,
        withtrend_excursion_atr=withtrend,
    )
    prior_week_return_atr = float(day["prior_week_return_atr"])
    retracement_fraction = _safe_ratio(countertrend, abs(prior_week_return_atr))
    return {
        "event_weekday": weekday,
        "structural_trend": structural,
        "structural_trend_strength": str(day["structural_trend_strength"]),
        "structural_trend_score": int(day["structural_trend_score"]),
        "d20_return_atr": float(day["d20_return_atr"]),
        "close_vs_sma20_atr": float(day["close_vs_sma20_atr"]),
        "sma20_slope_5d_atr": float(day["sma20_slope_5d_atr"]),
        "efficiency20": float(day["efficiency20"]),
        "daily_atr20": atr,
        "prior_week_return_atr": prior_week_return_atr,
        "prior_week_close_location": float(day["prior_week_close_location"]),
        "trade_direction": trade_direction,
        "trade_aligns_structural": bool(
            trade_direction == structural and structural != "NEUTRAL"
        ),
        "trade_opposes_structural": bool(
            trade_direction != structural and structural != "NEUTRAL"
        ),
        "week_open": week_open,
        "current_price_before_entry": current,
        "current_week_high": week_high,
        "current_week_low": week_low,
        "current_week_direction": current_direction,
        "price_vs_week_open_atr": price_vs_open,
        "withtrend_excursion_atr": withtrend,
        "countertrend_excursion_atr": countertrend,
        "recovery_from_countertrend_extreme_atr": recovery,
        "current_week_range_atr": (week_high - week_low) / atr,
        "monday_high": monday_high,
        "monday_low": monday_low,
        "distance_to_monday_high_atr": _safe_ratio(monday_high - current, atr),
        "distance_to_monday_low_atr": _safe_ratio(current - monday_low, atr),
        "countertrend_excursion_fraction_prior_week": retracement_fraction,
        "weekly_phase": phase,
        "trade_role": role,
    }


def enrich_pair_target_ledger(
    targets: pd.DataFrame,
    minutes: pd.DataFrame,
    *,
    symbol: str,
) -> pd.DataFrame:
    required = {
        "event_id",
        "instrument",
        "trade_date",
        "year",
        "side",
        "landmark",
        "entry_timestamp_utc",
        "extended_target",
        "extended_target_hit",
        "extended_reward_risk_stress_010",
    }
    missing = sorted(required - set(targets.columns))
    if missing:
        raise ValueError(f"missing target-ledger columns: {missing}")
    symbol = symbol.upper()
    source = targets.loc[
        targets["instrument"].eq(symbol)
        & targets["landmark"].eq("T0")
        & targets["year"].between(2015, 2019)
    ].copy()
    if source.empty:
        raise ValueError(f"{symbol}: no T0 development target rows")
    source["entry_timestamp_utc"] = pd.to_datetime(
        source["entry_timestamp_utc"], utc=True, errors="raise"
    )
    events = source.drop_duplicates("event_id").loc[
        :, ["event_id", "entry_timestamp_utc", "side"]
    ]
    daily = build_daily_context(minutes)
    rows: list[dict[str, Any]] = []
    for row in events.sort_values("entry_timestamp_utc").itertuples(index=False):
        try:
            context = _event_context(
                minutes,
                daily,
                entry_time=pd.Timestamp(row.entry_timestamp_utc),
                side=str(row.side),
            )
        except ValueError:
            continue
        rows.append({"event_id": str(row.event_id), **context})
    context_frame = pd.DataFrame(rows)
    if context_frame.empty:
        raise ValueError(f"{symbol}: weekly-profile context is empty")
    enriched = source.merge(
        context_frame,
        on="event_id",
        how="inner",
        validate="many_to_one",
    )
    enriched["observed_stressed_ev_proxy"] = (
        enriched["extended_target_hit"].astype(float)
        * enriched["extended_reward_risk_stress_010"].astype(float)
        - (1.0 - enriched["extended_target_hit"].astype(float))
    )
    if enriched.duplicated(["event_id", "extended_target"]).any():
        raise ValueError(f"{symbol}: duplicate event-target rows after T0 enrichment")
    return enriched.sort_values(
        ["extended_target", "entry_timestamp_utc", "event_id"],
        kind="mergesort",
    ).reset_index(drop=True)


def _population_metrics(frame: pd.DataFrame) -> dict[str, float | int]:
    clean = frame.dropna(
        subset=[
            "extended_target_hit",
            "extended_reward_risk_stress_010",
            "observed_stressed_ev_proxy",
        ]
    )
    if clean.empty:
        return {
            "events": 0,
            "positives": 0,
            "hit_rate": math.nan,
            "mean_ev_proxy": math.nan,
            "median_stressed_rr": math.nan,
            "rr_125_breadth": math.nan,
        }
    return {
        "events": int(len(clean)),
        "positives": int(clean["extended_target_hit"].sum()),
        "hit_rate": float(clean["extended_target_hit"].mean()),
        "mean_ev_proxy": float(clean["observed_stressed_ev_proxy"].mean()),
        "median_stressed_rr": float(
            clean["extended_reward_risk_stress_010"].median()
        ),
        "rr_125_breadth": float(
            (clean["extended_reward_risk_stress_010"] >= 1.25).mean()
        ),
    }


def _subgroup_counts_and_metrics(
    subset: pd.DataFrame,
    reference: pd.DataFrame,
    key: str,
    expected: Iterable[Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for value in expected:
        sub = subset.loc[subset[key].eq(value)]
        ref = reference.loc[reference[key].eq(value)]
        sm = _population_metrics(sub)
        rm = _population_metrics(ref)
        lift = (
            float(sm["hit_rate"]) - float(rm["hit_rate"])
            if np.isfinite(sm["hit_rate"]) and np.isfinite(rm["hit_rate"])
            else math.nan
        )
        rows.append(
            {
                key: value,
                **sm,
                "reference_events": rm["events"],
                "reference_hit_rate": rm["hit_rate"],
                "absolute_lift": lift,
            }
        )
    return rows


def evaluate_hypothesis_target(
    ledger: pd.DataFrame,
    *,
    hypothesis: str,
    target: str,
) -> dict[str, Any]:
    frame = ledger.loc[ledger["extended_target"].eq(target)].copy()
    if hypothesis == "H1_HTF_TREND_RESUMPTION":
        subset = frame.loc[frame["trade_role"].eq("HTF_TREND_RESUMPTION")]
        reference = frame.loc[
            frame["structural_trend"].isin(["UP", "DOWN"])
            & frame["event_weekday"].le(2)
            & frame["trade_aligns_structural"].astype(bool)
        ]
    elif hypothesis == "H2_WEEKLY_RETRACE_CONTINUATION":
        subset = frame.loc[
            frame["trade_role"].eq("WEEKLY_RETRACE_CONTINUATION")
        ]
        reference = frame.loc[
            frame["structural_trend"].isin(["UP", "DOWN"])
            & frame["event_weekday"].le(1)
            & frame["trade_opposes_structural"].astype(bool)
        ]
    else:
        raise ValueError(f"unknown hypothesis: {hypothesis}")

    metrics = _population_metrics(subset)
    reference_metrics = _population_metrics(reference)
    hit_rate = float(metrics["hit_rate"])
    reference_rate = float(reference_metrics["hit_rate"])
    absolute_lift = (
        hit_rate - reference_rate
        if np.isfinite(hit_rate) and np.isfinite(reference_rate)
        else math.nan
    )
    relative_lift = (
        hit_rate / reference_rate
        if np.isfinite(hit_rate) and reference_rate > 0.0
        else math.nan
    )
    pair_rows = _subgroup_counts_and_metrics(
        subset,
        reference,
        "instrument",
        PAIRS,
    )
    year_rows = _subgroup_counts_and_metrics(
        subset,
        reference,
        "year",
        DEVELOPMENT_YEARS,
    )

    pair_event_min = min(int(row["events"]) for row in pair_rows)
    pair_ev_positive_count = sum(
        float(row["mean_ev_proxy"]) > 0.0
        for row in pair_rows
        if np.isfinite(row["mean_ev_proxy"])
    )
    pair_lift_positive_count = sum(
        float(row["absolute_lift"]) > 0.0
        for row in pair_rows
        if np.isfinite(row["absolute_lift"])
    )
    year_ev_positive_count = sum(
        float(row["mean_ev_proxy"]) > 0.0
        for row in year_rows
        if np.isfinite(row["mean_ev_proxy"])
    )
    year_lift_positive_count = sum(
        float(row["absolute_lift"]) > 0.0
        for row in year_rows
        if np.isfinite(row["absolute_lift"])
    )
    event_count = int(metrics["events"])
    pair_concentration = (
        max((int(row["events"]) for row in pair_rows), default=0) / event_count
        if event_count
        else math.nan
    )
    year_concentration = (
        max((int(row["events"]) for row in year_rows), default=0) / event_count
        if event_count
        else math.nan
    )

    gate = GATES[hypothesis]
    checks = {
        "sample_events": event_count >= gate.min_events,
        "sample_positives": int(metrics["positives"]) >= gate.min_positives,
        "pair_event_min": pair_event_min >= gate.min_pair_events,
        "absolute_lift": (
            np.isfinite(absolute_lift)
            and absolute_lift >= gate.min_absolute_lift
        ),
        "relative_lift": (
            np.isfinite(relative_lift)
            and relative_lift >= gate.min_relative_lift
        ),
        "pooled_ev": (
            np.isfinite(metrics["mean_ev_proxy"])
            and float(metrics["mean_ev_proxy"]) > 0.0
        ),
        "pair_ev_breadth": pair_ev_positive_count == 2,
        "year_ev_breadth": year_ev_positive_count >= 3,
        "pair_lift_breadth": pair_lift_positive_count == 2,
        "year_lift_breadth": year_lift_positive_count >= 4,
        "median_rr": (
            np.isfinite(metrics["median_stressed_rr"])
            and float(metrics["median_stressed_rr"]) >= 1.25
        ),
        "rr_breadth": (
            np.isfinite(metrics["rr_125_breadth"])
            and float(metrics["rr_125_breadth"]) >= 0.75
        ),
        "pair_concentration": (
            np.isfinite(pair_concentration) and pair_concentration <= 0.70
        ),
        "year_concentration": (
            np.isfinite(year_concentration) and year_concentration <= 0.40
        ),
    }
    failures = [name for name, passed in checks.items() if not passed]
    return {
        "hypothesis": hypothesis,
        "target": target,
        **metrics,
        "reference_events": int(reference_metrics["events"]),
        "reference_hit_rate": reference_rate,
        "absolute_lift": absolute_lift,
        "relative_lift": relative_lift,
        "pair_event_min": pair_event_min,
        "pair_ev_positive_count": pair_ev_positive_count,
        "pair_lift_positive_count": pair_lift_positive_count,
        "year_ev_positive_count": year_ev_positive_count,
        "year_lift_positive_count": year_lift_positive_count,
        "pair_concentration": pair_concentration,
        "year_concentration": year_concentration,
        "passed": not failures,
        "failed_gates": failures,
        "pair_metrics": pair_rows,
        "year_metrics": year_rows,
    }


def aggregate_mechanism_decision(
    ledger: pd.DataFrame,
) -> tuple[dict[str, Any], pd.DataFrame]:
    required = {
        "instrument",
        "year",
        "extended_target",
        "trade_role",
        "structural_trend",
        "event_weekday",
        "trade_aligns_structural",
        "trade_opposes_structural",
        "extended_target_hit",
        "extended_reward_risk_stress_010",
        "observed_stressed_ev_proxy",
    }
    missing = sorted(required - set(ledger.columns))
    if missing:
        raise ValueError(f"missing pooled mechanism columns: {missing}")
    pairs = tuple(sorted(ledger["instrument"].unique()))
    if pairs != PAIRS:
        raise ValueError(f"expected pairs {PAIRS}, found {pairs}")
    years = tuple(sorted(pd.to_numeric(ledger["year"]).astype(int).unique()))
    if years != DEVELOPMENT_YEARS:
        raise ValueError(f"expected years {DEVELOPMENT_YEARS}, found {years}")

    detailed: list[dict[str, Any]] = []
    for hypothesis, targets in (
        ("H1_HTF_TREND_RESUMPTION", H1_TARGETS),
        ("H2_WEEKLY_RETRACE_CONTINUATION", H2_TARGETS),
    ):
        for target in targets:
            detailed.append(
                evaluate_hypothesis_target(
                    ledger,
                    hypothesis=hypothesis,
                    target=target,
                )
            )

    selected = next(
        (
            item
            for item in detailed
            if item["hypothesis"] == "H1_HTF_TREND_RESUMPTION"
            and item["passed"]
        ),
        None,
    )
    if selected is None:
        selected = next(
            (
                item
                for item in detailed
                if item["hypothesis"] == "H2_WEEKLY_RETRACE_CONTINUATION"
                and item["passed"]
            ),
            None,
        )

    decision_code = (
        "PASS_WEEKLY_PROFILE_MECHANISM_OPEN_MODELING"
        if selected is not None
        else "FAIL_WEEKLY_PROFILE_MECHANISM_STOP"
    )
    summary_rows = [
        {
            key: value
            for key, value in item.items()
            if key not in {"pair_metrics", "year_metrics"}
        }
        for item in detailed
    ]
    summary = pd.DataFrame(summary_rows)
    decision = {
        "decision": decision_code,
        "development_years": list(DEVELOPMENT_YEARS),
        "protected_years_opened": False,
        "hypotheses_evaluated": 2,
        "candidate_count": int(len(summary)),
        "selected_hypothesis": selected["hypothesis"] if selected else None,
        "selected_target": selected["target"] if selected else None,
        "selected_metrics": (
            {
                key: value
                for key, value in selected.items()
                if key not in {"pair_metrics", "year_metrics"}
            }
            if selected
            else None
        ),
        "modeling_authorized": bool(selected),
        "position_structure_pnl_opened": False,
        "results": detailed,
    }
    return decision, summary
