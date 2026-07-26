from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TrendDirection(StrEnum):
    NONE = "NONE"
    BULL = "BULL"
    BEAR = "BEAR"
    AMBIGUOUS_SHOCK = "AMBIGUOUS_SHOCK"


class CandidateState(StrEnum):
    NEUTRAL = "NEUTRAL"
    FIRST_EXTREME = "FIRST_EXTREME"
    DOUBLE_EXTREME = "DOUBLE_EXTREME"
    BOS = "BOS"
    RETEST = "RETEST"
    PULLBACK_CONFIRMED = "PULLBACK_CONFIRMED"
    TREND_CONFIRMED = "TREND_CONFIRMED"


@dataclass(frozen=True)
class TrendConfig:
    swing_left: int = 2
    swing_right: int = 2
    atr_length: int = 20
    double_tolerance_atr: float = 0.20
    break_buffer_atr: float = 0.05
    retest_band_atr: float = 0.15
    min_separation_bars: int = 5
    max_separation_bars: int = 60
    max_bos_wait_bars: int = 30
    max_retest_wait_bars: int = 20
    max_continuation_wait_bars: int = 30

    def __post_init__(self) -> None:
        if self.swing_left < 1 or self.swing_right < 1:
            raise ValueError("swing confirmation windows must be positive")
        if self.atr_length < 2:
            raise ValueError("atr_length must be at least two")
        for name in (
            "double_tolerance_atr",
            "break_buffer_atr",
            "retest_band_atr",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.min_separation_bars < 1:
            raise ValueError("min_separation_bars must be positive")
        if self.max_separation_bars < self.min_separation_bars:
            raise ValueError("max_separation_bars must not be smaller than minimum")
        if self.max_bos_wait_bars < 1:
            raise ValueError("max_bos_wait_bars must be positive")
        if self.max_retest_wait_bars < 1:
            raise ValueError("max_retest_wait_bars must be positive")
        if self.max_continuation_wait_bars < 1:
            raise ValueError("max_continuation_wait_bars must be positive")


DEFAULT_TREND_CONFIG = TrendConfig()
