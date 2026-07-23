from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import typer
import yaml

from dtr_lab.strategies.asia_sweep.shadow_baseline import (
    SESSION_TIMEZONE,
    VARIANTS,
    ShadowExecutionConfig,
    instrument_breakdowns,
    load_source_window,
    sha256_file,
    simulate_event,
)

app = typer.Typer(add_completion=False)


def _load_yaml(path: Path) -> dict[str, object]:
    value = yaml.safe_load(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"YAML file is not a mapping: {path}")
    return value


@app.command()
def main(
    baseline_config: Path,
    manifest_path: Path,
    report_root: Path,
) -> None:
    baseline = _load_yaml(baseline_config)
    manifest = _load_yaml(manifest_path)
    dataset = manifest["dataset"]
    instrument = str(dataset["instrument"])
    if instrument not in baseline["instruments"]:
        raise typer.BadParameter(f"instrument not preregistered: {instrument}")
    instrument_spec = baseline["instruments"][instrument]
    if str(dataset["source_instrument"]) != str(instrument_spec["source_instrument"]):
        raise typer.BadParameter("source instrument differs from preregistration")
    source = Path(str(dataset["path"]))
    if not source.exists():
        raise typer.BadParameter(f"source ZIP not found: {source}")
    expected_sha = str(dataset["sha256"])
    actual_sha = sha256_file(source)
    if actual_sha != expected_sha:
        raise typer.BadParameter("source checksum mismatch")
    periods = baseline["periods"]
    start = pd.Timestamp(periods["development_start"]).tz_localize(SESSION_TIMEZONE)
    end = pd.Timestamp(periods["development_end_exclusive"]).tz_localize(
        SESSION_TIMEZONE
    )
    source_frame = load_source_window(
        source,
        start=start - pd.DateOffset(days=1),
        end=end + pd.DateOffset(days=1),
    )
    cfg = ShadowExecutionConfig(
        instrument=instrument,
        source_instrument=str(dataset["source_instrument"]),
        point_value=float(dataset["point_value"]),
        commission_per_side=float(dataset["commission_per_side"]),
        entry_slippage_ticks=float(manifest["execution"]["slippage_ticks_each_side"]),
        stop_slippage_ticks=float(manifest["execution"]["slippage_ticks_each_side"]),
        market_exit_slippage_ticks=float(
            manifest["execution"]["slippage_ticks_each_side"]
        ),
        maximum_consecutive_inactive_minutes=int(
            dataset["activity_gate"]["maximum_consecutive_zero_volume_minutes"]
        ),
    )
    rows: list[dict[str, object]] = []
    event_counts: dict[str, object] = {}
    for variant in VARIANTS:
        ledger_path = report_root / f"{variant.lower()}_event_ledger.csv"
        ledger = pd.read_csv(ledger_path)
        event_counts[variant] = {
            str(key): int(value)
            for key, value in ledger["status"].value_counts(dropna=False).items()
        }
        signals = ledger[ledger["status"] == "SIGNAL"].copy()
        for _, event in signals.iterrows():
            try:
                rows.append(simulate_event(event, source_frame, cfg))
            except Exception as exc:
                rows.append(
                    {
                        "instrument": instrument,
                        "trade_date": pd.Timestamp(event["trade_date"]).strftime(
                            "%Y-%m-%d"
                        ),
                        "execution_window": str(event["execution_window"]),
                        "variant": variant,
                        "direction": int(event["direction"]),
                        "status": "BLOCKED",
                        "reason": "SHADOW_PIPELINE_ERROR",
                        "error": str(exc),
                    }
                )
    trades = pd.DataFrame(rows)
    output = report_root / "first_proxy_baseline"
    output.mkdir(parents=True, exist_ok=True)
    trades.to_csv(output / "shadow_trade_ledger.csv", index=False)
    summary = {
        "work_package": baseline["work_package"],
        "baseline_id": baseline["baseline_id"],
        "instrument": instrument,
        "source_instrument": cfg.source_instrument,
        "source_sha256": actual_sha,
        "development_start": str(periods["development_start"]),
        "development_end_exclusive": str(periods["development_end_exclusive"]),
        "event_status_counts": event_counts,
        "trade_ledger_rows": int(len(trades)),
        "breakdowns": instrument_breakdowns(trades),
        "private_source_removed_before_upload": False,
        "cme_futures_validated": False,
        "deployment_authorized": False,
    }
    (output / "instrument_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )
    typer.echo(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    app()
