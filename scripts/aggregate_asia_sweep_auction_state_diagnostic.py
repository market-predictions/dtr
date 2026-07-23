from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import typer

from dtr_lab.strategies.asia_sweep.auction_state_analysis import (
    build_diagnostic_summary,
    flat_summary_rows,
)

app = typer.Typer(add_completion=False)


@app.command()
def main(input_root: Path, output_root: Path) -> None:
    """Aggregate both proxy ledgers and apply the frozen promotion standard."""

    ledgers = sorted(input_root.rglob("auction_state_ledger.csv"))
    if len(ledgers) != 2:
        raise typer.BadParameter(f"expected two diagnostic ledgers, found {len(ledgers)}")
    frames = [pd.read_csv(path) for path in ledgers]
    instruments = {str(frame["instrument"].iloc[0]) for frame in frames}
    if instruments != {"NQ_PROXY", "ES_PROXY"}:
        raise typer.BadParameter(f"unexpected instrument set: {sorted(instruments)}")
    ledger = pd.concat(frames, ignore_index=True)
    if bool(ledger["event_id"].duplicated(keep=False).any()):
        raise ValueError("combined diagnostic ledger contains duplicate event IDs")
    if pd.to_datetime(ledger["trade_date"]).max() >= pd.Timestamp("2024-07-01"):
        raise ValueError("combined diagnostic opened the validation partition")
    summary = build_diagnostic_summary(ledger)
    output_root.mkdir(parents=True, exist_ok=True)
    ledger.sort_values(["trade_date", "instrument", "session"]).to_csv(
        output_root / "combined_auction_state_ledger.csv",
        index=False,
    )
    flat_summary_rows(summary).to_csv(
        output_root / "mechanism_summary.csv",
        index=False,
    )
    pd.DataFrame(summary["state_distribution"]).to_csv(
        output_root / "state_distribution.csv",
        index=False,
    )
    (output_root / "diagnostic_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )
    typer.echo(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    app()
