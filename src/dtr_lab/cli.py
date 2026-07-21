from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from dtr_lab.data import audit_market_data, load_market_data

app = typer.Typer(no_args_is_help=True, add_completion=False)
console = Console()


@app.command("audit")
def audit_command(
    path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            readable=True,
            help="CSV or ZIP market-data file",
        ),
    ],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Optional JSON output path"),
    ] = None,
) -> None:
    """Validate a market-data file and print a compact audit."""

    frame = load_market_data(path)
    audit = audit_market_data(frame)
    payload = audit.to_dict()

    table = Table(title="DTR Dataset Audit")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    for key, value in payload.items():
        table.add_row(key, str(value))
    console.print(table)

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        console.print(f"Wrote audit JSON to {output}")


if __name__ == "__main__":
    app()
