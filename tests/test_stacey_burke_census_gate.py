from __future__ import annotations

from typing import Any

import pandas as pd

from stacey_burke_lab.census_gate import build_census_decision
from stacey_burke_lab.fx_source import INSTRUMENTS


def _summaries(*, counts: dict[str, int] | None = None) -> list[dict[str, Any]]:
    counts = counts or {item.symbol: 10 for item in INSTRUMENTS}
    return [
        {
            "symbol": item.symbol,
            "factor_block": item.factor_block,
            "definition": {
                "london_start_minute": 420,
                "london_end_minute": 600,
                "excursion_atr_fraction": 0.05,
                "reclaim_minutes": 15,
            },
            "performance_execution": False,
            "forward_returns_inspected": False,
            "retained_events": counts.get(item.symbol, 0),
            "sessions_eligible": 100,
            "sessions_ineligible": 0,
            "sessions_ambiguous": 0,
            "high_events": counts.get(item.symbol, 0) // 2,
            "low_events": counts.get(item.symbol, 0) - counts.get(item.symbol, 0) // 2,
        }
        for item in INSTRUMENTS
    ]


def _events(*, counts: dict[str, int] | None = None) -> pd.DataFrame:
    counts = counts or {item.symbol: 10 for item in INSTRUMENTS}
    rows: list[dict[str, Any]] = []
    date_index = 0
    for item in INSTRUMENTS:
        for offset in range(counts.get(item.symbol, 0)):
            rows.append(
                {
                    "event_id": f"{item.symbol}-{offset}",
                    "symbol": item.symbol,
                    "factor_block": item.factor_block,
                    "london_date": f"2020-01-{date_index % 20 + 1:02d}",
                    "swept_side": "high" if offset % 2 else "low",
                }
            )
            date_index += 1
    return pd.DataFrame(rows)


def test_gate_passes_balanced_hundred_event_census() -> None:
    decision, pair_summary = build_census_decision(
        summaries=_summaries(),
        events=_events(),
    )

    assert decision["qualified"]
    assert decision["total_events"] == 100
    assert decision["pairs_with_at_least_five_events"] == 10
    assert decision["factor_blocks_with_at_least_ten_events"] == 4
    assert decision["max_pair_share"] == 0.10
    assert decision["max_date_share"] == 0.05
    assert pair_summary["count_matches_ledger"].all()


def test_gate_rejects_hidden_outcome_columns() -> None:
    events = _events()
    events["forward_return_60m"] = 0.0

    decision, _ = build_census_decision(
        summaries=_summaries(),
        events=events,
    )

    assert not decision["qualified"]
    assert decision["prohibited_columns"] == ["forward_return_60m"]
    assert not decision["gates"]["no_performance_or_forward_outcomes"]


def test_gate_rejects_pair_concentration() -> None:
    counts = {item.symbol: 7 for item in INSTRUMENTS}
    counts[INSTRUMENTS[0].symbol] = 40

    decision, _ = build_census_decision(
        summaries=_summaries(counts=counts),
        events=_events(counts=counts),
    )

    assert decision["total_events"] == 103
    assert not decision["gates"]["pair_concentration"]
    assert not decision["qualified"]


def test_gate_rejects_missing_pair_summary() -> None:
    summaries = _summaries()[:-1]

    decision, _ = build_census_decision(
        summaries=summaries,
        events=_events(),
    )

    assert not decision["gates"]["all_ten_pair_summaries_present"]
    assert not decision["qualified"]
