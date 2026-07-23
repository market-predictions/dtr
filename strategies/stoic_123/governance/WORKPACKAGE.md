# STOIC123-WP-20260723-01 — Separate 1-2-3 Test Framework

## Objective

Build an isolated Python research framework for the Stoic Edge 1-2-3 sequence using the available NQ and S&P proxy data, while preventing contamination of DTR tests, baselines, decisions, and result ledgers.

## In scope

- Mechanical translation of map, Step 1, Step 2, boundary lock, Step 3, and opposite-sequence exit.
- NQ and `ES_PROXY` source adapters using existing qualified data contracts.
- Small preregistered candidate family.
- Cost-aware one-minute execution.
- Causal and independent validation gates.
- Dedicated documentation, roadmap, status, changelog, and handover.

## Out of scope

- Changes to DTR strategy logic.
- Retuning DTR E5/E6 or the no-FOMC working configuration.
- Treating USA500 as actual ES futures.
- Partial profits, discretionary climactic exits, sizing, Pine, or deployment.
- Selecting a winner before robustness and fresh-data gates.

## Acceptance criteria

- Separate branch and file structure.
- Base boundaries are selected and frozen before Step 3.
- Wick-only EMA breaches cannot complete Step 1.
- The management timeframe is fixed before entry.
- Unsafe gaps cannot be silently bridged.
- NQ and `ES_PROXY` results cannot be pooled.
- Synthetic causality, execution, gap, configuration, and independent-review tests pass.
- Raw-data absence is reported honestly; no invented performance results.
