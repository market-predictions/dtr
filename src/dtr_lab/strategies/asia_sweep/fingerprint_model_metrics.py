from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from dtr_lab.strategies.asia_sweep.fingerprint_model_contract import CandidateSummary


def _safe_average_precision(y: np.ndarray, p: np.ndarray) -> float:
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(average_precision_score(y, p))


def _safe_roc_auc(y: np.ndarray, p: np.ndarray) -> float:
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(roc_auc_score(y, p))


def calibration_intercept_slope(y: np.ndarray, p: np.ndarray) -> tuple[float, float]:
    eps = 1e-6
    x = np.log(np.clip(p, eps, 1 - eps) / np.clip(1 - p, eps, 1 - eps))
    design = np.column_stack([np.ones(len(x)), x])
    beta = np.array([0.0, 1.0], dtype=float)
    for _ in range(100):
        eta = design @ beta
        mu = 1.0 / (1.0 + np.exp(-np.clip(eta, -35, 35)))
        weights = np.clip(mu * (1.0 - mu), 1e-8, None)
        hessian = design.T @ (weights[:, None] * design)
        gradient = design.T @ (y - mu)
        try:
            step = np.linalg.solve(hessian, gradient)
        except np.linalg.LinAlgError:
            return float("nan"), float("nan")
        beta = beta + step
        if np.max(np.abs(step)) < 1e-9:
            break
    return float(beta[0]), float(beta[1])


def add_test_fold_quintiles(predictions: pd.DataFrame) -> pd.DataFrame:
    result = predictions.copy()
    result["quintile"] = 0
    for _, indices in result.groupby("outer_year").groups.items():
        frame = result.loc[list(indices)].sort_values(["prediction", "event_id"])
        ranks = frame["prediction"].rank(method="first", pct=True)
        quintile = np.ceil(ranks * 5).clip(1, 5).astype(int)
        result.loc[frame.index, "quintile"] = quintile.to_numpy()
    return result


def weekly_ranking(predictions: pd.DataFrame) -> pd.DataFrame:
    ranked = predictions.sort_values(
        ["instrument", "week_key", "prediction", "sweep_timestamp_utc", "event_id"],
        ascending=[True, True, False, True, True],
        kind="mergesort",
    )
    rows: list[dict[str, Any]] = []
    for (instrument, week_key), group in ranked.groupby(["instrument", "week_key"], sort=True):
        selected = group.iloc[0]
        successes = int(group["target"].sum())
        rows.append(
            {
                "instrument": instrument,
                "week_key": week_key,
                "year": int(selected["year"]),
                "candidate_count": int(len(group)),
                "success_count": successes,
                "contains_success": bool(successes > 0),
                "selected_event_id": selected["event_id"],
                "selected_prediction": float(selected["prediction"]),
                "selected_success": int(selected["target"]),
                "naive_random_success_probability": float(successes / len(group)),
                "regret": int(successes > 0 and selected["target"] == 0),
            }
        )
    return pd.DataFrame(rows)


def _relative_lift(value: float, baseline: float) -> float:
    return float(value / baseline - 1.0) if baseline > 0 else float("nan")


def _subgroup_top_lift_counts(
    predictions: pd.DataFrame, group_column: str
) -> tuple[int, pd.DataFrame]:
    rows = []
    for value, group in predictions.groupby(group_column):
        base = float(group["target"].mean())
        top = float(group.loc[group["quintile"] == 5, "target"].mean())
        rows.append(
            {
                group_column: value,
                "base_rate": base,
                "top_quintile_rate": top,
                "top_quintile_lift": _relative_lift(top, base),
                "positive": bool(np.isfinite(top) and top > base),
            }
        )
    result = pd.DataFrame(rows)
    return int(result["positive"].sum()), result


def summarize_candidate(
    predictions: pd.DataFrame,
    landmark: str,
    family: str,
) -> tuple[CandidateSummary, dict[str, pd.DataFrame]]:
    q = add_test_fold_quintiles(predictions)
    y = q["target"].to_numpy(dtype=int)
    p = q["prediction"].to_numpy(dtype=float)
    base = float(y.mean())
    pr_auc = _safe_average_precision(y, p)
    roc_auc = _safe_roc_auc(y, p)
    brier = float(brier_score_loss(y, p))
    baseline_brier = float(brier_score_loss(y, q["baseline_prediction"].to_numpy()))
    cal_intercept, cal_slope = calibration_intercept_slope(y, p)
    top_rate = float(q.loc[q["quintile"] == 5, "target"].mean())
    bottom_rate = float(q.loc[q["quintile"] == 1, "target"].mean())
    weekly = weekly_ranking(q)
    hit = float(weekly["selected_success"].mean())
    naive = float(weekly["naive_random_success_probability"].mean())
    pair_positive, pair_table = _subgroup_top_lift_counts(q, "instrument")
    year_positive, year_table = _subgroup_top_lift_counts(q, "year")
    _, side_table = _subgroup_top_lift_counts(q, "side")
    _, weekday_table = _subgroup_top_lift_counts(q, "weekday")
    q["decile"] = 0
    for _, indices in q.groupby("outer_year").groups.items():
        frame = q.loc[list(indices)].sort_values(["prediction", "event_id"])
        ranks = frame["prediction"].rank(method="first", pct=True)
        decile = np.ceil(ranks * 10).clip(1, 10).astype(int)
        q.loc[frame.index, "decile"] = decile.to_numpy()
    calibration = (
        q.groupby("decile", as_index=False)
        .agg(
            event_count=("target", "size"),
            mean_prediction=("prediction", "mean"),
            observed_success_rate=("target", "mean"),
        )
        .sort_values("decile")
    )
    predicates = {
        "pr_auc_lift_at_least_15pct": _relative_lift(pr_auc, base) >= 0.15,
        "top_quintile_at_least_1_50x": top_rate >= 1.50 * base,
        "bottom_quintile_below_base": bottom_rate < base,
        "brier_improves_baseline": brier < baseline_brier,
        "hit_at_1_lift_at_least_15pct": _relative_lift(hit, naive) >= 0.15,
        "both_pairs_positive_top_lift": pair_positive == 2,
        "five_of_seven_years_positive_top_lift": year_positive >= 5,
        "calibration_slope_in_range": 0.4 <= cal_slope <= 1.8,
    }
    failed = tuple(name for name, passed in predicates.items() if not passed)
    summary = CandidateSummary(
        landmark=landmark,
        family=family,
        base_rate=base,
        pr_auc=pr_auc,
        pr_auc_relative_lift=_relative_lift(pr_auc, base),
        roc_auc=roc_auc,
        brier=brier,
        baseline_brier=baseline_brier,
        calibration_intercept=cal_intercept,
        calibration_slope=cal_slope,
        top_quintile_rate=top_rate,
        top_quintile_lift=_relative_lift(top_rate, base),
        bottom_quintile_rate=bottom_rate,
        hit_at_1=hit,
        naive_hit_at_1=naive,
        hit_at_1_relative_lift=_relative_lift(hit, naive),
        pair_positive_top_lift_count=pair_positive,
        year_positive_top_lift_count=year_positive,
        eligible=not failed,
        failed_predicates=failed,
    )
    return summary, {
        "predictions": q,
        "weekly": weekly,
        "pair_top_lift": pair_table,
        "year_top_lift": year_table,
        "side_top_lift": side_table,
        "weekday_top_lift": weekday_table,
        "calibration": calibration,
    }


def choose_final_candidate(summaries: list[CandidateSummary]) -> CandidateSummary | None:
    eligible = [summary for summary in summaries if summary.eligible]
    if not eligible:
        return None
    eligible.sort(key=lambda value: value.pr_auc, reverse=True)
    best_pr = eligible[0].pr_auc
    close = [value for value in eligible if best_pr - value.pr_auc < 0.01]
    close.sort(
        key=lambda value: (
            value.brier,
            0 if value.family == "elastic_net" else 1,
            0 if value.landmark == "T0" else 1,
        )
    )
    return close[0]


def evaluate_abstention(predictions: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    q = add_test_fold_quintiles(predictions)
    base = float(q["target"].mean())
    weekly = weekly_ranking(q)
    rows = []
    selected_rule: dict[str, Any] | None = None
    for quantile in (0.50, 0.60, 0.70, 0.80, 0.90):
        threshold = float(q["prediction"].quantile(quantile))
        selected = weekly.loc[weekly["selected_prediction"] >= threshold].copy()
        coverage = float(len(selected) / len(weekly)) if len(weekly) else 0.0
        selected_rate = (
            float(selected["selected_success"].mean()) if len(selected) else float("nan")
        )
        pair_positive = 0
        for _, group in selected.groupby("instrument"):
            rate = float(group["selected_success"].mean())
            pair_positive += int(rate > base)
        year_positive = 0
        for _, group in selected.groupby("year"):
            rate = float(group["selected_success"].mean())
            year_positive += int(rate > base)
        qualifies = bool(
            coverage >= 0.25
            and np.isfinite(selected_rate)
            and selected_rate >= 1.75 * base
            and pair_positive == 2
            and year_positive >= 5
        )
        row = {
            "quantile": quantile,
            "threshold": threshold,
            "selected_pair_weeks": int(len(selected)),
            "total_pair_weeks": int(len(weekly)),
            "coverage": coverage,
            "selected_success_rate": selected_rate,
            "base_rate": base,
            "selected_relative_lift": _relative_lift(selected_rate, base),
            "pair_positive_count": pair_positive,
            "year_positive_count": year_positive,
            "qualifies": qualifies,
        }
        rows.append(row)
        if selected_rule is None and qualifies:
            selected_rule = row.copy()
    if selected_rule is None:
        selected_rule = {"status": "NO_ABSTENTION_THRESHOLD"}
    else:
        selected_rule["status"] = "FROZEN_ABSTENTION_THRESHOLD"
    return pd.DataFrame(rows), selected_rule
