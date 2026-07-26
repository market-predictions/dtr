"""Wayne McDonell pivot-point research package."""

from dtr_lab.strategies.wayne_pivots.pivot_atlas import evaluate_geometry_atlas
from dtr_lab.strategies.wayne_pivots.pivot_geometry import (
    PRIMARY_PAIRS,
    STRUCTURES,
    build_anatomy_ledger as _build_anatomy_ledger,
    build_pivot_days,
    build_structures,
    load_bid_ask_minutes,
    midpoint_minutes,
    pivot_day_start,
    traditional_structure,
)


def build_anatomy_ledger(*args, **kwargs):
    """Build anatomy and normalize the non-authoritative previous-pivot metadata."""
    ledger, day_ledger = _build_anatomy_ledger(*args, **kwargs)
    day_ledger = day_ledger.copy()
    day_ledger["previous_wayne_p"] = day_ledger["wayne_p"].shift(1)
    return ledger, day_ledger


__all__ = [
    "PRIMARY_PAIRS",
    "STRUCTURES",
    "build_anatomy_ledger",
    "build_pivot_days",
    "build_structures",
    "evaluate_geometry_atlas",
    "load_bid_ask_minutes",
    "midpoint_minutes",
    "pivot_day_start",
    "traditional_structure",
]
