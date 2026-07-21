from __future__ import annotations

import argparse
import json
from pathlib import Path

from dtr_lab.data import classify_gaps, load_market_data, summarize_gaps


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify market-data gaps")
    parser.add_argument("dataset", help="CSV or single-member ZIP market dataset")
    parser.add_argument("--out", default="reports/gap-audit")
    parser.add_argument(
        "--keep-final-date",
        action="store_true",
        help="Do not drop the final source date before auditing",
    )
    args = parser.parse_args()

    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    frame = load_market_data(args.dataset)
    if not args.keep_final_date:
        final_date = frame["timestamp_et"].dt.normalize().iloc[-1]
        frame = frame[frame["timestamp_et"].dt.normalize() < final_date].copy()

    gaps = classify_gaps(frame)
    summary = summarize_gaps(gaps)
    gaps.to_csv(output / "all_gaps.csv", index=False)
    gaps[gaps["reject_trade_bridge"]].to_csv(
        output / "unsafe_gaps.csv", index=False
    )
    with (output / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary.as_dict(), handle, indent=2, sort_keys=True)
        handle.write("\n")

    print(
        f"total_gaps={summary.total_gaps} unsafe_gaps={summary.unsafe_gaps} "
        f"output={output}"
    )


if __name__ == "__main__":
    main()
