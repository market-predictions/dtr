from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dtr_lab.strategies.wayne_direction.data import (
    REPLICATION_PAIRS,
    load_bid_ask_minutes,
)
from dtr_lab.strategies.wayne_direction.replication_panel import (
    build_pair_quality_summary,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Qualify one frozen Wayne replication FX source."
    )
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--symbol", choices=REPLICATION_PAIRS, required=True)
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2021)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def main() -> None:
    args = parse_args()
    quotes = load_bid_ask_minutes(
        args.data,
        args.symbol,
        start_year=args.start_year,
        end_year=args.end_year,
    )
    summary = build_pair_quality_summary(quotes, args.symbol)
    safe = _json_safe(summary)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "wayne_replication_pair_quality.json").write_text(
        json.dumps(safe, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    pd.DataFrame(safe["annual"]).to_csv(
        args.out / "wayne_replication_annual_quality.csv",
        index=False,
    )
    print(json.dumps(safe, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
