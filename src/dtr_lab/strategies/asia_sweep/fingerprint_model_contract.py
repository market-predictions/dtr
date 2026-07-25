from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import OneHotEncoder

RANDOM_SEED = 20260725
YEARS = tuple(range(2015, 2022))
PAIRS = ("EURUSD", "GBPUSD")
TARGET = "midpoint_success_09_10"
T0_CATEGORICAL_FEATURES = (
    "instrument",
    "side",
    "weekday",
    "week_of_month",
    "sweep_half_hour",
    "asian_compression_bucket",
    "sweep_consumption_class",
)
T0_NUMERIC_FEATURES = (
    "sweep_minute",
    "sweep_before_0900",
    "asian_range_pips",
    "asian_range_atr20",
    "asian_range_adr20",
    "asian_range_vs_median20",
    "asian_range_percentile20",
    "asian_range_percentile60",
    "asian_range_zscore60",
    "asian_range_under_20_pip_flag",
    "asian_range_20_30_pip_flag",
    "asian_range_over_30_pip_flag",
    "asian_close_location",
    "asian_return_range_fraction",
    "asian_realized_vol_range_fraction",
    "asian_high_formation_minute",
    "asian_low_formation_minute",
    "asian_high_zone_touches",
    "asian_low_zone_touches",
    "asian_direction_changes",
    "asian_first_half_range_fraction",
    "asian_second_half_range_fraction",
    "pre_sweep_return_range_fraction",
    "pre_sweep_reversal_signed_return",
    "pre_sweep_realized_vol_range_fraction",
    "pre_sweep_boundary_tests",
    "pre_sweep_minutes_from_0800",
    "pre_sweep_trailing_15m_range_fraction",
    "sweep_depth_pips",
    "sweep_depth_range_fraction",
    "sweep_body_range_fraction",
    "sweep_wick_range_fraction",
    "sweep_close_beyond_boundary_fraction",
    "sweep_close_location_in_bar",
    "sweep_displacement_vs_trailing_vol",
    "prior_day_return_atr20",
    "same_side_level_count",
    "same_side_source_diversity",
    "nearest_same_side_distance_atr",
    "second_same_side_distance_atr",
    "third_same_side_distance_atr",
    "same_side_levels_within_0_05_atr",
    "same_side_levels_within_0_10_atr",
    "same_side_levels_within_0_20_atr",
    "same_side_levels_within_0_25_range",
    "same_side_source_families_within_0_10_atr",
    "same_side_weighted_density",
    "stack_present",
    "stack_member_count",
    "stack_source_diversity",
    "stack_centroid_distance_atr",
    "stack_span_atr",
    "stack_contains_equal_cluster",
    "levels_consumed_before_sweep",
    "levels_consumed_by_sweep",
    "stack_fraction_consumed_t0",
    "full_stack_exhausted_t0",
    "remaining_levels_beyond_t0",
    "nearest_remaining_distance_atr_t0",
    "residual_density_t0",
    "sweep_stops_inside_stack",
    "opposite_level_count",
    "opposite_source_diversity",
    "nearest_opposite_distance_atr",
    "midpoint_before_nearest_opposite",
    "other_pair_swept_before_t0",
    "other_pair_minutes_since_sweep_t0",
    "other_pair_same_side_t0",
    "other_pair_sweep_depth_t0",
    "other_pair_same_side_within_5m",
    "other_pair_opposite_side_within_15m",
)
T5_INCREMENTAL_FEATURES = (
    "t5_closes_outside",
    "t5_closes_inside",
    "t5_reclaim",
    "t5_reclaim_delay_minutes",
    "t5_reclaim_depth_range_fraction",
    "t5_return_range_fraction",
    "t5_mfe_range_fraction",
    "t5_mae_range_fraction",
    "t5_extreme_extension_range_fraction",
    "t5_retest_touch",
    "t5_retest_hold",
    "t5_reversal_swing_break",
    "levels_consumed_through_t5",
    "stack_fraction_consumed_t5",
    "full_stack_exhausted_t5",
    "remaining_levels_beyond_t5",
    "nearest_remaining_distance_atr_t5",
    "residual_density_t5",
    "other_pair_reclaim_known_t5",
    "other_pair_t5_reclaim",
    "other_pair_t5_return",
    "other_pair_t5_retest_hold",
    "other_pair_t5_reversal_swing_break",
)
INTERACTIONS_T0 = (
    ("asian_range_atr20", "sweep_depth_range_fraction"),
    ("asian_range_atr20", "sweep_minute"),
    ("asian_range_atr20", "pre_sweep_realized_vol_range_fraction"),
    ("asian_range_atr20", "same_side_weighted_density"),
    ("asian_range_atr20", "residual_density_t0"),
)
INTERACTIONS_T5 = INTERACTIONS_T0 + (
    ("asian_range_atr20", "t5_reclaim_depth_range_fraction"),
)
PROHIBITED_MODEL_COLUMNS = {
    "event_id",
    "trade_date",
    "week_key",
    "sweep_timestamp_utc",
    "sweep_timestamp_amsterdam",
    "t5_timestamp_utc",
    "midpoint_success_09_10",
    "primary_outcome",
    "midpoint_first_passage_utc",
    "barrier_first_passage_utc",
    "reaction_first_passage_utc",
    "opposite_first_passage_utc",
    "return_5m_range_fraction",
    "mfe_5m_range_fraction",
    "mae_5m_range_fraction",
    "return_15m_range_fraction",
    "mfe_15m_range_fraction",
    "mae_15m_range_fraction",
    "return_30m_range_fraction",
    "mfe_30m_range_fraction",
    "mae_30m_range_fraction",
    "return_60m_range_fraction",
    "mfe_60m_range_fraction",
    "mae_60m_range_fraction",
    "close_1000_range_fraction",
    "close_1100_range_fraction",
    "early_midpoint",
    "reaction_25",
    "full_range_success",
    "late_midpoint",
    "immediate_continuation",
    "false_reversal",
    "stalled_reaction",
    "two_sided_ambiguous",
}
LOGISTIC_GRID = tuple(
    {"alpha": alpha, "l1_ratio": l1}
    for alpha, l1 in itertools.product(
        (0.00001, 0.00003, 0.0001, 0.0003, 0.001),
        (0.25, 0.5, 0.75, 1.0),
    )
)
HGB_GRID = (
    {
        "learning_rate": learning_rate,
        "max_leaf_nodes": max_leaf_nodes,
        "min_samples_leaf": 50,
        "l2_regularization": 5.0,
    }
    for learning_rate, max_leaf_nodes in itertools.product((0.04, 0.08), (7, 15))
)
HGB_GRID = tuple(HGB_GRID)


@dataclass(frozen=True)
class PreprocessorState:
    numeric_features: tuple[str, ...]
    categorical_features: tuple[str, ...]
    medians: dict[str, float]
    centers: dict[str, float]
    scales: dict[str, float]
    missing_indicator_features: tuple[str, ...]
    categorical_modes: dict[str, str]
    encoder: OneHotEncoder
    interactions: tuple[tuple[str, str], ...]
    feature_names: tuple[str, ...]


@dataclass(frozen=True)
class CandidateSummary:
    landmark: str
    family: str
    base_rate: float
    pr_auc: float
    pr_auc_relative_lift: float
    roc_auc: float
    brier: float
    baseline_brier: float
    calibration_intercept: float
    calibration_slope: float
    top_quintile_rate: float
    top_quintile_lift: float
    bottom_quintile_rate: float
    hit_at_1: float
    naive_hit_at_1: float
    hit_at_1_relative_lift: float
    pair_positive_top_lift_count: int
    year_positive_top_lift_count: int
    eligible: bool
    failed_predicates: tuple[str, ...]


def _parse_timestamps(events: pd.DataFrame) -> pd.DataFrame:
    result = events.copy()
    for column in (
        "sweep_timestamp_utc",
        "t5_timestamp_utc",
        "midpoint_first_passage_utc",
        "barrier_first_passage_utc",
        "reaction_first_passage_utc",
        "opposite_first_passage_utc",
    ):
        values = result[column] if column in result else pd.Series(pd.NaT, index=result.index)
        result[column] = pd.to_datetime(values, utc=True, errors="coerce")
    result["trade_date"] = pd.to_datetime(result["trade_date"], errors="raise").dt.date.astype(str)
    result["year"] = pd.to_datetime(result["trade_date"]).dt.year.astype(int)
    return result


def validate_development_events(events: pd.DataFrame) -> None:
    required = {
        "event_id",
        "instrument",
        "trade_date",
        "week_key",
        "sweep_timestamp_utc",
        "t5_timestamp_utc",
        TARGET,
    }
    missing = sorted(required - set(events.columns))
    if missing:
        raise ValueError(f"missing required development columns: {missing}")
    pairs = tuple(sorted(events["instrument"].unique()))
    if pairs != PAIRS:
        raise ValueError(f"expected exactly {PAIRS}, found {pairs}")
    years = tuple(sorted(pd.to_datetime(events["trade_date"]).dt.year.unique()))
    if years != YEARS:
        raise ValueError(f"expected development years {YEARS}, found {years}")
    if events["event_id"].duplicated().any():
        raise ValueError("event_id must be globally unique")
    if events[TARGET].isna().any():
        raise ValueError("target contains missing values")


def _optional_bool_float(value: Any) -> float:
    if pd.isna(value):
        return float("nan")
    return float(bool(value))


def add_cross_pair_features(events: pd.DataFrame) -> pd.DataFrame:
    """Add only opposite-pair information known by each event's T0/T5 timestamp."""
    result = _parse_timestamps(events).sort_values(
        ["trade_date", "sweep_timestamp_utc", "instrument", "event_id"]
    ).reset_index(drop=True)
    defaults: dict[str, Any] = {
        "other_pair_swept_before_t0": 0.0,
        "other_pair_minutes_since_sweep_t0": np.nan,
        "other_pair_same_side_t0": np.nan,
        "other_pair_sweep_depth_t0": np.nan,
        "other_pair_same_side_within_5m": 0.0,
        "other_pair_opposite_side_within_15m": 0.0,
        "other_pair_reclaim_known_t5": 0.0,
        "other_pair_t5_reclaim": np.nan,
        "other_pair_t5_return": np.nan,
        "other_pair_t5_retest_hold": np.nan,
        "other_pair_t5_reversal_swing_break": np.nan,
    }
    for column, value in defaults.items():
        result[column] = value

    for _, indices in result.groupby("trade_date", sort=False).groups.items():
        day = result.loc[list(indices)].sort_values("sweep_timestamp_utc")
        for index, row in day.iterrows():
            other = day.loc[day["instrument"] != row["instrument"]]
            observed = other.loc[other["sweep_timestamp_utc"] <= row["sweep_timestamp_utc"]]
            if not observed.empty:
                latest = observed.iloc[-1]
                minutes = (
                    row["sweep_timestamp_utc"] - latest["sweep_timestamp_utc"]
                ).total_seconds() / 60.0
                result.at[index, "other_pair_swept_before_t0"] = 1.0
                result.at[index, "other_pair_minutes_since_sweep_t0"] = minutes
                result.at[index, "other_pair_same_side_t0"] = float(
                    latest["side"] == row["side"]
                )
                result.at[index, "other_pair_sweep_depth_t0"] = latest[
                    "sweep_depth_range_fraction"
                ]
                if 0.0 <= minutes <= 5.0 and latest["side"] == row["side"]:
                    result.at[index, "other_pair_same_side_within_5m"] = 1.0
                if 0.0 <= minutes <= 15.0 and latest["side"] != row["side"]:
                    result.at[index, "other_pair_opposite_side_within_15m"] = 1.0

            if pd.notna(row["t5_timestamp_utc"]):
                t5_observed = other.loc[
                    other["t5_available"].astype(bool)
                    & other["t5_timestamp_utc"].notna()
                    & (other["t5_timestamp_utc"] <= row["t5_timestamp_utc"])
                ].sort_values("t5_timestamp_utc")
                if not t5_observed.empty:
                    latest_t5 = t5_observed.iloc[-1]
                    result.at[index, "other_pair_reclaim_known_t5"] = 1.0
                    result.at[index, "other_pair_t5_reclaim"] = _optional_bool_float(
                        latest_t5["t5_reclaim"]
                    )
                    result.at[index, "other_pair_t5_return"] = latest_t5[
                        "t5_return_range_fraction"
                    ]
                    result.at[index, "other_pair_t5_retest_hold"] = _optional_bool_float(
                        latest_t5["t5_retest_hold"]
                    )
                    result.at[index, "other_pair_t5_reversal_swing_break"] = (
                        _optional_bool_float(latest_t5["t5_reversal_swing_break"])
                    )
    return result.sort_values("event_id").reset_index(drop=True)


def _occurred_by(event_time: pd.Series, decision_time: pd.Series) -> pd.Series:
    return event_time.notna() & decision_time.notna() & (event_time <= decision_time)


def build_population(
    events: pd.DataFrame,
    landmark: Literal["T0", "T5"],
) -> pd.DataFrame:
    result = add_cross_pair_features(events)
    result["target"] = result[TARGET].astype(int)
    if landmark == "T0":
        return result.reset_index(drop=True)
    if landmark != "T5":
        raise ValueError(f"unsupported landmark: {landmark}")
    resolved = (
        _occurred_by(result["midpoint_first_passage_utc"], result["t5_timestamp_utc"])
        | _occurred_by(result["barrier_first_passage_utc"], result["t5_timestamp_utc"])
        | _occurred_by(result["opposite_first_passage_utc"], result["t5_timestamp_utc"])
    )
    return result.loc[result["t5_available"].astype(bool) & ~resolved].reset_index(drop=True)


def feature_spec(
    landmark: Literal["T0", "T5"],
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[tuple[str, str], ...]]:
    if landmark == "T0":
        numeric = T0_NUMERIC_FEATURES
        interactions = INTERACTIONS_T0
    elif landmark == "T5":
        numeric = T0_NUMERIC_FEATURES + T5_INCREMENTAL_FEATURES
        interactions = INTERACTIONS_T5
    else:
        raise ValueError(landmark)
    all_features = set(numeric) | set(T0_CATEGORICAL_FEATURES)
    overlap = sorted(all_features & PROHIBITED_MODEL_COLUMNS)
    if overlap:
        raise AssertionError(f"outcome leakage in feature spec: {overlap}")
    return numeric, T0_CATEGORICAL_FEATURES, interactions


def fit_preprocessor(
    frame: pd.DataFrame,
    numeric_features: tuple[str, ...],
    categorical_features: tuple[str, ...],
    interactions: tuple[tuple[str, str], ...],
) -> PreprocessorState:
    absent = sorted((set(numeric_features) | set(categorical_features)) - set(frame.columns))
    if absent:
        raise ValueError(f"missing model feature columns: {absent}")
    numeric = frame.loc[:, numeric_features].apply(pd.to_numeric, errors="coerce").astype(float)
    numeric = numeric.replace([np.inf, -np.inf], np.nan)
    medians = numeric.median().fillna(0.0).to_dict()
    filled = numeric.fillna(medians)
    centers = filled.median().to_dict()
    q75 = filled.quantile(0.75)
    q25 = filled.quantile(0.25)
    scale_series = (q75 - q25).where((q75 - q25).abs() > 1e-12, 1.0)
    scales = scale_series.to_dict()
    missing_indicators = tuple(
        column for column in numeric_features if numeric[column].isna().any()
    )

    categorical = frame.loc[:, categorical_features].copy()
    modes: dict[str, str] = {}
    for column in categorical_features:
        values = categorical[column].dropna().astype(str)
        modes[column] = values.mode().iloc[0] if not values.empty else "__MISSING__"
        categorical[column] = categorical[column].astype("string").fillna(modes[column])
    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False, dtype=np.float64)
    encoder.fit(categorical)

    numeric_names = list(numeric_features)
    missing_names = [f"{column}__missing" for column in missing_indicators]
    categorical_names = encoder.get_feature_names_out(categorical_features).tolist()
    interaction_names = [f"{left}__x__{right}" for left, right in interactions]
    names = tuple(numeric_names + missing_names + categorical_names + interaction_names)
    return PreprocessorState(
        numeric_features=numeric_features,
        categorical_features=categorical_features,
        medians={key: float(value) for key, value in medians.items()},
        centers={key: float(value) for key, value in centers.items()},
        scales={key: float(value) for key, value in scales.items()},
        missing_indicator_features=missing_indicators,
        categorical_modes=modes,
        encoder=encoder,
        interactions=interactions,
        feature_names=names,
    )


def transform_preprocessor(frame: pd.DataFrame, state: PreprocessorState) -> np.ndarray:
    numeric_raw = (
        frame.loc[:, state.numeric_features]
        .apply(pd.to_numeric, errors="coerce")
        .astype(float)
    )
    numeric_raw = numeric_raw.replace([np.inf, -np.inf], np.nan)
    missing = (
        numeric_raw.loc[:, state.missing_indicator_features].isna().astype(float).to_numpy()
        if state.missing_indicator_features
        else np.empty((len(frame), 0), dtype=float)
    )
    filled = numeric_raw.fillna(state.medians)
    scaled = pd.DataFrame(index=frame.index)
    for column in state.numeric_features:
        scaled[column] = (filled[column] - state.centers[column]) / state.scales[column]

    categorical = frame.loc[:, state.categorical_features].copy()
    for column in state.categorical_features:
        categorical[column] = categorical[column].astype("string").fillna(
            state.categorical_modes[column]
        )
    encoded = state.encoder.transform(categorical)
    interaction_values = np.column_stack(
        [scaled[left].to_numpy() * scaled[right].to_numpy() for left, right in state.interactions]
    ) if state.interactions else np.empty((len(frame), 0), dtype=float)
    return np.column_stack([scaled.to_numpy(dtype=float), missing, encoded, interaction_values])


def _model(family: Literal["elastic_net", "hgb"], params: dict[str, Any]):
    if family == "elastic_net":
        return SGDClassifier(
            loss="log_loss",
            penalty="elasticnet",
            average=True,
            class_weight=None,
            fit_intercept=True,
            max_iter=3000,
            tol=1e-4,
            shuffle=True,
            random_state=RANDOM_SEED,
            **params,
        )
    if family == "hgb":
        return HistGradientBoostingClassifier(
            loss="log_loss",
            early_stopping=False,
            max_iter=120,
            random_state=RANDOM_SEED,
            **params,
        )
    raise ValueError(family)


def _parameter_grid(family: Literal["elastic_net", "hgb"]):
    return LOGISTIC_GRID if family == "elastic_net" else HGB_GRID
