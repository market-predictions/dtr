# DTR Optimization Lab Status

## Current work package

`DTR-NQ-WP-20260721-01 — Baseline integrity closure`

Status: **implementation complete; full-dataset rerun pending**

Branch: `agent/nq-baseline-integrity-closure`

Draft PR: `#1 — Close NQ baseline integrity gate`

## Current primary dataset

`nq_futures_1m_2022_2025`

The NQ dataset remains the sole optimization base for the current phase. Dukascopy and other feeds are deferred.

## Current candidates

### Frozen reference

`DTR_PY_NQ_CANDIDATE_0_1`

Execution policy: `observe_only`

Purpose: reproduce the historical 504-trade result and report integrity observations without changing the trade set.

### Sanitized candidate

`DTR_PY_NQ_CANDIDATE_0_1_GAP_SAFE`

Execution policy: `reject_unsafe`

Purpose: use identical strategy parameters while rejecting contaminated ranges, setup paths, and open-trade intervals.

## Validation status

- Gap-safe implementation: **complete**
- Independent adversarial review: **complete**
- Pinned Ruff 0.15.22: **passed**
- Pytest Python 3.11: **passed**
- Pytest Python 3.12: **passed**
- CI run: `29850412195` — **success**
- Full reference manifest rerun: **pending local archive**
- Full gap-safe manifest rerun: **pending local archive**

## Promotion state

`PROMOTE_TO_FULL_DATASET_RERUN`

This is not candidate-performance approval and does not yet authorize new parameter optimization.

## Immediate next action

Place the checksum-matched NQ archive at:

`data/raw/NQ_Futures_-_1min_Bar_2022_2025.zip`

Then execute the two commands in:

`handovers/DTR-NQ-WP-20260721-01.md`

The rerun must reproduce the frozen baseline, generate the gap-safe comparison, attribute every changed trade, and lock deterministic artifacts.

## Next planned research phase

Independent continuation engine, only after the reference-versus-gap-safe comparison receives a new promotion decision.
