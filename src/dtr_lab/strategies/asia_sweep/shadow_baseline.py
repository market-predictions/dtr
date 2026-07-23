from __future__ import annotations

from .shadow_common import (
    EXECUTION_TICK,
    SESSION_TIMEZONE,
    SOURCE_INCREMENT,
    TARGET_RR,
    VARIANTS,
    ShadowExecutionConfig,
    normalize_bar,
    normalize_event,
    sha256_file,
)
from .shadow_execution import simulate_event
from .shadow_reporting import (
    classify_variant,
    instrument_breakdowns,
    load_source_window,
    max_drawdown_r,
    summarize_trades,
)

__all__ = [
    "EXECUTION_TICK",
    "SESSION_TIMEZONE",
    "SOURCE_INCREMENT",
    "TARGET_RR",
    "VARIANTS",
    "ShadowExecutionConfig",
    "classify_variant",
    "instrument_breakdowns",
    "load_source_window",
    "max_drawdown_r",
    "normalize_bar",
    "normalize_event",
    "sha256_file",
    "simulate_event",
    "summarize_trades",
]
