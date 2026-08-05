from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Any


class CacheRestoreError(RuntimeError):
    """Raised when a private market-data archive cannot be verified or restored."""


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_registry(path: Path) -> dict[str, Any]:
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise CacheRestoreError(f"Registry not found: {path}") from error
    except json.JSONDecodeError as error:
        raise CacheRestoreError(f"Invalid registry JSON: {path}: {error}") from error
    if registry.get("status") != "CANONICAL_ACTIVE_PRIVATE_CACHE":
        raise CacheRestoreError("Registry is not active; stop before using data.")
    if not isinstance(registry.get("pairs"), dict):
        raise CacheRestoreError("Registry does not contain a valid pairs mapping.")
    return registry


def pair_entry(registry: dict[str, Any], pair: str) -> dict[str, Any]:
    normalized = pair.upper().strip()
    try:
        return registry["pairs"][normalized]
    except KeyError as error:
        available = ", ".join(sorted(registry["pairs"]))
        raise CacheRestoreError(f"Pair {normalized!r} is not registered. Available: {available}") from error


def verify_parts(parts_dir: Path, entry: dict[str, Any]) -> list[Path]:
    if not parts_dir.is_dir():
        raise CacheRestoreError(f"Parts directory does not exist: {parts_dir}")
    verified: list[Path] = []
    for part in entry["parts"]:
        path = parts_dir / part["file"]
        if not path.is_file():
            raise CacheRestoreError(f"Missing registered part: {path}")
        if path.stat().st_size != int(part["size_bytes"]):
            raise CacheRestoreError(f"Size mismatch for {path.name}")
        actual_sha = sha256_file(path)
        if actual_sha.lower() != str(part["sha256"]).lower():
            raise CacheRestoreError(f"SHA-256 mismatch for {path.name}")
        verified.append(path)
    return verified


def reconstruct_archive(parts_dir: Path, output: Path, entry: dict[str, Any], *, overwrite: bool = False) -> Path:
    parts = verify_parts(parts_dir, entry)
    if output.exists() and not overwrite:
        if sha256_file(output) == entry["archive_sha256"]:
            return output
        raise CacheRestoreError(f"Output already exists with a different checksum: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".partial")
    if temporary.exists():
        temporary.unlink()
    try:
        with temporary.open("wb") as destination:
            for part in parts:
                with part.open("rb") as source:
                    shutil.copyfileobj(source, destination, length=1024 * 1024)
        if temporary.stat().st_size != int(entry["archive_size_bytes"]):
            raise CacheRestoreError("Reconstructed archive size mismatch")
        actual_sha = sha256_file(temporary)
        if actual_sha.lower() != str(entry["archive_sha256"]).lower():
            raise CacheRestoreError("Reconstructed archive SHA-256 mismatch")
        if output.exists():
            output.unlink()
        temporary.replace(output)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise
    return output


def _safe_member_target(root: Path, member_name: str) -> Path:
    target = (root / member_name).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as error:
        raise CacheRestoreError(f"Unsafe archive member: {member_name}") from error
    return target


def extract_verified_archive(archive: Path, extract_to: Path) -> None:
    extract_to.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            _safe_member_target(extract_to, member.filename)
        bundle.extractall(extract_to)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify and restore a registered private Dukascopy archive.")
    parser.add_argument("--registry", type=Path, default=Path("data/private_market_data_cache_registry.json"))
    parser.add_argument("--pair", required=True)
    parser.add_argument("--parts-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--extract-to", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--verify-parts-only", action="store_true")
    args = parser.parse_args()
    try:
        registry = load_registry(args.registry)
        entry = pair_entry(registry, args.pair)
        parts = verify_parts(args.parts_dir, entry)
        print(f"Verified {len(parts)} parts for {args.pair.upper()}.")
        if args.verify_parts_only:
            return 0
        archive = reconstruct_archive(args.parts_dir, args.output, entry, overwrite=args.overwrite)
        print(f"Restored and verified archive: {archive}")
        print(f"SHA-256: {entry['archive_sha256']}")
        if args.extract_to is not None:
            extract_verified_archive(archive, args.extract_to)
            print(f"Extracted verified archive to: {args.extract_to}")
        return 0
    except CacheRestoreError as error:
        print(f"CACHE RESTORE FAILED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
