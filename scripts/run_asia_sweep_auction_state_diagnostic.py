from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import typer
import yaml

from dtr_lab.strategies.asia_sweep.auction_state import (
    DEVELOPMENT_END,
    DEVELOPMENT_START,
    build_auction_state_ledger,
)
from dtr_lab.strategies.asia_sweep.data import ZipCsvSchema, load_one_minute_zip

app = typer.Typer(add_completion=False)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_yaml(path: Path) -> dict[str, object]:
    value = yaml.safe_load(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"YAML file must contain a mapping: {path}")
    return value


@app.command()
def main(manifest_path: Path, output_root: Path) -> None:
    """Run the development-only auction-state diagnostic without P&L."""

    manifest = _load_yaml(manifest_path)
    dataset = manifest["dataset"]
    periods = manifest["periods"]
    if str(periods["development_start"]) != "2023-01-01T00:00:00":
        raise typer.BadParameter("development_start differs from frozen diagnostic")
    if str(periods["development_end"]) != "2024-07-01T00:00:00":
        raise typer.BadParameter("development_end differs from frozen diagnostic")
    if dataset["source_kind"] != "DUKASCOPY_INDEX_CFD_PROXY":
        raise typer.BadParameter("diagnostic requires the registered Dukascopy proxy")
    if dataset["session_timezone"] != "America/New_York":
        raise typer.BadParameter("diagnostic requires America/New_York session time")
    source = Path(str(dataset["path"]))
    if not source.exists():
        raise typer.BadParameter(f"private source not found: {source}")
    expected = str(dataset["sha256"])
    actual = _sha256(source)
    if actual != expected:
        raise typer.BadParameter(
            f"source checksum mismatch: expected {expected}, received {actual}"
        )
    schema_data = dataset["schema"]
    schema = ZipCsvSchema(
        timestamp_column=str(schema_data["timestamp_column"]),
        timestamp_format=schema_data.get("timestamp_format"),
        required_columns=tuple(schema_data["required_columns"]),
        source_timezone=str(dataset["source_timezone"]),
        session_timezone=str(dataset["session_timezone"]),
    )
    one_minute = load_one_minute_zip(source, schema)
    ledger = build_auction_state_ledger(
        str(dataset["instrument"]),
        one_minute,
        development_start=DEVELOPMENT_START,
        development_end=DEVELOPMENT_END,
    )
    if ledger.empty:
        raise RuntimeError("auction-state diagnostic produced no boundary events")
    if pd.to_datetime(ledger["trade_date"]).max() >= pd.Timestamp("2024-07-01"):
        raise RuntimeError("diagnostic opened the protected validation partition")
    output_root.mkdir(parents=True, exist_ok=True)
    ledger_path = output_root / "auction_state_ledger.csv"
    ledger.to_csv(ledger_path, index=False)
    sample = ledger.sort_values("event_id").head(50)
    sample.to_csv(output_root / "audit_sample_50.csv", index=False)
    summary = {
        "work_package": "AS-WP-20260723-08",
        "instrument": str(dataset["instrument"]),
        "source_instrument": str(dataset["source_instrument"]),
        "source_sha256": actual,
        "development_start": DEVELOPMENT_START.isoformat(),
        "development_end_exclusive": DEVELOPMENT_END.isoformat(),
        "rows": int(len(ledger)),
        "state_counts": {
            str(key): int(value)
            for key, value in ledger["state"].value_counts(dropna=False).items()
        },
        "sessions": {
            str(key): int(value)
            for key, value in ledger["session"].value_counts(dropna=False).items()
        },
        "pnl_calculated": False,
        "execution_simulated": False,
        "validation_partition_opened": False,
        "private_source_removed_before_upload": False,
    }
    (output_root / "instrument_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )
    typer.echo(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    app()
