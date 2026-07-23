# Status — Stoic Edge 1-2-3

Date: 2026-07-23
Version: `v0.1.0-research`
Work package: `STOIC123-WP-20260723-01`
Decision state: `FRAMEWORK_COMPLETE_DATA_RUN_PENDING`

## Complete

- Dedicated strategy namespace and governance tree.
- Frozen six-arm phase-one candidate family.
- NQ and `ES_PROXY` checksum-gated loaders.
- Causal multi-timeframe map alignment.
- Step-1, retest, post-retest base, boundary lock, and Step-3 state machine.
- Next-open execution, base-derived stop, cost model, gap liquidation, maximum hold, and opposite-sequence exit.
- Event, trade, funnel, summary, bootstrap, manifest, and decision outputs.
- Independent trade-ledger reconstruction gate.
- Ten synthetic tests passing locally.

## Pending

The raw NQ and USA500 files are intentionally excluded from Git and were not mounted in the implementation environment. The historical run must therefore execute where the qualified local data artifacts are available. No performance result has been inspected or claimed in this work package.

## Scientific restrictions

- No DTR baseline or DTR test result is changed.
- No pooled NQ/ES-proxy optimization.
- No proxy-specific parameter tuning.
- No CME ES claim from USA500.
- No promotion from full-sample profitability alone.
- No live trading, sizing, or Pine authorization.
