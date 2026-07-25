from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from stacey_burke_lab.fx_source import INSTRUMENTS, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate Stacey Burke FX source qualification")
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    records: dict[str, dict[str, Any]] = {}
    for path in sorted(args.inputs.glob("*_source_qualification.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        symbol = str(record["symbol"])
        if symbol in records:
            raise ValueError(f"duplicate qualification result for {symbol}")
        records[symbol] = record

    expected = [item.symbol for item in INSTRUMENTS]
    missing = sorted(set(expected) - set(records))
    unexpected = sorted(set(records) - set(expected))
    qualified_symbols = sorted(
        symbol for symbol, record in records.items() if bool(record.get("qualified"))
    )
    all_qualified = not missing and not unexpected and qualified_symbols == sorted(expected)

    partitions = []
    for symbol in expected:
        record = records.get(symbol)
        if record is None:
            continue
        for partition in record["partitions"]:
            partitions.append(
                {
                    "symbol": symbol,
                    "factor_block": record["factor_block"],
                    "partition": partition["partition"]["label"],
                    "monitoring_only": partition["partition"]["monitoring_only"],
                    "qualified": partition["qualified"],
                    "synchronized_active_rows": partition["synchronized_active_rows"],
                    "synchronization_fraction": partition[
                        "bid_ask_synchronization_fraction"
                    ],
                    "median_close_spread_pips": partition["median_close_spread_pips"],
                    "bid_sha256": partition["bid"]["sha256"],
                    "ask_sha256": partition["ask"]["sha256"],
                }
            )

    decision = {
        "programme": "stacey_burke_fx_source_universe_v1",
        "decision": "PASS_SOURCE_GATE_EVENT_CENSUS_AUTHORIZED"
        if all_qualified
        else "FAIL_SOURCE_GATE_EVENT_CENSUS_BLOCKED",
        "expected_symbols": expected,
        "received_symbols": sorted(records),
        "qualified_symbols": qualified_symbols,
        "missing_symbols": missing,
        "unexpected_symbols": unexpected,
        "all_qualified": all_qualified,
        "performance_execution": False,
        "event_return_inspection": False,
        "partition_evidence": partitions,
    }
    write_json(decision, args.out / "stacey_burke_fx_source_universe_decision.json")

    lines = [
        "# Stacey Burke FX Source Universe Decision",
        "",
        f"Decision: `{decision['decision']}`",
        "",
        f"Qualified mandatory symbols: {len(qualified_symbols)}/{len(expected)}",
        "",
        "No event returns or strategy P&L were calculated in this source work package.",
    ]
    (args.out / "STACEY_BURKE_FX_SOURCE_UNIVERSE_DECISION.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    if not all_qualified:
        raise SystemExit(decision["decision"])


if __name__ == "__main__":
    main()
