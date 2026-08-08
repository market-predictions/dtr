#!/usr/bin/env python3
"""Render the human-readable Dukascopy FX Cash research index."""

import json
from pathlib import Path

from dtr_lab.research_registry import render_registry_markdown


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    registry = root / "research_registry" / "dukascopy_fx_cash"
    index = json.loads((registry / "index.json").read_text(encoding="utf-8"))
    (registry / "INDEX.md").write_text(render_registry_markdown(index), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
