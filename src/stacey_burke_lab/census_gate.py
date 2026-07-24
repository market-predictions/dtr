from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from stacey_burke_lab.fx_source import INSTRUMENTS, write_json

PROHIBITED_OUTCOME_TOKENS = (
    "forward",
    "return",
    "entry",
    "stop",
    "target",
    "pnl",
    "expectancy",
    "profit",
    "loss",
)
REQUIRED_SYMBOLS = tuple(item.symbol for item in INSTRUMENTS)
REQUIRED_FACTOR_BLOCKS = tuple(sorted({item.factor_block for item in INSTRUMENTS}))


def _load_pair_inputs(inputs: Path) -> tuple[list[dict[str, Any]], pd.DataFrame]:
    summary_paths = sorted(inputs.rglob("*_event_census_summary.json"))
    event_paths = sorted(inputs.rglob("*_event_census.csv"))
    summaries = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in summary_paths
    ]
    events = (
        pd.concat((pd.read_csv(path) for path in event_paths), ignore_index=True)
        if event_paths
        else pd.DataFrame()
    )
    return summaries, events


def build_census_decision(
    *,
    summaries: list[dict[str, Any]],
    events: pd.DataFrame,
) -> tuple[dict[str, Any], pd.DataFrame]:
    symbols = [str(summary.get("symbol", "")) for summary in summaries]
    duplicate_symbols = sorted(
        symbol for symbol in set(symbols) if symbols.count(symbol) > 1
    )
    observed_symbols = set(symbols)
    missing_symbols = sorted(set(REQUIRED_SYMBOLS) - observed_symbols)
    unexpected_symbols = sorted(observed_symbols - set(REQUIRED_SYMBOLS))

    definitions = {
        json.dumps(summary.get("definition"), sort_keys=True)
        for summary in summaries
    }
    definition_consistent = len(definitions) == 1 and len(summaries) == len(REQUIRED_SYMBOLS)
    no_execution_flags = all(
        summary.get("performance_execution") is False
        and summary.get("forward_returns_inspected") is False
        for summary in summaries
    )
    prohibited_columns = sorted(
        column
        for column in events.columns
        if any(token in column.lower() for token in PROHIBITED_OUTCOME_TOKENS)
    )

    if not events.empty:
        event_symbols = set(events["symbol"].astype(str))
        event_count_by_date = (
            events.groupby("london_date", observed=True)
            .size()
            .sort_values(ascending=False)
        )
    else:
        event_symbols = set()
        event_count_by_date = pd.Series(dtype="int64", name="retained_events")

    pair_summary_rows: list[dict[str, Any]] = []
    for item in INSTRUMENTS:
        summary = next(
            (value for value in summaries if value.get("symbol") == item.symbol),
            {},
        )
        count = int(summary.get("retained_events", 0))
        ledger_count = (
            int((events["symbol"].astype(str) == item.symbol).sum())
            if "symbol" in events
            else 0
        )
        pair_summary_rows.append(
            {
                "symbol": item.symbol,
                "factor_block": item.factor_block,
                "retained_events": count,
                "ledger_events": ledger_count,
                "count_matches_ledger": count == ledger_count,
                "sessions_eligible": int(summary.get("sessions_eligible", 0)),
                "sessions_ineligible": int(summary.get("sessions_ineligible", 0)),
                "sessions_ambiguous": int(summary.get("sessions_ambiguous", 0)),
                "high_events": int(summary.get("high_events", 0)),
                "low_events": int(summary.get("low_events", 0)),
            }
        )
    pair_summary = pd.DataFrame(pair_summary_rows)
    total_events = int(pair_summary["retained_events"].sum())
    ledger_total = int(len(events))

    factor_counts = (
        pair_summary.groupby("factor_block", observed=True)["retained_events"]
        .sum()
        .to_dict()
    )
    pair_counts = pair_summary.set_index("symbol")["retained_events"].to_dict()
    pairs_with_five = sum(count >= 5 for count in pair_counts.values())
    factor_blocks_with_ten = sum(
        factor_counts.get(block, 0) >= 10 for block in REQUIRED_FACTOR_BLOCKS
    )
    max_pair_count = max(pair_counts.values(), default=0)
    max_pair_share = max_pair_count / total_events if total_events else None
    max_date_count = int(event_count_by_date.iloc[0]) if not event_count_by_date.empty else 0
    max_date_share = max_date_count / total_events if total_events else None

    gates = {
        "all_ten_pair_summaries_present": (
            not missing_symbols
            and not unexpected_symbols
            and not duplicate_symbols
            and len(summaries) == len(REQUIRED_SYMBOLS)
        ),
        "definition_consistent": definition_consistent,
        "no_performance_or_forward_outcomes": (
            no_execution_flags and not prohibited_columns
        ),
        "pair_summary_counts_match_ledgers": bool(
            pair_summary["count_matches_ledger"].all()
        )
        and total_events == ledger_total,
        "minimum_pooled_events": total_events >= 100,
        "pair_breadth": pairs_with_five >= 8,
        "factor_block_breadth": factor_blocks_with_ten == len(REQUIRED_FACTOR_BLOCKS),
        "pair_concentration": (
            max_pair_share is not None and max_pair_share <= 0.30
        ),
        "date_concentration": (
            max_date_share is not None and max_date_share <= 0.10
        ),
    }
    qualified = all(gates.values())

    definition = (
        json.loads(next(iter(definitions)))
        if definition_consistent and definitions
        else None
    )
    decision: dict[str, Any] = {
        "programme": "stacey_burke_conditional_sweep_reclaim_census_v1",
        "decision": (
            "PASS_EVENT_CENSUS_AUTHORIZE_CONTROLLED_EVENT_STUDY"
            if qualified
            else "FAIL_EVENT_CENSUS_STOP_REVERSAL_PROGRAMME"
        ),
        "qualified": qualified,
        "performance_execution": False,
        "forward_returns_inspected": False,
        "definition": definition,
        "required_symbols": list(REQUIRED_SYMBOLS),
        "required_factor_blocks": list(REQUIRED_FACTOR_BLOCKS),
        "missing_symbols": missing_symbols,
        "unexpected_symbols": unexpected_symbols,
        "duplicate_symbols": duplicate_symbols,
        "event_symbols": sorted(event_symbols),
        "prohibited_columns": prohibited_columns,
        "total_events": total_events,
        "ledger_total_events": ledger_total,
        "pairs_with_at_least_five_events": pairs_with_five,
        "factor_blocks_with_at_least_ten_events": factor_blocks_with_ten,
        "pair_counts": {key: int(value) for key, value in pair_counts.items()},
        "factor_block_counts": {
            key: int(value) for key, value in factor_counts.items()
        },
        "max_pair_count": max_pair_count,
        "max_pair_share": max_pair_share,
        "max_date_count": max_date_count,
        "max_date_share": max_date_share,
        "gates": gates,
    }
    return decision, pair_summary


def summarize_census_inputs(*, inputs: Path, output: Path) -> dict[str, Any]:
    summaries, events = _load_pair_inputs(inputs)
    decision, pair_summary = build_census_decision(
        summaries=summaries,
        events=events,
    )
    output.mkdir(parents=True, exist_ok=True)
    write_json(decision, output / "event_census_decision.json")
    pair_summary.to_csv(output / "event_census_pair_summary.csv", index=False)
    events.to_csv(output / "event_census_events.csv", index=False)
    return decision


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aggregate and enforce the preregistered Stacey Burke event census gate"
    )
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    decision = summarize_census_inputs(inputs=args.inputs, output=args.out)
    print(
        f"{decision['decision']}: {decision['total_events']} pooled events, "
        f"{decision['pairs_with_at_least_five_events']} pairs with >=5 events"
    )
    if not decision["qualified"]:
        raise SystemExit(decision["decision"])


if __name__ == "__main__":
    main()
