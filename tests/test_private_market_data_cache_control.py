# ruff: noqa: I001
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "private_market_data_cache_registry.json"
EXPECTED_PAIRS = {
    "EURUSD",
    "GBPUSD",
    "USDCHF",
    "AUDUSD",
    "NZDUSD",
    "USDCAD",
    "USDJPY",
    "EURJPY",
    "GBPJPY",
    "EURGBP",
}
CONTROL_MARKER = "CACHE-FIRST CONTROL"
CANONICAL_FOLDER_ID = "160qGdjm9Gi6pr05nRHuUXaTZc9EgJOOU"
DUKASCOPY_ENDPOINT_TOKENS = ("datafeed.dukascopy.com", "dukascopy-node")


def test_private_cache_registry_is_complete_and_active() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert registry["status"] == "CANONICAL_ACTIVE_PRIVATE_CACHE"
    assert registry["canonical_storage"]["dataset_folder_id"] == CANONICAL_FOLDER_ID
    assert set(registry["pairs"]) == EXPECTED_PAIRS
    for pair, entry in registry["pairs"].items():
        assert entry["drive_folder_id"]
        assert entry["archive_size_bytes"] > 100_000_000
        assert re.fullmatch(r"[0-9a-f]{64}", entry["archive_sha256"])
        assert 2 <= len(entry["parts"]) <= 3
        assert sum(part["size_bytes"] for part in entry["parts"]) == entry[
            "archive_size_bytes"
        ]
        for part in entry["parts"]:
            assert part["file"].startswith(pair)
            assert re.fullmatch(r"[0-9a-f]{64}", part["sha256"])


def test_cache_first_control_is_prominent() -> None:
    control_files = (
        "AGENTS.md",
        "REPOSITORY_CONTROL.md",
        "README.md",
        "STATUS.md",
    )
    for relative_path in control_files:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        first_lines = "\n".join(text.splitlines()[:30])
        assert CONTROL_MARKER in first_lines, relative_path
        assert CANONICAL_FOLDER_ID in first_lines, relative_path


def test_catalog_and_runbook_point_to_registry() -> None:
    catalog = (ROOT / "data" / "catalog.yaml").read_text(encoding="utf-8")
    runbook = (
        ROOT / "docs" / "PERMANENT_MARKET_DATA_CACHE.md"
    ).read_text(encoding="utf-8")
    assert "private_market_data_cache_registry.json" in catalog
    assert CANONICAL_FOLDER_ID in catalog
    assert CANONICAL_FOLDER_ID in runbook
    assert "restore_private_market_data_cache.py" in runbook


def test_new_dukascopy_downloaders_require_explicit_cache_miss_authorization() -> None:
    candidates = list((ROOT / "scripts").rglob("*.py"))
    candidates += list((ROOT / ".github" / "workflows").rglob("*.yml"))
    candidates += list((ROOT / ".github" / "workflows").rglob("*.yaml"))
    violations: list[str] = []
    for path in candidates:
        text = path.read_text(encoding="utf-8")
        if not any(token in text for token in DUKASCOPY_ENDPOINT_TOKENS):
            continue
        has_authorization = "CACHE_MISS_AUTHORIZATION:" in text
        references_registry = "private_market_data_cache_registry.json" in text
        if not has_authorization or not references_registry:
            violations.append(str(path.relative_to(ROOT)))
    message = (
        "Dukascopy acquisition code bypasses permanent cache control: "
        + ", ".join(violations)
    )
    assert not violations, message
