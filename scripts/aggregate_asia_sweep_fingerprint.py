from __future__ import annotations

import argparse
import json
from pathlib import Path

from dtr_lab.strategies.asia_sweep.fingerprint_report import (
    build_development_report,
    write_development_report,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    report, tables = build_development_report(args.inputs)
    write_development_report(args.out, report, tables)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
