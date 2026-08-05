from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the frozen GBP/USD Stage-1 engine on a pip-normalized pair cache."
    )
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--pair-label", required=True)
    parser.add_argument("--source-symbol", required=True)
    parser.add_argument("--normalization-scale", type=float, required=True)
    parser.add_argument("--bootstrap", type=int, default=5000)
    args = parser.parse_args()

    command = [
        sys.executable,
        "scripts/run_quarters_stage1.py",
        "--data-dir",
        str(args.data_dir),
        "--output-dir",
        str(args.output_dir),
        "--start-year",
        "2015",
        "--end-year",
        "2021",
        "--reset-pips",
        "25",
        "--bootstrap",
        str(args.bootstrap),
    ]
    subprocess.run(command, check=True)

    key_path = args.output_dir / "key_results.json"
    key = json.loads(key_path.read_text(encoding="utf-8"))
    key["configuration"].update(
        {
            "pair": args.pair_label,
            "source_symbol": args.source_symbol,
            "source_quote_normalization_scale": args.normalization_scale,
            "analysis_pip_size": 0.0001,
            "normalization_contract": (
                "Prices are multiplied by source_quote_normalization_scale so one source pip "
                "equals 0.0001 in the unchanged frozen GBPUSD engine."
            ),
        }
    )
    key_path.write_text(json.dumps(key, indent=2), encoding="utf-8")
    print(json.dumps(key, indent=2))


if __name__ == "__main__":
    main()
