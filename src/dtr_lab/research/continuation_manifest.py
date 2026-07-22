from __future__ import annotations

from dataclasses import fields, replace
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .continuation import ContinuationConfig
from .manifest import DatasetSpec, PeriodSpec, file_sha256, resolve_dataset_path


class ContinuationVariantSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    overrides: dict[str, Any] = Field(default_factory=dict)

    @field_validator("overrides")
    @classmethod
    def validate_override_keys(cls, value: dict[str, Any]) -> dict[str, Any]:
        allowed = {field.name for field in fields(ContinuationConfig)} - {"name"}
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError(f"Unknown ContinuationConfig fields: {unknown}")
        return value


class ContinuationExecutionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intrabar_source: Literal["1min"] = "1min"
    same_minute_collision_policy: Literal["conservative_stop_first"] = (
        "conservative_stop_first"
    )
    random_seed: int = 20260721
    gap_policy: Literal["reject_unsafe", "liquidate_unsafe"] = "liquidate_unsafe"


class ContinuationManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    run_id: str
    dataset: DatasetSpec
    periods: PeriodSpec
    shared_config: dict[str, Any] = Field(default_factory=dict)
    variants: list[ContinuationVariantSpec]
    execution: ContinuationExecutionSpec = Field(default_factory=ContinuationExecutionSpec)

    @field_validator("shared_config")
    @classmethod
    def validate_shared_keys(cls, value: dict[str, Any]) -> dict[str, Any]:
        allowed = {field.name for field in fields(ContinuationConfig)} - {"name"}
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError(f"Unknown ContinuationConfig fields: {unknown}")
        return value

    @model_validator(mode="after")
    def validate_variants(self) -> ContinuationManifest:
        if not self.variants:
            raise ValueError("At least one continuation variant is required")
        names = [variant.name for variant in self.variants]
        if len(names) != len(set(names)):
            raise ValueError("Continuation variant names must be unique")
        return self

    def configs(self) -> list[ContinuationConfig]:
        base_payload = dict(self.shared_config)
        for tuple_field in ("sessions", "weekdays"):
            if tuple_field in base_payload and isinstance(base_payload[tuple_field], list):
                base_payload[tuple_field] = tuple(base_payload[tuple_field])
        base = ContinuationConfig(**base_payload)
        configs: list[ContinuationConfig] = []
        for variant in self.variants:
            overrides = dict(variant.overrides)
            for tuple_field in ("sessions", "weekdays"):
                if tuple_field in overrides and isinstance(overrides[tuple_field], list):
                    overrides[tuple_field] = tuple(overrides[tuple_field])
            configs.append(replace(base, name=variant.name, **overrides))
        return configs


def load_continuation_manifest(path: str | Path) -> ContinuationManifest:
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Continuation manifest root must be a mapping")
    return ContinuationManifest.model_validate(payload)


def verify_continuation_dataset(
    manifest: ContinuationManifest,
    manifest_path: str | Path,
) -> Path:
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
