from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import typer
import yaml

from dtr_lab.strategies.asia_sweep.cluster_challenger import (
    ClusterExecutionConfig,
    build_cluster_signal_ledger,
    simulate_cluster_signal,
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
    """Run the frozen London PDH/PDL cluster challenger on development data."""

    manifest = _load_yaml(manifest_path)
    dataset = manifest["dataset"]
    periods = manifest["periods"]
    if pd.Timestamp(periods["development_start"]) != pd.Timestamp("2023-01-01"):
        raise typer.BadParameter("development_start differs from frozen cluster study")
    if pd.Timestamp(periods["development_end"]) != pd.Timestamp("2024-07-01"):
        raise typer.BadParameter("development_end differs from frozen cluster study")
    if dataset["source_kind"] != "DUKASCOPY_INDEX_CFD_PROXY":
        raise typer.BadParameter("cluster study requires the registered Dukascopy proxy")
    if dataset["session_timezone"] != "America/New_York":
        raise typer.BadParameter("cluster study requires America/New_York session time")
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
    signals, audit, funnel = build_cluster_signal_ledger(
        str(dataset["instrument"]), one_minute
    )
    cfg = ClusterExecutionConfig(
        instrument=str(dataset["instrument"]),
        source_instrument=str(dataset["source_instrument"]),
        point_value=float(dataset["point_value"]),
        commission_per_side=float(dataset["commission_per_side"]),
    )
    executions = pd.DataFrame(
        [simulate_cluster_signal(row, one_minute, cfg) for _, row in signals.iterrows()]
    )
    if executions.empty:
        executions = pd.DataFrame(
            columns=[
                "event_id", "instrument", "trade_date", "status", "reason",
                "entry_timestamp", "net_r", "gross_r", "planned_reward_r"
            ]
        )
    output_root.mkdir(parents=True, exist_ok=True)
    signals.to_csv(output_root / "cluster_signal_ledger.csv", index=False)
    audit.to_csv(output_root / "cluster_audit_ledger.csv", index=False)
    executions.to_csv(output_root / "cluster_execution_ledger.csv", index=False)
    summary = {
        "work_package": "AS-WP-20260723-09",
        "instrument": str(dataset["instrument"]),
        "source_instrument": str(dataset["source_instrument"]),
        "source_sha256": actual,
        "signals": int(len(signals)),
        "executions": int(len(executions)),
        "exited": int((executions.get("status", pd.Series(dtype=str)) == "EXITED").sum()),
        "blocked": int((executions.get("status", pd.Series(dtype=str)) == "BLOCKED").sum()),
        "unresolved": int((executions.get("status", pd.Series(dtype=str)) == "UNRESOLVED").sum()),
        "funnel": funnel,
        "development_end_exclusive": "2024-07-01",
        "validation_partition_opened": False,
        "private_source_removed_before_upload": False,
    }
    (output_root / "instrument_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )
    typer.echo(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    app()
