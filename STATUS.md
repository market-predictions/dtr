# DTR Optimization Lab Status

## Current work package

`DTR-NQ-WP-20260721-01 — Baseline integrity closure`

Status: **in progress**

Branch: `agent/nq-baseline-integrity-closure`

## Current primary dataset

`nq_futures_1m_2022_2025`

The NQ dataset remains the sole optimization base for the current phase. Dukascopy and other feeds are deferred.

## Current candidate

`DTR_PY_NQ_CANDIDATE_0_1`

Promotion state: **HOLD_FOR_MORE_DATA / INTEGRITY GATE OPEN**

## Immediate gate

- integrate deterministic gap-state metadata;
- invalidate setups across reset boundaries;
- reject open-trade bridges across unsafe gaps;
- preserve clean-data behavior;
- run CI and independent review;
- rerun the frozen manifest when the local NQ dataset is available.

## Next planned phase

Independent continuation engine after the baseline integrity gate closes.
