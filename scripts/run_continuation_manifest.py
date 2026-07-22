from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.research import build_session_table, load_zip, resample_5m
from dtr_lab.research.continuation import run_continuation_backtest
from dtr_lab.research.continuation_manifest import (
    load_continuation_manifest,
    verify_continuation_dataset,
)
from dtr_lab.research.engine import metrics, prepare_market_arrays
from dtr_lab.research.manifest import file_sha256


def _json_value(value: Any) -> Any:
    if isinstance(value, (np.integer, np.floating)):
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


def _attribution(trades: pd.DataFrame, column: str) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame(columns=[column])
    return pd.DataFrame(
        [{column: key, **metrics(group)} for key, group in trades.groupby(column)]
    )


def _period_metrics(trades: pd.DataFrame, manifest: object) -> dict[str, dict[str, float]]:
    periods = manifest.periods
    bounds = {
        "development": (periods.development_start, periods.development_end),
        "validation": (periods.development_end, periods.validation_end),
        "research_later": (periods.validation_end, periods.research_end),
    }
    result: dict[str, dict[str, float]] = {}
    for name, (start, end) in bounds.items():
        subset = (
            trades[
                (trades["entry_time"] >= pd.Timestamp(start))
                & (trades["entry_time"] < pd.Timestamp(end))
            ]
            if not trades.empty
            else trades
        )
        result[name] = metrics(subset)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a continuation research manifest")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    manifest = load_continuation_manifest(manifest_path)
    dataset_path = verify_continuation_dataset(manifest, manifest_path)
    output = args.out or Path("reports") / manifest.run_id
    output.mkdir(parents=True, exist_ok=True)

    one_minute = load_zip(dataset_path)
    bars = resample_5m(one_minute)
    sessions = build_session_table(one_minute, bars)
    market_arrays = prepare_market_arrays(one_minute)

    leaderboard_rows: list[dict[str, Any]] = []
    summaries: dict[str, Any] = {}
    for config in manifest.configs():
        trades, funnel = run_continuation_backtest(
            one_minute,
            bars,
            sessions,
            config,
            market_arrays=market_arrays,
            gap_policy=manifest.execution.gap_policy,
        )
        variant_output = output / config.name
        variant_output.mkdir(parents=True, exist_ok=True)
        trades.to_csv(variant_output / "trades.csv", index=False)
        trades.to_parquet(variant_output / "trades.parquet", index=False)
        pd.DataFrame([funnel.as_dict()]).to_csv(variant_output / "funnel.csv", index=False)
        for column, filename in (
            ("session", "by_session.csv"),
            ("day_of_week", "by_weekday.csv"),
            ("direction", "by_direction.csv"),
            ("exit_reason", "by_exit_reason.csv"),
        ):
            _attribution(trades, column).to_csv(variant_output / filename, index=False)

        total = metrics(trades)
        period = _period_metrics(trades, manifest)
        summary = {
            "config": asdict(config),
            "metrics": total,
            "period_metrics": period,
            "funnel": funnel.as_dict(),
        }
        summaries[config.name] = summary
        leaderboard_rows.append(
            {
                "name": config.name,
                "acceptance_bars": config.acceptance_bars,
                "entry_mode": config.entry_mode,
                "min_minutes_from_range_end": config.min_minutes_from_range_end,
                **{f"all_{key}": value for key, value in total.items()},
                **{
                    f"{period_name}_{key}": value
                    for period_name, values in period.items()
                    for key, value in values.items()
                },
                **{f"funnel_{key}": value for key, value in funnel.as_dict().items()},
            }
        )

    leaderboard = pd.DataFrame(leaderboard_rows)
    leaderboard.to_csv(output / "leaderboard.csv", index=False)
    run_summary = {
        "schema_version": 1,
        "run_id": manifest.run_id,
        "manifest_path": str(manifest_path),
        "manifest_sha256": file_sha256(manifest_path),
        "dataset_path": str(dataset_path),
        "dataset_sha256": file_sha256(dataset_path),
        "execution": manifest.execution.model_dump(),
        "variants": summaries,
    }
    with (output / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(_json_value(run_summary), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(leaderboard.to_string(index=False))


if __name__ == "__main__":
    main()
