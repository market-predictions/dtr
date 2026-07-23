from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import typer
import yaml

from dtr_lab.research.engine import load_zip, resample_5m
from dtr_lab.strategies.asia_sweep.model import AsiaSweepConfig, AsiaSweepVariant
from dtr_lab.strategies.asia_sweep.signals import build_event_ledger

app = typer.Typer(add_completion=False)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_manifest(path: Path) -> dict[str, object]:
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise ValueError("Manifest must be a mapping")
    separation = data.get("separation", {})
    if separation.get("strategy_namespace") != "asia_sweep":
        raise ValueError("Manifest is not in the Asia Sweep namespace")
    if separation.get("call_active_dtr_generate_signals") is not False:
        raise ValueError("Asia Sweep may not call the active DTR signal generator")
    if separation.get("write_into_dtr_results") is not False:
        raise ValueError("Asia Sweep outputs must remain separate")
    return data


def _config(manifest: dict[str, object], variant: AsiaSweepVariant) -> AsiaSweepConfig:
    dataset = manifest["dataset"]
    strategy = manifest["strategy"]
    execution = manifest["execution"]
    return AsiaSweepConfig(
        name=f"{manifest['strategy_id']}:{variant.value}",
        variant=variant,
        tick_size=float(dataset["tick_size"]),
        point_value=float(dataset["point_value"]),
        commission_per_side=float(dataset["commission_per_side"]),
        slippage_ticks_each_side=float(execution["slippage_ticks_each_side"]),
        weekdays=tuple(int(x) for x in strategy["weekdays"]),
        min_sweep_ticks=int(strategy["min_sweep_ticks"]),
        wick_ratio_min=float(strategy["wick_ratio_min"]),
        close_location_min=float(strategy["close_location_min"]),
        displacement_max_bars=int(strategy["displacement_max_bars"]),
        displacement_body_mult=float(strategy["displacement_body_mult"]),
        displacement_median_length=int(strategy["displacement_median_length"]),
        failed_retest_max_bars=int(strategy["failed_retest_max_bars"]),
        retest_band_ticks=int(strategy["retest_band_ticks"]),
        stop_buffer_ticks=int(strategy["stop_buffer_ticks"]),
        target_rr=float(strategy["target_rr"]),
    )


@app.command()
def main(manifest_path: Path) -> None:
    """Build Asia Sweep event ledgers only; P&L execution is intentionally disabled."""

    manifest = _load_manifest(manifest_path)
    dataset = manifest["dataset"]
    if dataset["qualification_status"] == "DATA_NOT_REGISTERED":
        raise typer.BadParameter(
            "Dataset is not registered; fill path, checksum and semantics first"
        )
    if dataset["loader"] != "dtr_zip_v1":
        raise typer.BadParameter("Foundation runner currently supports only dtr_zip_v1")
    source = Path(dataset["path"])
    if not source.exists():
        raise typer.BadParameter(f"Dataset not found: {source}")
    expected = str(dataset["sha256"])
    actual = _sha256(source)
    if actual != expected:
        raise typer.BadParameter(f"Dataset checksum mismatch: expected {expected}, got {actual}")

    one = load_zip(source)
    bars = resample_5m(one)
    start = pd.Timestamp(manifest["periods"]["development_start"])
    end = pd.Timestamp(manifest["periods"]["development_end"])
    one = one[(one["timestamp"] >= start - pd.Timedelta(days=1)) & (one["timestamp"] < end)]
    bars = bars[
        (bars["timestamp"] >= start - pd.Timedelta(days=1))
        & (bars["timestamp"] < end)
    ]

    out_root = Path(manifest["outputs"]["root"])
    out_root.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, object]] = []
    for variant_name in manifest["strategy"]["variants"]:
        variant = AsiaSweepVariant(variant_name)
        ledger = build_event_ledger(
            str(dataset["instrument"]),
            one,
            bars,
            _config(manifest, variant),
        )
        ledger_path = out_root / f"{variant.value.lower()}_event_ledger.csv"
        ledger.to_csv(ledger_path, index=False)
        counts = ledger["status"].value_counts(dropna=False).to_dict()
        summaries.append(
            {
                "variant": variant.value,
                "rows": int(len(ledger)),
                "signals": int((ledger["status"] == "SIGNAL").sum()),
                "status_counts": {str(k): int(v) for k, v in counts.items()},
                "ledger": str(ledger_path),
            }
        )

    summary = {
        "run_id": manifest["run_id"],
        "strategy_id": manifest["strategy_id"],
        "instrument": dataset["instrument"],
        "research_status": manifest["research_status"],
        "execution_status": manifest["execution"]["status"],
        "pnl_calculated": False,
        "variants": summaries,
    }
    (out_root / "event_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )
    typer.echo(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    app()
