from __future__ import annotations

import pandas as pd

from stacey_burke_lab.event_study_gate import (
    build_gate_b_decision,
    clustered_matched_set_permutation,
    date_block_bootstrap,
)
from stacey_burke_lab.fx_source import INSTRUMENTS


def _synthetic_gate_inputs(
    *,
    event_outcome: float = 0.05,
    control_outcome: float = 0.0,
) -> tuple[list[dict[str, object]], pd.DataFrame, pd.DataFrame]:
    summaries = [
        {
            "symbol": item.symbol,
            "factor_block": item.factor_block,
            "definition": {
                "forward_minutes": 60,
                "pre_return_minutes": 15,
                "realized_vol_minutes": 60,
                "controls_per_event": 5,
                "london_bucket_minutes": 15,
            },
            "performance_execution": False,
            "strategy_pnl_calculated": False,
        }
        for item in INSTRUMENTS
    ]
    event_rows = []
    control_rows = []
    for symbol_index, item in enumerate(INSTRUMENTS):
        for offset in range(40):
            event_id = f"{item.symbol}-{offset:03d}"
            event_date = f"2020-02-{offset % 20 + 1:02d}"
            event_rows.append(
                {
                    "event_id": event_id,
                    "symbol": item.symbol,
                    "factor_block": item.factor_block,
                    "london_date": event_date,
                    "event_outcome_atr": event_outcome,
                    "control_mean_outcome_atr": control_outcome,
                    "effect_atr": event_outcome - control_outcome,
                }
            )
            for rank in range(1, 6):
                control_rows.append(
                    {
                        "event_id": event_id,
                        "symbol": item.symbol,
                        "factor_block": item.factor_block,
                        "event_london_date": event_date,
                        "control_rank": rank,
                        "control_london_date": (
                            f"2019-{rank:02d}-{symbol_index + 1:02d}"
                        ),
                        "control_outcome_atr": control_outcome,
                    }
                )
    return summaries, pd.DataFrame(event_rows), pd.DataFrame(control_rows)


def test_blocked_inference_detects_uniform_positive_effect() -> None:
    _, events, controls = _synthetic_gate_inputs()

    bootstrap = date_block_bootstrap(events, iterations=1_000)
    permutation = clustered_matched_set_permutation(
        events=events,
        controls=controls,
        iterations=1_000,
    )

    assert bootstrap["lo95_mean_effect_atr"] > 0
    assert bootstrap["hi95_mean_effect_atr"] > 0
    assert permutation["one_sided_p_value"] <= 0.05


def test_gate_b_passes_only_complete_broad_positive_study() -> None:
    summaries, events, controls = _synthetic_gate_inputs()

    decision, pair_summary, factor_summary = build_gate_b_decision(
        summaries=summaries,
        events=events,
        controls=controls,
    )

    assert decision["qualified"]
    assert decision["matched_events"] == 400
    assert decision["positive_pairs"] == 10
    assert decision["positive_factor_blocks"] == 4
    assert pair_summary["mean_effect_atr"].gt(0).all()
    assert factor_summary["mean_effect_atr"].gt(0).all()


def test_gate_b_rejects_effect_below_frozen_minimum() -> None:
    summaries, events, controls = _synthetic_gate_inputs(
        event_outcome=0.01,
        control_outcome=0.0,
    )

    decision, _, _ = build_gate_b_decision(
        summaries=summaries,
        events=events,
        controls=controls,
    )

    assert not decision["qualified"]
    assert not decision["scientific_gates"]["minimum_mean_effect_0_02_atr"]
