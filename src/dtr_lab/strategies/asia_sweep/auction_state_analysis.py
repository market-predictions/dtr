from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

_RETURN_COLUMNS = (
    "return_30m_range_fraction",
    "return_60m_range_fraction",
)


def _safe_mean(series: pd.Series) -> float | None:
    values = pd.to_numeric(series, errors="coerce").dropna()
    return float(values.mean()) if not values.empty else None


def _safe_median(series: pd.Series) -> float | None:
    values = pd.to_numeric(series, errors="coerce").dropna()
    return float(values.median()) if not values.empty else None


def group_summary(frame: pd.DataFrame) -> dict[str, Any]:
    result: dict[str, Any] = {"observations": int(len(frame))}
    for horizon in (5, 15, 30, 60):
        result[f"mean_return_{horizon}m_range_fraction"] = _safe_mean(
            frame[f"return_{horizon}m_range_fraction"]
        )
        result[f"median_return_{horizon}m_range_fraction"] = _safe_median(
            frame[f"return_{horizon}m_range_fraction"]
        )
        result[f"mean_mfe_{horizon}m_range_fraction"] = _safe_mean(
            frame[f"mfe_{horizon}m_range_fraction"]
        )
        result[f"mean_mae_{horizon}m_range_fraction"] = _safe_mean(
            frame[f"mae_{horizon}m_range_fraction"]
        )
    for name in ("midpoint_hit", "projection_hit", "opposite_boundary_hit"):
        values = frame[name].dropna()
        result[f"{name}_rate"] = float(values.astype(bool).mean()) if not values.empty else None
    return result


def cluster_bootstrap_mean(
    frame: pd.DataFrame,
    column: str,
    *,
    draws: int = 5000,
    seed: int = 20260723,
) -> dict[str, float | int | None]:
    values = frame[["trade_date", column]].copy()
    values[column] = pd.to_numeric(values[column], errors="coerce")
    values = values.dropna()
    if values.empty:
        return {"clusters": 0, "mean": None, "ci_low": None, "ci_high": None}
    clusters = values.groupby("trade_date")[column].agg(["sum", "count"])
    array = clusters.to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(array), size=(draws, len(array)))
    sampled_sum = array[indices, 0].sum(axis=1)
    sampled_count = array[indices, 1].sum(axis=1)
    means = sampled_sum / sampled_count
    low, high = np.quantile(means, [0.025, 0.975])
    return {
        "clusters": int(len(array)),
        "mean": float(values[column].mean()),
        "ci_low": float(low),
        "ci_high": float(high),
    }


def _period_label(series: pd.Series) -> pd.Series:
    years = pd.to_datetime(series, errors="raise").dt.year
    return pd.Series(np.where(years == 2023, "2023", "2024_H1"), index=series.index)


def _cell_metrics(frame: pd.DataFrame) -> dict[str, Any]:
    result = group_summary(frame)
    result["bootstrap_30m"] = cluster_bootstrap_mean(
        frame,
        "return_30m_range_fraction",
        seed=20260724,
    )
    result["bootstrap_60m"] = cluster_bootstrap_mean(
        frame,
        "return_60m_range_fraction",
        seed=20260725,
    )
    return result


def _mechanism_cells(
    frame: pd.DataFrame,
    *,
    mechanism: str,
) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for session in ("LONDON", "NEW_YORK"):
        session_frame = frame[frame["session"] == session]
        instruments: dict[str, Any] = {}
        for instrument in ("NQ_PROXY", "ES_PROXY"):
            instruments[instrument] = _cell_metrics(
                session_frame[session_frame["instrument"] == instrument]
            )
        pooled = session_frame.copy()
        pooled["period"] = _period_label(pooled["trade_date"])
        periods = {
            str(period): _cell_metrics(group)
            for period, group in pooled.groupby("period")
        }
        output[session] = {
            "mechanism": mechanism,
            "instruments": instruments,
            "periods": periods,
            "pooled": _cell_metrics(pooled),
        }
    return output


def _positive(value: Any) -> bool:
    return value is not None and math.isfinite(float(value)) and float(value) > 0


def _passes_session(cell: dict[str, Any]) -> bool:
    instruments = cell["instruments"]
    for instrument in ("NQ_PROXY", "ES_PROXY"):
        metrics = instruments[instrument]
        if int(metrics["observations"]) < 40:
            return False
        if not _positive(metrics["mean_return_30m_range_fraction"]):
            return False
        if not _positive(metrics["mean_return_60m_range_fraction"]):
            return False
    for period in ("2023", "2024_H1"):
        metrics = cell["periods"].get(period)
        if metrics is None:
            return False
        if not _positive(metrics["mean_return_30m_range_fraction"]):
            return False
        if not _positive(metrics["mean_return_60m_range_fraction"]):
            return False
    return True


def _replace_with_retest_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy(deep=True)
    metric_names = [
        "anchor_timestamp",
        "anchor_price",
        "anchor_active",
        "midpoint_hit",
        "projection_hit",
        "opposite_boundary_hit",
        "return_session_range_fraction",
        "mfe_session_range_fraction",
        "mae_session_range_fraction",
    ]
    for horizon in (5, 15, 30, 60):
        metric_names.extend(
            [
                f"return_{horizon}m_range_fraction",
                f"mfe_{horizon}m_range_fraction",
                f"mae_{horizon}m_range_fraction",
            ]
        )
    for name in metric_names:
        result[name] = result[f"retest_{name}"]
    return result


def build_diagnostic_summary(ledger: pd.DataFrame) -> dict[str, Any]:
    required = {
        "instrument",
        "trade_date",
        "session",
        "state",
        "compression_bucket",
        "external_confluence",
        "retest_resume",
        "retest_return_30m_range_fraction",
        "retest_return_60m_range_fraction",
        *_RETURN_COLUMNS,
    }
    missing = required.difference(ledger.columns)
    if missing:
        raise ValueError(f"diagnostic ledger missing columns: {sorted(missing)}")
    state_distribution = (
        ledger.groupby(["instrument", "session", "state"])
        .size()
        .rename("observations")
        .reset_index()
        .to_dict(orient="records")
    )
    rejection = ledger[
        (ledger["state"] == "REJECTION") & ledger["external_confluence"].astype(bool)
    ].copy()
    acceptance = ledger[
        (ledger["state"] == "ACCEPTANCE")
        & (ledger["compression_bucket"] == "COMPRESSED")
    ].copy()
    acceptance_retest = acceptance[acceptance["retest_resume"].astype(bool)].copy()
    acceptance_retest = _replace_with_retest_metrics(acceptance_retest)
    rejection_cells = _mechanism_cells(
        rejection,
        mechanism="EXTERNAL_LIQUIDITY_REJECTION",
    )
    acceptance_cells = _mechanism_cells(
        acceptance,
        mechanism="COMPRESSED_RANGE_ACCEPTANCE",
    )
    retest_cells = _mechanism_cells(
        acceptance_retest,
        mechanism="COMPRESSED_ACCEPTANCE_HELD_RETEST",
    )
    passing = [
        f"COMPRESSED_RANGE_ACCEPTANCE:{session}"
        for session, cell in acceptance_cells.items()
        if _passes_session(cell)
    ]
    passing.extend(
        f"EXTERNAL_LIQUIDITY_REJECTION:{session}"
        for session, cell in rejection_cells.items()
        if _passes_session(cell)
    )
    passing = sorted(set(passing))
    selected = passing[0] if len(passing) == 1 else None
    decision = (
        "PROMOTE_ONE_CHALLENGER"
        if selected is not None
        else "NO_MECHANISM_PASSES_DEVELOPMENT_PROMOTION_STANDARD"
    )
    return {
        "diagnostic_status": "EXPLORATORY_DEVELOPMENT_ONLY",
        "state_distribution": state_distribution,
        "external_liquidity_rejection": rejection_cells,
        "compressed_range_acceptance": acceptance_cells,
        "compressed_acceptance_held_retest": retest_cells,
        "passing_mechanism_sessions": passing,
        "selected_challenger": selected,
        "decision": decision,
        "multiple_comparison_note": (
            "Bootstrap intervals are descriptive and unadjusted. The diagnostic was informed "
            "by a feasibility preview and is not out-of-sample evidence."
        ),
        "pnl_calculated": False,
        "execution_simulated": False,
        "validation_partition_opened": False,
    }


def flat_summary_rows(summary: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for family_key in (
        "external_liquidity_rejection",
        "compressed_range_acceptance",
        "compressed_acceptance_held_retest",
    ):
        family = summary[family_key]
        for session, cell in family.items():
            for instrument, metrics in cell["instruments"].items():
                rows.append(
                    {
                        "family": family_key,
                        "session": session,
                        "scope": instrument,
                        **{
                            key: value
                            for key, value in metrics.items()
                            if not isinstance(value, dict)
                        },
                    }
                )
            for period, metrics in cell["periods"].items():
                rows.append(
                    {
                        "family": family_key,
                        "session": session,
                        "scope": period,
                        **{
                            key: value
                            for key, value in metrics.items()
                            if not isinstance(value, dict)
                        },
                    }
                )
    return pd.DataFrame(rows)
