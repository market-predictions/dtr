from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import pytest


def _load_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "restore_private_market_data_cache.py"
    spec = importlib.util.spec_from_file_location("restore_private_cache", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _entry(parts: list[tuple[str, bytes]], archive: bytes) -> dict:
    return {
        "archive_size_bytes": len(archive),
        "archive_sha256": _sha(archive),
        "parts": [
            {"file": name, "size_bytes": len(payload), "sha256": _sha(payload)}
            for name, payload in parts
        ],
    }


def test_reconstructs_registered_archive(tmp_path: Path) -> None:
    module = _load_module()
    archive = b"0123456789abcdef"
    parts = [("pair.zip.part-000", archive[:7]), ("pair.zip.part-001", archive[7:])]
    for name, payload in parts:
        (tmp_path / name).write_bytes(payload)
    output = tmp_path / "archive.zip"
    result = module.reconstruct_archive(tmp_path, output, _entry(parts, archive))
    assert result == output
    assert output.read_bytes() == archive
    assert module.sha256_file(output) == _sha(archive)


def test_rejects_corrupt_part(tmp_path: Path) -> None:
    module = _load_module()
    archive = b"registered archive"
    parts = [("pair.zip.part-000", archive)]
    (tmp_path / parts[0][0]).write_bytes(b"corrupt archive")
    with pytest.raises(module.CacheRestoreError, match="Size mismatch|SHA-256 mismatch"):
        module.verify_parts(tmp_path, _entry(parts, archive))


def test_safe_extract_rejects_path_traversal(tmp_path: Path) -> None:
    module = _load_module()
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("../escape.txt", "not allowed")
    with pytest.raises(module.CacheRestoreError, match="Unsafe archive member"):
        module.extract_verified_archive(archive, tmp_path / "extract")


def test_registry_requires_active_status(tmp_path: Path) -> None:
    module = _load_module()
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({"status": "RETIRED", "pairs": {}}), encoding="utf-8")
    with pytest.raises(module.CacheRestoreError, match="not active"):
        module.load_registry(registry)
