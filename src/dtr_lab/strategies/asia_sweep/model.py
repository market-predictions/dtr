from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum

import pandas as pd


class AsiaSweepVariant(StrEnum):
    """Pre-registered signal variants; variants are never selected after lockbox inspection."""

    AGGRESSIVE_RECLAIM = "AS_A_AGGRESSIVE_RECLAIM"
    WICK_QUALIFIED = "AS_B_WICK_QUALIFIED"
    DISPLACEMENT = "AS_C_DISPLACEMENT"
    FAILED_RETEST = "AS_D_FAILED_RETEST"


@dataclass(frozen=True)
class ExecutionWindow:
    name: str
    start_hour: int
    start_minute: int
    end_hour: int
    end_minute: int


DEFAULT_WINDOWS = (
    ExecutionWindow("LONDON", 2, 0, 6, 0),
    ExecutionWindow("NEW_YORK", 8, 30, 11, 30),
)


@dataclass(frozen=True)
class AsiaSweepConfig:
    name: str
    variant: AsiaSweepVariant
    tick_size: float
    point_value: float
    commission_per_side: float
    slippage_ticks_each_side: float = 1.0
    asia_start_hour: int = 18
    asia_start_minute: int = 0
    asia_end_hour: int = 2
    asia_end_minute: int = 0
    windows: tuple[ExecutionWindow, ...] = DEFAULT_WINDOWS
    weekdays: tuple[int, ...] = (0, 1, 2, 3, 4)
    min_sweep_ticks: int = 2
    wick_ratio_min: float = 0.50
    close_location_min: float = 0.60
    displacement_max_bars: int = 3
    displacement_body_mult: float = 1.25
    displacement_median_length: int = 20
    failed_retest_max_bars: int = 8
    retest_band_ticks: int = 4
    stop_buffer_ticks: int = 2
    target_rr: float = 2.0
    same_bar_double_sweep_policy: str = "reject_ambiguous"

    def __post_init__(self) -> None:
        if self.tick_size <= 0:
            raise ValueError("tick_size must be positive")
        if self.point_value <= 0:
            raise ValueError("point_value must be positive")
        if self.min_sweep_ticks < 1:
            raise ValueError("min_sweep_ticks must be at least one")
        if not 0 <= self.wick_ratio_min <= 1:
            raise ValueError("wick_ratio_min must be in [0, 1]")
        if not 0 <= self.close_location_min <= 1:
            raise ValueError("close_location_min must be in [0, 1]")
        if self.target_rr <= 0:
            raise ValueError("target_rr must be positive")
        if self.same_bar_double_sweep_policy != "reject_ambiguous":
            raise ValueError("Only reject_ambiguous is currently supported")


@dataclass(frozen=True)
class AsiaSweepEvent:
    instrument: str
    trade_date: pd.Timestamp
    execution_window: str
    variant: str
    status: str
    rejection_reason: str | None
    asia_start: pd.Timestamp
    asia_end: pd.Timestamp
    asia_high: float
    asia_low: float
    asia_range_points: float
    swept_side: str | None = None
    direction: int = 0
    first_sweep_timestamp: pd.Timestamp | None = None
    sweep_extreme: float | None = None
    sweep_depth_points: float | None = None
    sweep_depth_ticks: float | None = None
    sweep_depth_range_fraction: float | None = None
    sweep_bar_open: float | None = None
    sweep_bar_high: float | None = None
    sweep_bar_low: float | None = None
    sweep_bar_close: float | None = None
    wick_ratio: float | None = None
    close_location_value: float | None = None
    closed_back_inside: bool = False
    reclaim_delay_bars: int | None = None
    displacement_present: bool = False
    displacement_delay_bars: int | None = None
    failed_retest_present: bool = False
    entry_timestamp: pd.Timestamp | None = None
    entry_price_raw: float | None = None
    stop_price_raw: float | None = None
    target_price_raw: float | None = None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)
