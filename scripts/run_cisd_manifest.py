from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.research import build_session_table, load_zip, prepare_market_arrays, resample_5m
from dtr_lab.research.artifacts import current_commit
from dtr_lab.research.cisd import (
    CISDAnnotation,
    CISDVariant,
    compare_cisd_portfolios,
    prepare_cisd_context,
    simulate_cisd_variant,
    variant_passes,
)
from dtr_lab.research.cisd_manifest import load_cisd_manifest, verify_cisd_dataset
from dtr_lab.research.engine import metrics
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
                (pd.to_datetime(trades["entry_time"]) >= pd.Timestamp(start))
                & (pd.to_datetime(trades["entry_time"]) < pd.Timestamp(end))
            ]
            if not trades.empty
            else trades
        )
        result[name] = metrics(subset)
    return result


def _attribution(trades: pd.DataFrame, column: str) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame(columns=[column])
    return pd.DataFrame(
        [{column: key, **metrics(group)} for key, group in trades.groupby(column)]
    )


def _annotation_from_row(row: object) -> CISDAnnotation:
    return CISDAnnotation(
        sequence_confirmed=bool(row.cisd_sequence_confirmed),
        last_candle_confirmed=bool(row.cisd_last_candle_confirmed),
        direction=int(row.cisd_direction),
        sequence_start_index=int(row.cisd_sequence_start_index),
        sequence_end_index=int(row.cisd_sequence_end_index),
        sequence_confirm_index=int(row.cisd_sequence_confirm_index),
        last_sequence_start_index=int(row.cisd_last_sequence_start_index),
        last_sequence_end_index=int(row.cisd_last_sequence_end_index),
        last_confirm_index=int(row.cisd_last_confirm_index),
        sequence_anchor=float(row.cisd_sequence_anchor),
        last_anchor=float(row.cisd_last_anchor),
        sequence_age_bars=int(row.cisd_sequence_age_bars),
        last_age_bars=int(row.cisd_last_age_bars),
        sequence_length=int(row.cisd_sequence_length),
        last_sequence_length=int(row.cisd_last_sequence_length),
        body_displacement=float(row.cisd_body_displacement),
        body_displacement_atr=float(row.cisd_body_displacement_atr),
        sequence_anchor_distance_atr=float(row.cisd_sequence_anchor_distance_atr),
        minutes_sweep_to_confirm=int(row.cisd_minutes_sweep_to_confirm),
        minutes_confirm_to_entry=int(row.cisd_minutes_confirm_to_entry),
        sequence_retest=bool(row.cisd_sequence_retest),
        sequence_retest_index=int(row.cisd_sequence_retest_index),
        sequence_retest_on_entry_bar=bool(row.cisd_sequence_retest_on_entry_bar),
        bars_retest_to_entry=int(row.cisd_bars_retest_to_entry),
        epoch=int(row.cisd_epoch),
    )


def _cohort_frame(observe: pd.DataFrame, variant: CISDVariant) -> pd.DataFrame:
    if variant.policy == "observe":
        return observe
    mask = [variant_passes(_annotation_from_row(row), variant) for row in observe.itertuples()]
    return observe.loc[mask].copy()


def _verify_observe(actual: dict[str, float], manifest: object) -> None:
    expected = manifest.expected_observe
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
        raise AssertionError("Observe regression failed: " + "; ".join(failures))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a deterministic CISD ablation manifest")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    manifest = load_cisd_manifest(manifest_path)
    dataset_path = verify_cisd_dataset(manifest, manifest_path)
    output = args.out or Path("reports") / manifest.run_id
    output.mkdir(parents=True, exist_ok=True)

    one_minute = load_zip(dataset_path)
    bars = resample_5m(one_minute)
    sessions = build_session_table(one_minute, bars)
    config = manifest.strategy_config()
    market_arrays = prepare_market_arrays(one_minute)
    prepared = prepare_cisd_context(one_minute, bars, sessions, config)

    variants = manifest.variant_configs()
    runs: dict[str, tuple[pd.DataFrame, object, pd.DataFrame]] = {}
    for variant in variants:
        runs[variant.name] = simulate_cisd_variant(
            one_minute,
            bars,
            config,
            variant,
            prepared,
            market_arrays=market_arrays,
        )

    observe_variant = next(variant for variant in variants if variant.policy == "observe")
    observe = runs[observe_variant.name][0]
    observe_metrics = metrics(observe)
    _verify_observe(observe_metrics, manifest)

    leaderboard_rows: list[dict[str, Any]] = []
    cohort_rows: list[dict[str, Any]] = []
    summaries: dict[str, Any] = {}
    changed_rows: list[pd.DataFrame] = []

    for variant in variants:
        trades, funnel, signals = runs[variant.name]
        variant_output = output / variant.name
        variant_output.mkdir(parents=True, exist_ok=True)
        trades.to_csv(variant_output / "trades.csv", index=False)
        trades.to_parquet(variant_output / "trades.parquet", index=False)
        signals.to_csv(variant_output / "signals.csv", index=False)
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
        comparison, changed = compare_cisd_portfolios(observe, trades)
        if not changed.empty:
            changed.insert(0, "variant", variant.name)
            changed_rows.append(changed)
        cohort = _cohort_frame(observe, variant)
        cohort_total = metrics(cohort)
        cohort_period = _period_metrics(cohort, manifest)
        cohort_rows.append(
            {
                "variant": variant.name,
                "policy": variant.policy,
                "coverage": len(cohort) / len(observe) if len(observe) else 0.0,
                **cohort_total,
                **{
                    f"{period_name}_{key}": value
                    for period_name, values in cohort_period.items()
                    for key, value in values.items()
                },
            }
        )
        summary = {
            "variant": asdict(variant),
            "metrics": total,
            "period_metrics": period,
            "funnel": funnel.as_dict(),
            "portfolio_comparison": comparison,
            "cohort_metrics": cohort_total,
            "cohort_period_metrics": cohort_period,
        }
        summaries[variant.name] = summary
        leaderboard_rows.append(
            {
                "variant": variant.name,
                "policy": variant.policy,
                **total,
                **{
                    f"{period_name}_{key}": value
                    for period_name, values in period.items()
                    for key, value in values.items()
                },
                **{f"funnel_{key}": value for key, value in funnel.as_dict().items()},
                **{f"portfolio_{key}": value for key, value in comparison.items()},
            }
        )

    leaderboard = pd.DataFrame(leaderboard_rows)
    leaderboard.to_csv(output / "leaderboard.csv", index=False)
    pd.DataFrame(cohort_rows).to_csv(output / "cohort_summary.csv", index=False)
    attribution = pd.concat(changed_rows, ignore_index=True) if changed_rows else pd.DataFrame()
    attribution.to_csv(output / "changed_trade_attribution.csv", index=False)

    run_summary = {
        "schema_version": 1,
        "run_id": manifest.run_id,
        "code_commit": current_commit(),
        "manifest_path": str(manifest_path),
        "manifest_sha256": file_sha256(manifest_path),
        "dataset_path": str(dataset_path),
        "dataset_sha256": file_sha256(dataset_path),
        "execution": manifest.execution.model_dump(),
        "strategy": asdict(config),
        "observe_regression_status": "passed",
        "variants": summaries,
    }
    with (output / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(_json_value(run_summary), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(leaderboard.to_string(index=False))


if __name__ == "__main__":
    main()
