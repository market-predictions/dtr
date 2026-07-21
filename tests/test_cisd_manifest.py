from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest
import yaml

from dtr_lab.research.cisd_manifest import load_cisd_manifest, verify_cisd_dataset


def _payload(dataset_path: str, digest: str) -> dict:
    return {
        "schema_version": 1,
        "run_id": "cisd_test",
        "candidate_name": "frozen_reversal",
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
        "strategy": {"sessions": ["LONDON_2AM"], "weekdays": [1, 2, 3, 4]},
        "variants": [
            {"name": "observe", "policy": "observe"},
            {"name": "retest", "policy": "sequence_retest"},
        ],
        "execution": {"gap_policy": "reject_unsafe"},
    }


def test_cisd_manifest_loads_and_verifies_dataset(tmp_path: Path) -> None:
    dataset = tmp_path / "sample.zip"
    dataset.write_bytes(b"deterministic fixture")
    digest = sha256(dataset.read_bytes()).hexdigest()
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(_payload(dataset.name, digest)), encoding="utf-8")

    manifest = load_cisd_manifest(path)

    assert manifest.strategy_config().sessions == ("LONDON_2AM",)
    assert [variant.policy for variant in manifest.variant_configs()] == [
        "observe",
        "sequence_retest",
    ]
    assert verify_cisd_dataset(manifest, path) == dataset.resolve()


def test_cisd_manifest_requires_exactly_one_observe_variant(tmp_path: Path) -> None:
    payload = _payload("sample.zip", "0" * 64)
    payload["variants"] = [{"name": "retest", "policy": "sequence_retest"}]
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="Exactly one observe"):
        load_cisd_manifest(path)


def test_cisd_manifest_rejects_unknown_strategy_field(tmp_path: Path) -> None:
    payload = _payload("sample.zip", "0" * 64)
    payload["strategy"]["future_leak"] = True
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="Unknown StrategyConfig fields"):
        load_cisd_manifest(path)
