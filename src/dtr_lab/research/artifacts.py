from __future__ import annotations

import json
import os
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .engine import Funnel, StrategyConfig, metrics
from .manifest import ResearchManifest, file_sha256


def _json_value(value: Any) -> Any:
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def current_commit() -> str:
    if sha := os.getenv("GITHUB_SHA"):
        return sha
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _empty_trade_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "entry_time",
            "exit_time",
            "session",
            "day_of_week",
            "direction",
            "pnl_r",
            "holding_minutes",
            "mfe_r",
            "mae_r",
        ]
    )


def normalize_trades(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty and "entry_time" not in trades.columns:
        trades = _empty_trade_frame()
    else:
        trades = trades.copy()
    if "entry_time" in trades.columns:
        trades["entry_time"] = pd.to_datetime(trades["entry_time"])
    if "exit_time" in trades.columns:
        trades["exit_time"] = pd.to_datetime(trades["exit_time"])
    return trades


def period_metrics(
    trades: pd.DataFrame, manifest: ResearchManifest
) -> dict[str, dict[str, float]]:
    trades = normalize_trades(trades)
    boundaries = {
        "development": (
            pd.Timestamp(manifest.periods.development_start),
            pd.Timestamp(manifest.periods.development_end),
        ),
        "validation": (
            pd.Timestamp(manifest.periods.development_end),
            pd.Timestamp(manifest.periods.validation_end),
        ),
        "research_later": (
            pd.Timestamp(manifest.periods.validation_end),
            pd.Timestamp(manifest.periods.research_end),
        ),
    }
    result: dict[str, dict[str, float]] = {}
    for name, (start, end) in boundaries.items():
        subset = trades[
            (trades["entry_time"] >= start) & (trades["entry_time"] < end)
        ]
        result[name] = metrics(subset)
    return result


def attribution(trades: pd.DataFrame, column: str) -> pd.DataFrame:
    trades = normalize_trades(trades)
    rows: list[dict[str, Any]] = []
    if trades.empty:
        return pd.DataFrame(columns=[column])
    for key, subset in trades.groupby(column, dropna=False):
        rows.append({column: key, **metrics(subset)})
    return pd.DataFrame(rows)


def halfyear_metrics(trades: pd.DataFrame) -> pd.DataFrame:
    trades = normalize_trades(trades)
    if trades.empty:
        return pd.DataFrame(columns=["period"])
    work = trades.copy()
    year = work["entry_time"].dt.year.astype(str)
    half = np.where(work["entry_time"].dt.month <= 6, "H1", "H2")
    work["period"] = year + half
    rows: list[dict[str, Any]] = []
    for period, subset in work.groupby("period", sort=True):
        rows.append({"period": period, **metrics(subset)})
    return pd.DataFrame(rows)


def verify_expected_baseline(
    actual: dict[str, float], manifest: ResearchManifest
) -> None:
    expected = manifest.expected_baseline
    if expected is None:
        return
    failures: list[str] = []
    if abs(int(actual["trades"]) - expected.trades) > expected.tolerance_trades:
        failures.append(f"trades expected {expected.trades}, actual {actual['trades']}")
    if abs(actual["net_r"] - expected.net_r) > expected.tolerance_net_r:
        failures.append(f"net_r expected {expected.net_r}, actual {actual['net_r']}")
    if (
        abs(actual["max_drawdown_r"] - expected.max_drawdown_r)
        > expected.tolerance_max_drawdown_r
    ):
        failures.append(
            "max_drawdown_r expected "
            f"{expected.max_drawdown_r}, actual {actual['max_drawdown_r']}"
        )
    if failures:
        raise AssertionError("Baseline regression failed: " + "; ".join(failures))


def write_run_artifacts(
    output_dir: str | Path,
    manifest_path: str | Path,
    dataset_path: str | Path,
    manifest: ResearchManifest,
    config: StrategyConfig,
    trades: pd.DataFrame,
    funnel: Funnel,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    trades = normalize_trades(trades)
    total_metrics = metrics(trades)
    verify_expected_baseline(total_metrics, manifest)

    trades.to_csv(output / "trades.csv", index=False)
    trades.to_parquet(output / "trades.parquet", index=False)
    pd.DataFrame([funnel.as_dict()]).to_csv(output / "funnel.csv", index=False)
    halfyear_metrics(trades).to_csv(output / "halfyear.csv", index=False)
    attribution(trades, "session").to_csv(output / "by_session.csv", index=False)
    attribution(trades, "day_of_week").to_csv(output / "by_weekday.csv", index=False)
    attribution(trades, "direction").to_csv(output / "by_direction.csv", index=False)

    summary: dict[str, Any] = {
        "schema_version": 1,
        "run_id": manifest.run_id,
        "candidate_name": manifest.candidate_name,
        "code_commit": current_commit(),
        "manifest_path": str(manifest_path),
        "manifest_sha256": file_sha256(manifest_path),
        "dataset_path": str(dataset_path),
        "dataset_sha256": file_sha256(dataset_path),
        "strategy": asdict(config),
        "execution": manifest.execution.model_dump(),
        "periods": manifest.periods.model_dump(mode="json"),
        "metrics": total_metrics,
        "period_metrics": period_metrics(trades, manifest),
        "funnel": funnel.as_dict(),
        "regression_status": "passed",
    }
    with (output / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(_json_value(summary), handle, indent=2, sort_keys=True)
        handle.write("\n")
    return summary
