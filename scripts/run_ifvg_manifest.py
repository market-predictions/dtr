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
from dtr_lab.research.engine import metrics
from dtr_lab.research.ifvg import (
    IFVGAnnotation,
    IFVGVariant,
    compare_ifvg_portfolios,
    prepare_ifvg_context,
    simulate_ifvg_variant,
    variant_passes,
)
from dtr_lab.research.ifvg_manifest import load_ifvg_manifest, verify_ifvg_dataset
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


def _annotation_from_row(row: object) -> IFVGAnnotation:
    return IFVGAnnotation(
        confirmed=bool(row.ifvg_confirmed),
        direction=int(row.ifvg_direction),
        created_index=int(row.ifvg_created_index),
        inversion_index=int(row.ifvg_inversion_index),
        age_bars=int(row.ifvg_age_bars),
        lower=float(row.ifvg_lower),
        upper=float(row.ifvg_upper),
        zone_size=float(row.ifvg_zone_size),
        zone_size_atr=float(row.ifvg_zone_size_atr),
        minutes_sweep_to_inversion=int(row.ifvg_minutes_sweep_to_inversion),
        minutes_inversion_to_entry=int(row.ifvg_minutes_inversion_to_entry),
        post_inversion_zone_touch=bool(row.ifvg_post_inversion_zone_touch),
        epoch=int(row.ifvg_epoch),
    )


def _cohort_frame(observe: pd.DataFrame, variant: IFVGVariant) -> pd.DataFrame:
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
    parser = argparse.ArgumentParser(description="Run a deterministic IFVG ablation manifest")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    manifest = load_ifvg_manifest(manifest_path)
    dataset_path = verify_ifvg_dataset(manifest, manifest_path)
    output = args.out or Path("reports") / manifest.run_id
    output.mkdir(parents=True, exist_ok=True)

    one_minute = load_zip(dataset_path)
    bars = resample_5m(one_minute)
    sessions = build_session_table(one_minute, bars)
    config = manifest.strategy_config()
    market_arrays = prepare_market_arrays(one_minute)
    prepared = prepare_ifvg_context(one_minute, bars, sessions, config)

    variants = manifest.variant_configs()
    runs: dict[str, tuple[pd.DataFrame, object, pd.DataFrame]] = {}
    for variant in variants:
        runs[variant.name] = simulate_ifvg_variant(
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
        comparison, changed = compare_ifvg_portfolios(observe, trades)
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
