from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from .data import file_sha256, validate_one_minute


def load_design(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Validation design must be a mapping")
    return payload


def _partition_contract(design: dict[str, object], partition: str) -> dict[str, object]:
    source = design.get("source_contract")
    if not isinstance(source, dict):
        raise ValueError("source_contract must be a mapping")
    partitions = source.get("partitions")
    if not isinstance(partitions, dict):
        raise ValueError("source partitions must be a mapping")
    contract = partitions.get(partition)
    if not isinstance(contract, dict):
        raise ValueError(f"Missing source partition: {partition}")
    return contract


def _source_path(source_dir: Path, *, prefix: str, label: str) -> Path:
    matches = sorted(source_dir.rglob(f"{prefix}_{label}.csv.gz"))
    if len(matches) != 1:
        raise ValueError(
            f"Expected one source file for {prefix} {label}, found {len(matches)}"
        )
    return matches[0]


def load_partition(
    source_dir: Path,
    design: dict[str, object],
    partition: str,
    *,
    filename_prefix: str,
) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    contract = _partition_contract(design, partition)
    labels = contract.get("labels")
    hashes = contract.get("expected_sha256_by_label")
    if not isinstance(labels, list) or not isinstance(hashes, dict):
        raise ValueError(f"Invalid source contract for {partition}")

    frames: list[pd.DataFrame] = []
    audits: list[dict[str, object]] = []
    for raw_label in labels:
        label = str(raw_label)
        expected = str(hashes.get(raw_label, hashes.get(label, "")))
        if len(expected) != 64 or "PENDING" in expected:
            raise ValueError(f"Source hash is not frozen for {label}")
        path = _source_path(source_dir, prefix=filename_prefix, label=label)
        observed = file_sha256(path)
        if observed != expected:
            raise ValueError(f"Source checksum mismatch for {label}")
        raw = pd.read_csv(path, compression="gzip")
        required = {
            "timestamp UTC",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "is_active_quote",
        }
        missing = required.difference(raw.columns)
        if missing:
            raise ValueError(f"Source {label} missing columns: {sorted(missing)}")
        active = pd.to_numeric(raw["is_active_quote"], errors="raise").astype(bool)
        frame = raw.loc[
            active,
            ["timestamp UTC", "open", "high", "low", "close", "volume"],
        ].rename(columns={"timestamp UTC": "timestamp"})
        frame["timestamp"] = pd.to_datetime(
            frame["timestamp"], utc=True, errors="raise"
        ).dt.tz_localize(None)
        frame = validate_one_minute(frame)
        frames.append(frame)
        audits.append(
            {
                "partition": partition,
                "label": label,
                "sha256": observed,
                "rows": int(len(frame)),
                "start": pd.Timestamp(frame["timestamp"].min()).isoformat(),
                "end": pd.Timestamp(frame["timestamp"].max()).isoformat(),
                "duplicate_timestamps": int(frame["timestamp"].duplicated().sum()),
            }
        )

    combined = validate_one_minute(pd.concat(frames, ignore_index=True))
    expected_start = pd.Timestamp(str(contract["start_inclusive_utc"]))
    expected_end = pd.Timestamp(str(contract["end_exclusive_utc"]))
    observed_start = pd.Timestamp(combined["timestamp"].min())
    observed_end = pd.Timestamp(combined["timestamp"].max())
    if observed_start < expected_start or observed_end >= expected_end:
        raise ValueError(
            f"Partition {partition} outside frozen bounds: "
            f"{observed_start} through {observed_end}"
        )
    if combined["timestamp"].duplicated().any():
        raise ValueError(f"Partition {partition} contains duplicate timestamps")
    return combined, audits
