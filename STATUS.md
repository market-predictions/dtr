# DTR Optimization Lab Status

## Current work package

`DTR-NQ-WP-20260721-01 — Baseline integrity closure`

Status: **complete**

Branch: `agent/nq-baseline-integrity-closure`

Draft PR: `#1 — Close NQ baseline integrity gate`

## Current primary dataset

`nq_futures_1m_2022_2025`

Dataset SHA-256:

`8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc`

NQ remains the sole optimization base for the current phase. Dukascopy and other feeds are deferred.

## Frozen reference

`DTR_PY_NQ_CANDIDATE_0_1`

- policy: `observe_only`;
- trades: `504`;
- net R: `84.16435914242919`;
- maximum drawdown: `14.107857513807524R`;
- regression: **passed**.

## Gap-safe baseline

`DTR_PY_NQ_CANDIDATE_0_1_GAP_SAFE`

- policy: `reject_unsafe`;
- strategy parameters: **identical to the frozen reference**;
- trades: `491`;
- net R: `88.49578342152539`;
- maximum drawdown: `14.107857513807524R`;
- regression: **locked and passed**.

## Difference attribution

- removed trades: `13`;
- added trades: `0`;
- contaminated session ranges: `9` trades;
- unsafe gaps during open trades: `4` trades;
- unexplained differences: `0`;
- deterministic clean reruns: **byte-identical for all required artifacts**.

Comparison report:

`docs/NQ_GAP_SAFE_COMPARISON_2026-07-21.md`

Compact machine-readable result:

`results/2026-07-21/nq_candidate_0_1_gap_safe_summary.json`

## Validation status

- Independent adversarial review: **complete**
- Pinned Ruff 0.15.22: **passed**
- Pytest Python 3.11: **passed**
- Pytest Python 3.12: **passed**
- Frozen reference full-data rerun: **passed**
- Gap-safe full-data rerun: **passed**
- Trade-level attribution: **complete**
- Artifact hash lock: **complete**

## Promotion state

`PROMOTE_TO_CONTINUATION_RESEARCH`

This closes the baseline-integrity gate. It does not authorize production use, performance claims, or combination with reversal before the continuation branch demonstrates independent value.

## Next planned work package

`DTR-NQ-WP-20260721-02 — Independent continuation engine`

The continuation branch must use the locked gap-safe data contract and be evaluated independently before any adaptive routing or combination with the reversal candidate.
