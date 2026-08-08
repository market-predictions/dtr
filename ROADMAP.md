# DTR Optimization Lab Roadmap

## Priority 0 — Permanent private market-data cache

Status: **active and mandatory**

- [x] Create canonical private Drive hierarchy for historic Dukascopy sources.
- [x] Preserve exact source archives for ten FX pairs.
- [x] Register archive and part SHA-256 values.
- [x] Add root cache-first controls and a deterministic restore utility.
- [x] Complete a real EURUSD reconstruction and extraction drill.
- [ ] Add a second encrypted off-provider mirror.
- [ ] Add periodic integrity and permission audits.
- [ ] Register incremental partitions after 2026-07-24 without mutating frozen history.

Canonical folder ID: `160qGdjm9Gi6pr05nRHuUXaTZc9EgJOOU`.

## Priority 0A — Dukascopy FX Cash research memory

Status: **implementation complete; independent assurance pending**

- [x] Adopt canonical research name **Dukascopy FX Cash** and stable machine dataset ID without breaking the legacy catalog key.
- [x] Define a repository-wide falsification-first research standard above the existing cache/provenance layer.
- [x] Add immutable `DFXC-*` study IDs, normalized study/result records and deterministic human/machine indexes.
- [x] Make exact branch + commit + artifact paths first-class so branch-resident research remains recoverable.
- [x] Preserve negative findings, holdout exposure, authorized next steps and prohibited rescue steps.
- [x] Add validator/tests that reject dataset/pair drift, inconsistent result/index state and unregistered study directories.
- [x] Seed Quarters Theory and recent classic-pivot research from frozen historical branch evidence.
- [x] Add a migration queue for older Dukascopy FX Cash strategy branches.
- [ ] Complete independent assurance of `DTR-DFXC-WP-20260808-01`.
- [ ] Merge the assured registry to `main` and make it mandatory for all subsequent Dukascopy FX Cash studies.
- [ ] Backfill the highest-value older Stacey Burke, Asian Sweep, DTR-FX and Wayne McDonnell studies from immutable evidence.

## Phase 0 — Data and execution validity

Status: **active; deployment-blocking**

- [x] Register dataset checksum, schema, gaps, and export-cap warning.
- [x] Preserve the 504-trade observe-only reference.
- [x] Identify and correct retrospective post-entry gap rejection.
- [x] Refreeze the causal 495-trade benchmark.
- [x] Add timestamp/VWAP hypothesis tests.
- [x] Add rollover sensitivity and discontinuity diagnostics.
- [x] Add deterministic uncertainty and concentration evidence.
- [ ] Resolve bar-open versus bar-close semantics from authoritative metadata or a qualified replacement dataset.
- [ ] Resolve continuous-contract roll and adjustment methodology.
- [ ] Build canonical qualified one-minute and five-minute datasets with provenance.

## Phase 1 — Reversal baseline

Status: **corrected historical research benchmark complete**

- [x] Implement session, sweep, reclaim, protected pivot, BOS, impulse, acceptance, regime, entry, stop, target, and time-exit logic.
- [x] Use one-minute execution with conservative collision handling.
- [x] Correct BOS/impulse funnel instrumentation.
- [x] Lock `DTR_PY_NQ_CANDIDATE_0_1_CAUSAL_GAP` at 495 trades.
- [ ] Complete multiple-testing-aware historical selection analysis.

Decision: `CONTINUE_RESEARCH_DO_NOT_DEPLOY`.

## Phase 2 — Independent modules

Status: **no-retune corrected-baseline reruns complete**

- [x] Continuation: `HOLD_FOR_FRESH_DATA`.
- [x] IFVG: `REJECT_NO_INCREMENTAL_VALUE`.
- [x] CISD: `REJECT_NO_INCREMENTAL_VALUE`.
- [x] Entry routing: corrected local rerun confirms `REJECT_NO_INCREMENTAL_VALUE`; PR #5 must be rebased and closed.
- [ ] Session VWAP context only after timestamp semantics are resolved.
- [ ] Weekly VWAP context only after timestamp semantics are resolved.
- [ ] H1Vol and higher-timeframe context only after fresh baseline evidence.
- [ ] Footprint only with suitable historical order-flow data.

## Phase 3 — Fresh out-of-sample evidence

Status: **preregistered; data not acquired**

- [x] Commit the 2026 OOS data qualification and pass/fail specification.
- [ ] Acquire qualified NQ one-minute data through at least 2026-07-21.
- [ ] Freeze dataset checksum and audit before performance inspection.
- [ ] Run the corrected manifest with zero parameter changes.
- [ ] Report return, funnel, concentration, costs, and roll attribution.
- [ ] Extend forward rather than retune when the sample is underpowered or ambiguous.

Passing authorizes continued paper research only.

## Phase 4 — Model-selection robustness

Status: **partially implemented**

- [x] Historical chronological slices.
- [x] Historical rolling walk-forward procedure.
- [x] Cost, block-bootstrap, concentration, and rollover stress.
- [ ] Reconstruct an aligned candidate-return matrix or rerun a fully locked selection procedure.
- [ ] Apply multiple-testing-aware selection inference.
- [ ] Run nested walk-forward only under a preregistered candidate set.

## Phase 5 — Pine and execution parity

Status: **blocked**

- [ ] Port only a fresh-data-supported finalist to Pine Script v6.
- [ ] Reconcile Python and Pine signals and trades one-for-one over a controlled period.
- [ ] Validate session boundaries, scheduled closes, costs, Bar Magnifier, and whole-contract risk.
- [ ] Complete paper-forward observation before any production decision.
