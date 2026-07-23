from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import typer
import yaml

from dtr_lab.strategies.asia_sweep.shadow_baseline import (
    VARIANTS,
    classify_variant,
    summarize_trades,
)

app = typer.Typer(add_completion=False)


@app.command()
def main(input_root: Path, baseline_config: Path, output_root: Path) -> None:
    baseline = yaml.safe_load(baseline_config.read_text())
    ledgers = sorted(input_root.rglob("shadow_trade_ledger.csv"))
    if len(ledgers) != 2:
        raise typer.BadParameter(f"expected two instrument ledgers, found {len(ledgers)}")
    trades = pd.concat([pd.read_csv(path) for path in ledgers], ignore_index=True)
    variants: dict[str, object] = {}
    for variant in VARIANTS:
        subset = trades[trades["variant"] == variant].copy()
        nq = summarize_trades(subset[subset["instrument"] == "NQ_PROXY"])
        es = summarize_trades(subset[subset["instrument"] == "ES_PROXY"])
        pooled = summarize_trades(subset)
        entry = pd.to_datetime(subset.get("entry_timestamp"), utc=True, errors="coerce")
        subset["period"] = entry.dt.year.map({2023: "2023", 2024: "2024_H1"})
        periods = {
            str(key): summarize_trades(group)
            for key, group in subset.groupby("period", dropna=True)
        }
        variants[variant] = {
            "NQ_PROXY": nq,
            "ES_PROXY": es,
            "POOLED_EQUAL_EVENT": pooled,
            "POOLED_PERIODS": periods,
            "classification": classify_variant(nq, es, pooled, periods),
        }
    classifications = [str(value["classification"]) for value in variants.values()]
    if "INVALID_BASELINE" in classifications:
        overall = "INVALID_BASELINE"
    elif "PROMISING_DEVELOPMENT_SCREEN" in classifications:
        overall = "PROMISING_DEVELOPMENT_SCREEN"
    elif "PROMISING_BUT_INSUFFICIENT_SAMPLE" in classifications:
        overall = "PROMISING_BUT_INSUFFICIENT_SAMPLE"
    elif "MIXED_NOT_PROMOTABLE" in classifications:
        overall = "MIXED_NOT_PROMOTABLE"
    else:
        overall = "NOT_PROMISING_CURRENT_SPEC"
    output_root.mkdir(parents=True, exist_ok=True)
    trades.to_csv(output_root / "combined_shadow_trade_ledger.csv", index=False)
    summary = {
        "work_package": baseline["work_package"],
        "baseline_id": baseline["baseline_id"],
        "overall_classification": overall,
        "variants": variants,
        "lockbox_opened": False,
        "optimization_performed": False,
        "cme_futures_validated": False,
        "deployment_authorized": False,
    }
    (output_root / "baseline_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )
    rows = []
    for variant, value in variants.items():
        for scope in ("NQ_PROXY", "ES_PROXY", "POOLED_EQUAL_EVENT"):
            rows.append(
                {
                    "variant": variant,
                    "scope": scope,
                    "classification": value["classification"],
                    **value[scope],
                }
            )
    pd.DataFrame(rows).to_csv(output_root / "baseline_summary.csv", index=False)
    typer.echo(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    app()
