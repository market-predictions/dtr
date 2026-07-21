from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .engine import StrategyConfig
from .ifvg import IFVGPolicy, IFVGVariant
from .manifest import DatasetSpec, ExpectedBaseline, PeriodSpec, file_sha256, resolve_dataset_path


class IFVGVariantSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    policy: IFVGPolicy


class IFVGExecutionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intrabar_source: Literal["1min"] = "1min"
    same_minute_collision_policy: Literal["conservative_stop_first"] = (
        "conservative_stop_first"
    )
    random_seed: int = 20260721
    gap_policy: Literal["reject_unsafe"] = "reject_unsafe"


class IFVGManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    run_id: str
    candidate_name: str
    dataset: DatasetSpec
    periods: PeriodSpec
    strategy: dict[str, Any]
    variants: list[IFVGVariantSpec]
    execution: IFVGExecutionSpec = Field(default_factory=IFVGExecutionSpec)
    expected_observe: ExpectedBaseline | None = None

    @field_validator("strategy")
    @classmethod
    def validate_strategy_keys(cls, value: dict[str, Any]) -> dict[str, Any]:
        allowed = {field.name for field in fields(StrategyConfig)}
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError(f"Unknown StrategyConfig fields: {unknown}")
        return value

    @model_validator(mode="after")
    def validate_variants(self) -> IFVGManifest:
        if not self.variants:
            raise ValueError("At least one IFVG variant is required")
        names = [variant.name for variant in self.variants]
        if len(names) != len(set(names)):
            raise ValueError("IFVG variant names must be unique")
        observe = [variant for variant in self.variants if variant.policy == "observe"]
        if len(observe) != 1:
            raise ValueError("Exactly one observe IFVG variant is required")
        return self

    def strategy_config(self) -> StrategyConfig:
        payload = {**self.strategy, "name": self.candidate_name}
        for tuple_field in ("sessions", "weekdays"):
            if tuple_field in payload and isinstance(payload[tuple_field], list):
                payload[tuple_field] = tuple(payload[tuple_field])
        return StrategyConfig(**payload)

    def variant_configs(self) -> list[IFVGVariant]:
        return [IFVGVariant(variant.name, variant.policy) for variant in self.variants]


def load_ifvg_manifest(path: str | Path) -> IFVGManifest:
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError("IFVG manifest root must be a mapping")
    return IFVGManifest.model_validate(payload)


def verify_ifvg_dataset(manifest: IFVGManifest, manifest_path: str | Path) -> Path:
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
