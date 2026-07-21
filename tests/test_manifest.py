from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest
import yaml

from dtr_lab.research.manifest import load_manifest, verify_dataset


def _payload(dataset_path: str, digest: str) -> dict:
    return {
        "schema_version": 1,
        "run_id": "test_run",
        "candidate_name": "test_candidate",
        "dataset": {
            "path": dataset_path,
            "sha256": digest,
            "timestamp_semantics": "provisional_bar_open",
            "timezone_assumption": "America/New_York",
            "drop_incomplete_final_date": True,
        },
        "periods": {
            "development_start": "2023-01-01T00:00:00",
            "development_end": "2024-01-01T00:00:00",
            "validation_end": "2025-01-01T00:00:00",
            "research_end": "2025-12-01T00:00:00",
        },
        "strategy": {
            "sessions": ["LONDON_2AM"],
            "weekdays": [1, 2, 3, 4],
            "pivot_len": 2,
        },
        "execution": {
            "intrabar_source": "1min",
            "same_minute_collision_policy": "conservative_stop_first",
            "random_seed": 7,
            "gap_policy": "reject_unsafe",
        },
    }


def test_manifest_loads_strategy_and_verifies_dataset(tmp_path: Path) -> None:
    dataset = tmp_path / "sample.zip"
    dataset.write_bytes(b"deterministic fixture")
    digest = sha256(dataset.read_bytes()).hexdigest()
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(_payload(dataset.name, digest)), encoding="utf-8"
    )

    manifest = load_manifest(manifest_path)
    config = manifest.strategy_config()

    assert config.name == "test_candidate"
    assert config.sessions == ("LONDON_2AM",)
    assert config.weekdays == (1, 2, 3, 4)
    assert config.pivot_len == 2
    assert manifest.execution.gap_policy == "reject_unsafe"
    assert verify_dataset(manifest, manifest_path) == dataset.resolve()


def test_manifest_defaults_legacy_runs_to_observe_only(tmp_path: Path) -> None:
    dataset = tmp_path / "sample.zip"
    dataset.write_bytes(b"fixture")
    digest = sha256(dataset.read_bytes()).hexdigest()
    payload = _payload(dataset.name, digest)
    del payload["execution"]["gap_policy"]
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    manifest = load_manifest(manifest_path)

    assert manifest.execution.gap_policy == "observe_only"


def test_manifest_rejects_unknown_gap_policy(tmp_path: Path) -> None:
    dataset = tmp_path / "sample.zip"
    dataset.write_bytes(b"fixture")
    digest = sha256(dataset.read_bytes()).hexdigest()
    payload = _payload(dataset.name, digest)
    payload["execution"]["gap_policy"] = "silently_fill_gaps"
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="gap_policy"):
        load_manifest(manifest_path)


def test_manifest_rejects_unknown_strategy_field(tmp_path: Path) -> None:
    dataset = tmp_path / "sample.zip"
    dataset.write_bytes(b"fixture")
    digest = sha256(dataset.read_bytes()).hexdigest()
    payload = _payload(dataset.name, digest)
    payload["strategy"]["imaginary_gate"] = 123
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="Unknown StrategyConfig fields"):
        load_manifest(manifest_path)


def test_manifest_rejects_checksum_mismatch(tmp_path: Path) -> None:
    dataset = tmp_path / "sample.zip"
    dataset.write_bytes(b"fixture")
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(_payload(dataset.name, "0" * 64)), encoding="utf-8"
    )
    manifest = load_manifest(manifest_path)

    with pytest.raises(ValueError, match="Dataset checksum mismatch"):
        verify_dataset(manifest, manifest_path)
