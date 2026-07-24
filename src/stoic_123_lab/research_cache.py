from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable
from dataclasses import asdict, is_dataclass
from pathlib import Path

import pandas as pd

CACHE_SCHEMA_VERSION = 1


def _canonical(value: object) -> object:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, dict):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def cache_key(namespace: str, components: dict[str, object]) -> str:
    payload = {
        "schema_version": CACHE_SCHEMA_VERSION,
        "namespace": namespace,
        "components": _canonical(components),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


class FrameCache:
    def __init__(self, root: Path, *, enabled: bool = True) -> None:
        self.root = root
        self.enabled = enabled
        self.hits = 0
        self.misses = 0

    def _paths(self, namespace: str, key: str) -> tuple[Path, Path]:
        directory = self.root / namespace
        return directory / f"{key}.parquet", directory / f"{key}.json"

    def get_or_build(
        self,
        namespace: str,
        components: dict[str, object],
        builder: Callable[[], pd.DataFrame],
    ) -> tuple[pd.DataFrame, bool, str]:
        key = cache_key(namespace, components)
        data_path, metadata_path = self._paths(namespace, key)
        if self.enabled and data_path.exists() and metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata.get("key") != key:
                raise ValueError(f"cache metadata key mismatch: {metadata_path}")
            frame = pd.read_parquet(data_path)
            if int(metadata.get("rows", -1)) != len(frame):
                raise ValueError(f"cache row-count mismatch: {data_path}")
            self.hits += 1
            return frame, True, key

        frame = builder()
        if not isinstance(frame, pd.DataFrame):
            raise TypeError("frame cache builders must return a pandas DataFrame")
        self.misses += 1
        if not self.enabled:
            return frame, False, key

        data_path.parent.mkdir(parents=True, exist_ok=True)
        temp_data = data_path.with_suffix(f".tmp-{os.getpid()}.parquet")
        temp_meta = metadata_path.with_suffix(f".tmp-{os.getpid()}.json")
        frame.to_parquet(temp_data, index=False)
        metadata = {
            "key": key,
            "namespace": namespace,
            "schema_version": CACHE_SCHEMA_VERSION,
            "rows": int(len(frame)),
            "columns": [str(column) for column in frame.columns],
            "components": _canonical(components),
        }
        temp_meta.write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temp_data, data_path)
        os.replace(temp_meta, metadata_path)
        return frame, False, key

    def summary(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "root": str(self.root),
            "hits": self.hits,
            "misses": self.misses,
        }
