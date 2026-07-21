from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from dtr_lab.research.artifacts import (
    halfyear_metrics,
    normalize_trades,
    verify_expected_baseline,
)
from dtr_lab.research.manifest import load_manifest


def _manifest(tmp_path: Path, expected: dict | None = None):
    dataset = tmp_path / "data.zip"
    dataset.write_bytes(b"fixture")
    payload = {
        "schema_version": 1,
        "run_id": "artifact_test",
        "candidate_name": "artifact_candidate",
        "dataset": {
            "path": dataset.name,
            "sha256": "0" * 64,
            "timestamp_semantics": "provisional_bar_open",
            "timezone_assumption": "America/New_York",
        },
        "periods": {
            "development_start": "2023-01-01T00:00:00",
            "development_end": "2024-01-01T00:00:00",
            "validation_end": "2025-01-01T00:00:00",
            "research_end": "2026-01-01T00:00:00",
        },
        "strategy": {},
    }
    if expected is not None:
        payload["expected_baseline"] = expected
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return load_manifest(path)


def test_normalize_empty_trades_has_required_columns() -> None:
    frame = normalize_trades(pd.DataFrame())
    assert "entry_time" in frame.columns
    assert "pnl_r" in frame.columns
    assert frame.empty


def test_halfyear_metrics_uses_calendar_half_labels() -> None:
    trades = pd.DataFrame(
        {
            "entry_time": pd.to_datetime(["2024-02-01", "2024-08-01"]),
            "exit_time": pd.to_datetime(["2024-02-01", "2024-08-01"]),
            "pnl_r": [1.0, -0.5],
            "holding_minutes": [5, 5],
            "mfe_r": [1.0, 0.2],
            "mae_r": [0.1, 0.5],
        }
    )
    output = halfyear_metrics(trades)
    assert output["period"].tolist() == ["2024H1", "2024H2"]


def test_expected_baseline_passes_within_tolerance(tmp_path: Path) -> None:
    manifest = _manifest(
        tmp_path,
        {
            "trades": 10,
            "net_r": 2.5,
            "max_drawdown_r": 1.25,
            "tolerance_trades": 0,
            "tolerance_net_r": 0.01,
            "tolerance_max_drawdown_r": 0.01,
        },
    )
    verify_expected_baseline(
        {"trades": 10, "net_r": 2.505, "max_drawdown_r": 1.255}, manifest
    )


def test_expected_baseline_fails_outside_tolerance(tmp_path: Path) -> None:
    manifest = _manifest(
        tmp_path,
        {
            "trades": 10,
            "net_r": 2.5,
            "max_drawdown_r": 1.25,
        },
    )
    with pytest.raises(AssertionError, match="Baseline regression failed"):
        verify_expected_baseline(
            {"trades": 9, "net_r": 2.0, "max_drawdown_r": 2.0}, manifest
        )
