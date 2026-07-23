from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import typer

from dtr_lab.strategies.asia_sweep.cluster_challenger import summarize_cluster_results

app = typer.Typer(add_completion=False)


@app.command()
def main(input_root: Path, output_root: Path) -> None:
    """Aggregate NQ/ES cluster executions and apply the frozen promotion gate."""

    ledgers = sorted(input_root.rglob("cluster_execution_ledger.csv"))
    if len(ledgers) != 2:
        raise typer.BadParameter(f"expected two execution ledgers, found {len(ledgers)}")
    frames = [pd.read_csv(path) for path in ledgers]
    nonempty = [frame for frame in frames if not frame.empty]
    instruments = {
        str(frame["instrument"].iloc[0])
        for frame in nonempty
        if "instrument" in frame.columns
    }
    if instruments and not instruments.issubset({"NQ_PROXY", "ES_PROXY"}):
        raise typer.BadParameter(f"unexpected instruments: {sorted(instruments)}")
    ledger = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if not ledger.empty and bool(ledger["event_id"].duplicated(keep=False).any()):
        raise ValueError("combined cluster ledger contains duplicate event IDs")
    if not ledger.empty and pd.to_datetime(ledger["trade_date"]).max() >= pd.Timestamp("2024-07-01"):
        raise ValueError("cluster study opened the validation partition")
    summary = summarize_cluster_results(ledger)
    output_root.mkdir(parents=True, exist_ok=True)
    ledger.to_csv(output_root / "combined_cluster_execution_ledger.csv", index=False)
    (output_root / "cluster_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )
    lines = [
        "# Asian Sweep PDH/PDL Cluster Challenger — Development Result",
        "",
        f"Decision: `{summary['decision']}`",
        f"Classification: `{summary['classification']}`",
        "",
        "## Instrument results",
        "",
        "| Instrument | Trades | Net R | Expectancy | Profit factor | Max DD |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for instrument in ("NQ_PROXY", "ES_PROXY"):
        values = summary.get("instruments", {}).get(instrument, {"trades": 0})
        lines.append(
            f"| {instrument} | {values.get('trades', 0)} | "
            f"{values.get('net_r', 0.0):.2f} | {values.get('expectancy_r', 0.0):.3f} | "
            f"{values.get('profit_factor', 0.0):.3f} | {values.get('max_drawdown_r', 0.0):.2f} |"
        )
    lines.extend(["", "## Promotion blockers", ""])
    for blocker in summary.get("promotion_blockers", []):
        lines.append(f"- `{blocker}`")
    lines.extend(
        [
            "",
            "No data on or after 2024-07-01 were opened. This is proxy development evidence, not CME futures validation.",
        ]
    )
    (output_root / "CLUSTER_CHALLENGER_RESULT.md").write_text("\n".join(lines) + "\n")
    typer.echo(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    app()
