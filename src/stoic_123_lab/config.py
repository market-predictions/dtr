from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

import yaml

MapMode = Literal["none", "ema_alignment", "recent_breakout", "ema_plus_breakout"]
FillMode = Literal["next_open", "signal_close"]
ExecutionModel = Literal["single_ohlc", "fx_bid_ask"]
InstrumentName = Literal["NQ", "NQ_PROXY", "ES_PROXY", "GBPUSD"]


@dataclass(frozen=True)
class InstrumentSpec:
    name: InstrumentName
    tick_size: float
    point_value: float
    commission_per_side: float
    source_sha256: str
    source_classification: str
    execution_model: ExecutionModel = "single_ohlc"


NQ_SPEC = InstrumentSpec(
    name="NQ",
    tick_size=0.25,
    point_value=20.0,
    commission_per_side=2.25,
    source_sha256="8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc",
    source_classification="NQ futures research archive",
)

NQ_PROXY_SPEC = InstrumentSpec(
    name="NQ_PROXY",
    tick_size=0.25,
    point_value=20.0,
    commission_per_side=2.25,
    source_sha256="b98f08a0fd35255c09232d41da10ee84559587067b48e942cccdbe37b0b888c4",
    source_classification=(
        "Dukascopy USATECH bid-CFD Nasdaq-100 proxy with NQ-equivalent research "
        "economics; not CME NQ futures"
    ),
)

ES_PROXY_SPEC = InstrumentSpec(
    name="ES_PROXY",
    tick_size=0.25,
    point_value=50.0,
    commission_per_side=2.25,
    source_sha256="a2342f9d64695d8ecb618a907600b4de0b1433ba65d25c1f0ac3d0566ab9a72f",
    source_classification=(
        "Dukascopy USA500 bid-CFD S&P-500 proxy with ES-equivalent research "
        "economics; not CME ES futures"
    ),
)

GBPUSD_SPEC = InstrumentSpec(
    name="GBPUSD",
    tick_size=0.00001,
    point_value=100_000.0,
    commission_per_side=0.0,
    source_sha256="44df46cfd7bce946074ae2f541a654cff907c7cc9a8bc43fac8b4090624e860e",
    source_classification=(
        "Dukascopy GBPUSD bid/ask M1 private cache; corrected from the documented "
        "BI5 open-close-low-high field order; midpoint signals with side-correct execution"
    ),
    execution_model="fx_bid_ask",
)


@dataclass(frozen=True)
class SequenceConfig:
    arm_id: str
    description: str
    execution_minutes: int = 5
    management_minutes: int = 15
    map_minutes: int = 60
    ema_fast: int = 10
    ema_slow: int = 20
    atr_length: int = 14
    map_mode: MapMode = "ema_alignment"
    map_breakout_lookback: int = 20
    map_breakout_active_bars: int = 6
    step1_close_buffer_atr: float = 0.05
    step1_min_body_fraction: float = 0.50
    retest_max_bars: int = 12
    retest_tolerance_atr: float = 0.25
    base_min_bars: int = 3
    base_max_bars: int = 8
    base_max_range_atr: float = 1.00
    base_min_overlap_ratio: float = 0.50
    step3_close_buffer_atr: float = 0.05
    breakout_expiry_bars: int = 8
    require_map_at_step3: bool = True
    fill_mode: FillMode = "next_open"
    stop_buffer_ticks: int = 4
    minimum_risk_ticks: int = 8
    max_hold_minutes: int = 1_440
    gap_reset_minutes: int = 15
    slippage_ticks_each_side: float = 1.0
    allow_long: bool = True
    allow_short: bool = True

    def management_config(self) -> SequenceConfig:
        return replace(
            self,
            arm_id=f"{self.arm_id}__MANAGEMENT",
            description=f"Management sequence for {self.arm_id}",
            execution_minutes=self.management_minutes,
        )

    def validate(self) -> None:
        if self.execution_minutes <= 0 or self.management_minutes <= 0 or self.map_minutes <= 0:
            raise ValueError("All timeframes must be positive")
        if self.ema_fast >= self.ema_slow:
            raise ValueError("ema_fast must be smaller than ema_slow")
        if self.base_min_bars < 2 or self.base_min_bars > self.base_max_bars:
            raise ValueError("Invalid base bar bounds")
        if self.retest_max_bars < 1 or self.breakout_expiry_bars < 1:
            raise ValueError("Retest and breakout expiry must be positive")
        if not 0 <= self.step1_min_body_fraction <= 1:
            raise ValueError("step1_min_body_fraction must be between zero and one")
        if not 0 <= self.base_min_overlap_ratio <= 1:
            raise ValueError("base_min_overlap_ratio must be between zero and one")
        if self.minimum_risk_ticks <= 0:
            raise ValueError("minimum_risk_ticks must be positive")
        if self.slippage_ticks_each_side < 0:
            raise ValueError("slippage_ticks_each_side cannot be negative")
        if not (self.allow_long or self.allow_short):
            raise ValueError("At least one direction must be enabled")


_ALLOWED_FIELDS = set(SequenceConfig.__dataclass_fields__)


def load_config_family(path: str | Path) -> list[SequenceConfig]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("arms"), list):
        raise ValueError("Config file must contain an 'arms' list")
    defaults = payload.get("defaults", {})
    if not isinstance(defaults, dict):
        raise ValueError("defaults must be a mapping")
    unknown_defaults = set(defaults).difference(_ALLOWED_FIELDS)
    if unknown_defaults:
        raise ValueError(f"Unknown default fields: {sorted(unknown_defaults)}")

    configs: list[SequenceConfig] = []
    seen: set[str] = set()
    for raw in payload["arms"]:
        if not isinstance(raw, dict):
            raise ValueError("Each arm must be a mapping")
        merged = {**defaults, **raw}
        unknown = set(merged).difference(_ALLOWED_FIELDS)
        if unknown:
            raise ValueError(f"Unknown config fields: {sorted(unknown)}")
        config = SequenceConfig(**merged)
        config.validate()
        if config.arm_id in seen:
            raise ValueError(f"Duplicate arm_id: {config.arm_id}")
        seen.add(config.arm_id)
        configs.append(config)
    if not configs:
        raise ValueError("At least one arm is required")
    return configs
