from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import yaml

from .config import SequenceConfig

_NON_DETECTION_FIELDS = frozenset(
    {
        "arm_id",
        "description",
        "fill_mode",
        "stop_buffer_ticks",
        "minimum_risk_ticks",
        "max_hold_minutes",
        "slippage_ticks_each_side",
    }
)
_PROTECTED_OVERRIDE_FIELDS = frozenset({"arm_id", "description"})
_ALLOWED_OVERRIDE_FIELDS = frozenset(SequenceConfig.__dataclass_fields__).difference(
    _PROTECTED_OVERRIDE_FIELDS
)


@dataclass(frozen=True)
class VariationSpec:
    variation_id: str
    description: str
    overrides: dict[str, object]


@dataclass(frozen=True)
class BatchDesign:
    study_id: str
    status: str
    source_partition: str
    variations: tuple[VariationSpec, ...]
    promotion_authorized: bool
    holdout_access_authorized: bool

    def validate(self, *, allowed_partitions: set[str]) -> None:
        if self.status != "DISCOVERY_ONLY":
            raise ValueError("batch studies must remain DISCOVERY_ONLY")
        if self.promotion_authorized:
            raise ValueError("batch screening cannot authorize promotion")
        if self.holdout_access_authorized:
            raise ValueError("batch screening cannot access holdout data")
        if self.source_partition not in allowed_partitions:
            raise ValueError(f"batch source partition is not allowed: {self.source_partition}")
        if not self.variations:
            raise ValueError("batch design requires at least one variation")
        identifiers = [variation.variation_id for variation in self.variations]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("batch variation IDs must be unique")
        for variation in self.variations:
            if not variation.variation_id.strip():
                raise ValueError("variation_id cannot be empty")
            unknown = set(variation.overrides).difference(_ALLOWED_OVERRIDE_FIELDS)
            if unknown:
                raise ValueError(
                    f"variation {variation.variation_id} has unsupported overrides: "
                    f"{sorted(unknown)}"
                )


def load_batch_design(
    path: str | Path,
    *,
    allowed_partitions: set[str],
    max_variations: int = 250,
) -> BatchDesign:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("batch design must be a mapping")
    raw_variations = payload.get("variations")
    if not isinstance(raw_variations, list):
        raise ValueError("batch design variations must be a list")
    if len(raw_variations) > max_variations:
        raise ValueError(
            f"batch contains {len(raw_variations)} variations; maximum is {max_variations}"
        )
    variations: list[VariationSpec] = []
    for raw in raw_variations:
        if not isinstance(raw, dict):
            raise ValueError("each batch variation must be a mapping")
        overrides = raw.get("overrides", {})
        if not isinstance(overrides, dict):
            raise ValueError("variation overrides must be a mapping")
        variations.append(
            VariationSpec(
                variation_id=str(raw.get("id", "")),
                description=str(raw.get("description", raw.get("id", ""))),
                overrides=dict(overrides),
            )
        )
    design = BatchDesign(
        study_id=str(payload.get("study_id", "")),
        status=str(payload.get("status", "")),
        source_partition=str(payload.get("source_partition", "")),
        variations=tuple(variations),
        promotion_authorized=bool(payload.get("promotion_authorized", False)),
        holdout_access_authorized=bool(payload.get("holdout_access_authorized", False)),
    )
    design.validate(allowed_partitions=allowed_partitions)
    return design


def apply_variation(base: SequenceConfig, variation: VariationSpec) -> SequenceConfig:
    config = replace(
        base,
        arm_id=f"{base.arm_id}__BATCH__{variation.variation_id}",
        description=variation.description,
        **variation.overrides,
    )
    config.validate()
    return config


def _signature(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def full_config_signature(config: SequenceConfig) -> str:
    payload = asdict(config)
    payload.pop("arm_id")
    payload.pop("description")
    return _signature(payload)


def detection_signature(config: SequenceConfig) -> str:
    payload = {
        key: value
        for key, value in asdict(config).items()
        if key not in _NON_DETECTION_FIELDS
    }
    return _signature(payload)


def group_variations_by_detection(
    base: SequenceConfig,
    variations: tuple[VariationSpec, ...],
) -> dict[str, tuple[VariationSpec, ...]]:
    groups: dict[str, list[VariationSpec]] = {}
    for variation in variations:
        signature = detection_signature(apply_variation(base, variation))
        groups.setdefault(signature, []).append(variation)
    return {key: tuple(value) for key, value in groups.items()}
