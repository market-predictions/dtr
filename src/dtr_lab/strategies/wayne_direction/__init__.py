"""Direction-first Wayne framework research package."""

from .calendar import (
    NEW_YORK_TZ,
    build_new_york_daily_bars,
    build_new_york_h4_bars,
    h4_bar_start,
    pivot_day_start,
)
from .data import (
    PRIMARY_PAIRS,
    REPLICATION_PAIRS,
    SUPPORTED_PAIRS,
    load_bid_ask_minutes,
    midpoint_minutes,
)
from .h4_sensitivity import (
    build_h4_monthly_attribution,
    classify_d1_relation,
    classify_h4_relation,
)
from .health import attach_last_completed_h4, build_h4_health
from .model import CandidateState, TrendConfig, TrendDirection
from .monthly import (
    build_monthly_context,
    build_monthly_reach_ledger,
    traditional_levels,
)
from .replication_panel import (
    DEFAULT_THRESHOLDS,
    PIP_SIZES,
    ReplicationQualityThresholds,
    annual_spread_quantiles,
    build_pair_quality_summary,
    evaluate_quality_metrics,
    expected_calendar_minutes,
)
from .staged_sequence import build_staged_monthly_sequence
from .structure import build_structure_ledger
from .structure_common import average_true_range, confirmed_swings

__all__ = [
    "CandidateState",
    "DEFAULT_THRESHOLDS",
    "NEW_YORK_TZ",
    "PIP_SIZES",
    "PRIMARY_PAIRS",
    "REPLICATION_PAIRS",
    "ReplicationQualityThresholds",
    "SUPPORTED_PAIRS",
    "TrendConfig",
    "TrendDirection",
    "annual_spread_quantiles",
    "attach_last_completed_h4",
    "average_true_range",
    "build_h4_health",
    "build_h4_monthly_attribution",
    "build_monthly_context",
    "build_monthly_reach_ledger",
    "build_new_york_daily_bars",
    "build_new_york_h4_bars",
    "build_pair_quality_summary",
    "build_staged_monthly_sequence",
    "build_structure_ledger",
    "classify_d1_relation",
    "classify_h4_relation",
    "confirmed_swings",
    "evaluate_quality_metrics",
    "expected_calendar_minutes",
    "h4_bar_start",
    "load_bid_ask_minutes",
    "midpoint_minutes",
    "pivot_day_start",
    "traditional_levels",
]
