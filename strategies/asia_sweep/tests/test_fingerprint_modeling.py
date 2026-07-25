from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import average_precision_score

from dtr_lab.strategies.asia_sweep import fingerprint_model_contract as contract
from dtr_lab.strategies.asia_sweep import fingerprint_model_metrics as metrics
from dtr_lab.strategies.asia_sweep import fingerprint_model_tuning as tuning


def _base_rows() -> pd.DataFrame:
    rows = [
        {
            "event_id": "eur-before",
            "instrument": "EURUSD",
            "trade_date": "2019-01-02",
            "week_key": "2019-W01",
            "side": "UP",
            "sweep_timestamp_utc": "2019-01-02T08:00:00Z",
            "t5_timestamp_utc": "2019-01-02T08:05:00Z",
            "t5_available": True,
            "sweep_depth_range_fraction": 0.10,
            "t5_reclaim": True,
            "t5_return_range_fraction": 0.20,
            "t5_retest_hold": True,
            "t5_reversal_swing_break": True,
            "midpoint_first_passage_utc": None,
            "barrier_first_passage_utc": None,
            "opposite_first_passage_utc": None,
            contract.TARGET: True,
        },
        {
            "event_id": "gbp-after",
            "instrument": "GBPUSD",
            "trade_date": "2019-01-02",
            "week_key": "2019-W01",
            "side": "UP",
            "sweep_timestamp_utc": "2019-01-02T08:03:00Z",
            "t5_timestamp_utc": "2019-01-02T08:08:00Z",
            "t5_available": True,
            "sweep_depth_range_fraction": 0.12,
            "t5_reclaim": False,
            "t5_return_range_fraction": -0.10,
            "t5_retest_hold": False,
            "t5_reversal_swing_break": False,
            "midpoint_first_passage_utc": None,
            "barrier_first_passage_utc": None,
            "opposite_first_passage_utc": None,
            contract.TARGET: False,
        },
    ]
    return pd.DataFrame(rows)


def _complete_feature_frame(count: int = 28) -> pd.DataFrame:
    years = np.resize(np.arange(2015, 2022), count)
    frame = pd.DataFrame(
        {
            "event_id": [f"event-{index:03d}" for index in range(count)],
            "instrument": np.where(np.arange(count) % 2 == 0, "EURUSD", "GBPUSD"),
            "trade_date": [
                f"{year}-01-{index % 20 + 1:02d}" for index, year in enumerate(years)
            ],
            "week_key": [
                f"{year}-W{index % 4 + 1:02d}" for index, year in enumerate(years)
            ],
            "side": np.where(np.arange(count) % 3 == 0, "UP", "DOWN"),
            "weekday": np.arange(count) % 5,
            "week_of_month": np.arange(count) % 4 + 1,
            "sweep_half_hour": np.where(
                np.arange(count) % 2 == 0, "09:00-09:29", "09:30-09:59"
            ),
            "asian_compression_bucket": np.where(
                np.arange(count) % 2 == 0, "LOW_NORMAL", "HIGH_NORMAL"
            ),
            "sweep_consumption_class": np.where(
                np.arange(count) % 2 == 0, "MULTIPLE_LEVELS", "BOUNDARY_ONLY"
            ),
            "sweep_timestamp_utc": [
                f"{year}-01-{index % 20 + 1:02d}T08:{index % 50:02d}:00Z"
                for index, year in enumerate(years)
            ],
            "t5_timestamp_utc": [
                f"{year}-01-{index % 20 + 1:02d}T08:{index % 50 + 5:02d}:00Z"
                for index, year in enumerate(years)
            ],
            "t5_available": True,
            "midpoint_first_passage_utc": None,
            "barrier_first_passage_utc": None,
            "opposite_first_passage_utc": None,
            contract.TARGET: (np.arange(count) % 4 == 0).astype(int),
        }
    )
    for column in set(contract.T0_NUMERIC_FEATURES) | set(
        contract.T5_INCREMENTAL_FEATURES
    ):
        if column not in frame:
            frame[column] = (
                np.linspace(-0.5, 0.5, count) + (np.arange(count) % 3) * 0.01
            )
    for column in (
        "t5_reclaim",
        "t5_retest_hold",
        "t5_reversal_swing_break",
        "sweep_before_0900",
    ):
        frame[column] = (np.arange(count) % 2 == 0).astype(int)
    return frame


def test_t5_landmark_excludes_already_resolved_events() -> None:
    frame = _base_rows()
    frame.loc[0, "midpoint_first_passage_utc"] = "2019-01-02T08:04:00Z"
    population = contract.build_population(frame, "T5")
    assert population["event_id"].tolist() == ["gbp-after"]


def test_cross_pair_features_never_use_future_sweep() -> None:
    result = contract.add_cross_pair_features(_base_rows()).set_index("event_id")
    assert result.loc["eur-before", "other_pair_swept_before_t0"] == 0
    assert result.loc["gbp-after", "other_pair_swept_before_t0"] == 1
    assert result.loc["gbp-after", "other_pair_minutes_since_sweep_t0"] == 3
    assert result.loc["gbp-after", "other_pair_same_side_within_5m"] == 1


def test_feature_contract_contains_no_outcome_columns() -> None:
    for landmark in ("T0", "T5"):
        numeric, categorical, _ = contract.feature_spec(landmark)
        assert not (
            (set(numeric) | set(categorical)) & contract.PROHIBITED_MODEL_COLUMNS
        )


def test_preprocessor_uses_training_median_only() -> None:
    train = _complete_feature_frame(14)
    test = _complete_feature_frame(7)
    train["asian_range_atr20"] = [1.0] * 13 + [100.0]
    test["asian_range_atr20"] = 999.0
    numeric, categorical, interactions = contract.feature_spec("T0")
    state = contract.fit_preprocessor(train, numeric, categorical, interactions)
    assert state.medians["asian_range_atr20"] == 1.0
    transformed = contract.transform_preprocessor(test, state)
    assert transformed.shape[0] == len(test)


def test_weekly_ranking_tie_break_is_deterministic() -> None:
    frame = pd.DataFrame(
        {
            "instrument": ["EURUSD", "EURUSD"],
            "week_key": ["2020-W01", "2020-W01"],
            "prediction": [0.4, 0.4],
            "sweep_timestamp_utc": pd.to_datetime(
                ["2020-01-02T09:05:00Z", "2020-01-02T09:01:00Z"], utc=True
            ),
            "event_id": ["later", "earlier"],
            "target": [1, 0],
            "year": [2020, 2020],
        }
    )
    ranked = metrics.weekly_ranking(frame)
    assert ranked.iloc[0]["selected_event_id"] == "earlier"


def test_population_is_invariant_to_input_row_order() -> None:
    frame = _base_rows()
    first = contract.add_cross_pair_features(frame).sort_values("event_id").reset_index(
        drop=True
    )
    second = (
        contract.add_cross_pair_features(frame.sample(frac=1, random_state=9))
        .sort_values("event_id")
        .reset_index(drop=True)
    )
    columns = [
        "event_id",
        "other_pair_swept_before_t0",
        "other_pair_minutes_since_sweep_t0",
        "other_pair_same_side_t0",
    ]
    pd.testing.assert_frame_equal(first[columns], second[columns])


def test_sgd_fit_is_deterministic_and_probabilistic() -> None:
    frame = contract.build_population(_complete_feature_frame(70), "T0")
    train = frame.loc[frame["year"] != 2021]
    test = frame.loc[frame["year"] == 2021]
    params = {"alpha": 0.0001, "l1_ratio": 0.5}
    _, _, first = tuning._fit_predict(train, test, "T0", "elastic_net", params)
    _, _, second = tuning._fit_predict(train, test, "T0", "elastic_net", params)
    np.testing.assert_allclose(first, second, atol=0, rtol=0)
    assert np.isfinite(first).all()
    assert ((first >= 0) & (first <= 1)).all()


def test_shuffled_labels_destroy_synthetic_signal() -> None:
    frame = contract.build_population(_complete_feature_frame(140), "T0")
    frame["asian_range_atr20"] = np.linspace(-2.0, 2.0, len(frame))
    frame["target"] = (frame["asian_range_atr20"] > 0.5).astype(int)
    predictions = []
    shuffled_predictions = []
    rng = np.random.default_rng(20260725)
    for year in contract.YEARS:
        train = frame.loc[frame["year"] != year].copy()
        test = frame.loc[frame["year"] == year].copy()
        params = {"alpha": 0.0001, "l1_ratio": 0.5}
        _, _, prediction = tuning._fit_predict(
            train, test, "T0", "elastic_net", params
        )
        predictions.extend(prediction)
        shuffled = train.copy()
        shuffled["target"] = rng.permutation(shuffled["target"].to_numpy())
        _, _, shuffled_prediction = tuning._fit_predict(
            shuffled, test, "T0", "elastic_net", params
        )
        shuffled_predictions.extend(shuffled_prediction)
    target = frame.sort_values("year")["target"].to_numpy()
    ordered_target = np.concatenate(
        [
            frame.loc[frame["year"] == year, "target"].to_numpy()
            for year in contract.YEARS
        ]
    )
    assert len(target) == len(ordered_target)
    signal_ap = average_precision_score(ordered_target, predictions)
    shuffled_ap = average_precision_score(ordered_target, shuffled_predictions)
    assert signal_ap > shuffled_ap + 0.20


def test_development_validator_rejects_future_years() -> None:
    frame = _complete_feature_frame(14)
    frame.loc[0, "trade_date"] = "2022-01-03"
    with pytest.raises(ValueError, match="development years"):
        contract.validate_development_events(frame)


def test_frozen_optimizer_grids() -> None:
    assert len(contract.LOGISTIC_GRID) == 20
    assert {row["alpha"] for row in contract.LOGISTIC_GRID} == {
        0.00001,
        0.00003,
        0.0001,
        0.0003,
        0.001,
    }
    assert len(contract.HGB_GRID) == 4
    assert {row["max_leaf_nodes"] for row in contract.HGB_GRID} == {7, 15}
