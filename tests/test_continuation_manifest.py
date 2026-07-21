from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest
import yaml

from dtr_lab.research.continuation_manifest import (
    load_continuation_manifest,
    verify_continuation_dataset,
)


def _payload(dataset: str, digest: str) -> dict:
    return {
        "schema_version": 1,
        "run_id": "continuation_test",
        "dataset": {
            "path": dataset,
            "sha256": digest,
            "timestamp_semantics": "provisional_bar_open",
            "timezone_assumption": "America/New_York",
        },
        "periods": {
            "development_start": "2023-01-01T00:00:00",
            "development_end": "2024-07-01T00:00:00",
            "validation_end": "2025-04-01T00:00:00",
            "research_end": "2025-12-11T00:00:00",
        },
        "shared_config": {"acceptance_bars": 2, "entry_mode": "pullback"},
        "variants": [
            {"name": "BASE", "overrides": {}},
            {"name": "LATE60", "overrides": {"min_minutes_from_range_end": 60}},
        ],
        "execution": {"gap_policy": "reject_unsafe"},
    }


def test_continuation_manifest_builds_configs_and_verifies_dataset(tmp_path: Path) -> None:
    dataset = tmp_path / "sample.zip"
    dataset.write_bytes(b"fixture")
    digest = sha256(dataset.read_bytes()).hexdigest()
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(_payload(dataset.name, digest)), encoding="utf-8")

    manifest = load_continuation_manifest(manifest_path)
    configs = manifest.configs()

    assert [config.name for config in configs] == ["BASE", "LATE60"]
    assert configs[0].acceptance_bars == 2
    assert configs[1].min_minutes_from_range_end == 60
    assert verify_continuation_dataset(manifest, manifest_path) == dataset.resolve()


def test_continuation_manifest_rejects_unknown_config_field(tmp_path: Path) -> None:
    dataset = tmp_path / "sample.zip"
    dataset.write_bytes(b"fixture")
    digest = sha256(dataset.read_bytes()).hexdigest()
    payload = _payload(dataset.name, digest)
    payload["variants"][0]["overrides"]["imaginary_filter"] = True
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="Unknown ContinuationConfig fields"):
        load_continuation_manifest(manifest_path)
