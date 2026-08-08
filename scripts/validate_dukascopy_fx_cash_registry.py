#!/usr/bin/env python3
"""Validate the Dukascopy FX Cash research registry."""

from pathlib import Path

from dtr_lab.research_registry import validate_registry


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate_registry(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Dukascopy FX Cash research registry: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
