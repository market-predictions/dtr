from __future__ import annotations

from dataclasses import fields
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal

import pandas as pd
import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .engine import StrategyConfig


class DatasetSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    sha256: str = Field(min_length=64, max_length=64)
    timestamp_semantics: str
    timezone_assumption: str
    drop_incomplete_final_date: bool = True

    @field_validator("sha256")
    @classmethod
    def normalize_hash(cls, value: str) -> str:
        normalized = value.strip().lower()
        if any(char not in "0123456789abcdef" for char in normalized):
            raise ValueError("sha256 must be a lowercase hexadecimal digest")
        return normalized


class PeriodSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    development_start: datetime
    development_end: datetime
    validation_end: datetime
    research_end: datetime

    @model_validator(mode="after")
    def validate_order(self) -> "PeriodSpec":
        values = (
            self.development_start,
            self.development_end,
            self.validation_end,
            self.research_end,
        )
        if list(values) != sorted(values) or len(set(values)) != len(values):
            raise ValueError("Research periods must be strictly increasing")
        return self


class ExecutionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intrabar_source: str = "1min"
    same_minute_collision_policy: str = "conservative_stop_first"
    random_seed: int = 20260721
    gap_policy: Literal["observe_only", "reject_unsafe"] = "observe_only"


class ExpectedBaseline(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trades: int
    net_r: float
    max_drawdown_r: float
    tolerance_trades: int = 0
    tolerance_net_r: float = 1e-9
    tolerance_max_drawdown_r: float = 1e-9


class ResearchManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    run_id: str
    candidate_name: str
    dataset: DatasetSpec
    periods: PeriodSpec
    strategy: dict[str, Any]
    execution: ExecutionSpec = Field(default_factory=ExecutionSpec)
    expected_baseline: ExpectedBaseline | None = None

    @field_validator("strategy")
    @classmethod
    def validate_strategy_keys(cls, value: dict[str, Any]) -> dict[str, Any]:
        allowed = {field.name for field in fields(StrategyConfig)}
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError(f"Unknown StrategyConfig fields: {unknown}")
        return value

    def strategy_config(self) -> StrategyConfig:
        payload = {**self.strategy, "name": self.candidate_name}
        for tuple_field in ("sessions", "weekdays"):
            if tuple_field in payload and isinstance(payload[tuple_field], list):
                payload[tuple_field] = tuple(payload[tuple_field])
        return StrategyConfig(**payload)

    @property
    def development_end(self) -> pd.Timestamp:
        return pd.Timestamp(self.periods.development_end)

    @property
    def validation_end(self) -> pd.Timestamp:
        return pd.Timestamp(self.periods.validation_end)

    @property
    def research_end(self) -> pd.Timestamp:
        return pd.Timestamp(self.periods.research_end)


def load_manifest(path: str | Path) -> ResearchManifest:
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Research manifest root must be a mapping")
    return ResearchManifest.model_validate(payload)


def file_sha256(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_dataset_path(manifest_path: str | Path, dataset_path: str) -> Path:
    candidate = Path(dataset_path).expanduser()
    if candidate.is_absolute():
        return candidate
    return (Path(manifest_path).resolve().parent / candidate).resolve()


def verify_dataset(manifest: ResearchManifest, manifest_path: str | Path) -> Path:
    path = resolve_dataset_path(manifest_path, manifest.dataset.path)
    if not path.exists():
        raise FileNotFoundError(path)
    actual = file_sha256(path)
    if actual != manifest.dataset.sha256:
        raise ValueError(
            f"Dataset checksum mismatch for {path}: expected "
            f"{manifest.dataset.sha256}, received {actual}"
        )
    return path
