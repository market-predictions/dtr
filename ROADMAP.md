# DTR Optimization Lab Roadmap

## Phase 0 — Data and execution validity

Status: **active; deployment-blocking**

- [x] Register dataset checksum, schema, gaps, and export-cap warning.
- [x] Preserve the 504-trade observe-only reference.
- [x] Identify and correct retrospective post-entry gap rejection.
- [x] Refreeze the causal 495-trade benchmark.
- [x] Add timestamp/VWAP hypothesis tests.
- [x] Run maintenance-boundary census; internal evidence strongly supports bar-close labels.
- [x] Run fixed nearby timing sensitivity without changing strategy logic.
- [x] Add rollover sensitivity and discontinuity diagnostics.
- [x] Add deterministic uncertainty and concentration evidence.
- [ ] Resolve timestamp semantics from authoritative metadata or a qualified replacement dataset.
- [ ] Resolve continuous-contract roll and adjustment methodology.
- [ ] Build canonical qualified one-minute and five-minute datasets with provenance.

## Phase 1 — Reversal baseline

Status: **causal reference complete; timing-corrected exploratory baseline added**

- [x] Implement session, sweep, reclaim, protected pivot, BOS, impulse, acceptance, regime, entry, stop, target, and time-exit logic.
- [x] Use one-minute execution with conservative collision handling.
- [x] Correct BOS/impulse funnel instrumentation.
- [x] Lock `DTR_PY_NQ_CANDIDATE_0_1_CAUSAL_GAP` at 495 trades as the historical causal regression reference.
- [x] Freeze `DTR_CAUSAL_BAR_CLOSE_RANGE_SHIFT_MINUS1` at 477 trades as the exploratory timestamp-corrected comparator.
- [ ] Complete current-code causal selection inference after timestamp scope is finalized.

Decision: `CONTINUE_RESEARCH_DO_NOT_DEPLOY`.

## Phase 2 — Independent modules and context

Status: **E6 mechanism, filters and sequencing complete; event attribution next**

- [x] Continuation: `HOLD_FOR_FRESH_DATA`.
- [x] IFVG: `REJECT_NO_INCREMENTAL_VALUE`.
- [x] CISD: `REJECT_NO_INCREMENTAL_VALUE`.
- [x] Entry routing: `REJECT_NO_INCREMENTAL_VALUE`.
- [x] D1/H4 direction, volatility, trend strength, range quality, prior-day/week location, overnight gap, volume and VWAP context.
- [x] Reject historical promotion of all context filters.
- [x] Freeze compressed-range E5 and prior-day-proximity E6 as fresh-OOS challengers.
- [x] Retain Tuesday–Friday and Asia, London and New York after factorial testing.
- [x] Freeze the E6 advanced-test framework and machine-readable preregistration.
- [x] Execute Block 0 exact regression and Block 1 E6 mechanism audit.
- [x] Classify the E6 mechanism as `SUPPORTED` without changing the 0.25 ATR threshold.
- [x] Execute frozen path-quality family P1–P3.
- [x] Execute frozen reward-space family R1–R2 and shadow interaction I1.
- [x] Complete independent reconstruction and deterministic-repeat checkpoint.
- [x] Record no new filter `FRESH_OOS_CHALLENGER`; retain E6 unchanged.
- [x] Execute frozen sequencing family S1–S3.
- [x] Retain S0 global sequencing; reject first-trade-only, cooldown and one-third-risk session sleeves.
- [ ] Complete official-event, holiday and rollover attribution.
- [ ] Complete fixed-fraction equity and cost stress for E6.
- [ ] Footprint only with suitable historical order-flow data.

Historical work may nominate fresh-OOS challengers only. It cannot replace E6 or authorize Pine.

## Phase 3 — Fresh out-of-sample evidence

Status: **baseline and context challengers preregistered; data not acquired**

- [x] Commit the 2026 OOS data qualification and pass/fail specification.
- [x] Define Arms 0/A/B and shadow Arm C before fresh performance inspection.
- [ ] Acquire qualified NQ one-minute data through at least 2026-07-21.
- [ ] Freeze dataset checksum and audit before performance inspection.
- [ ] Run Arms 0/A/B with zero parameter changes.
- [ ] Add at most one E6-derived advanced challenger only if a future frozen block passes the nomination gates.
- [ ] Report paired per-session differences, return, funnel, concentration, costs, and roll attribution.
- [ ] Extend forward rather than retune when the sample is underpowered or ambiguous.

Passing authorizes continued paper research only.

## Phase 4 — Model-selection robustness

Status: **original reconstruction blocked; explicit current-code primitives implemented**

- [x] Historical chronological slices.
- [x] Historical rolling walk-forward procedure.
- [x] Cost, block-bootstrap, concentration, and rollover stress.
- [x] Classify original staged 904 reconstruction as blocked by missing leaderboards and stage bases.
- [x] Implement aligned session/date return matrices, stream hashes, duplicate detection, max-t, best-mean and reselection primitives.
- [x] Apply joint market-date max-t inference to E6 path and reward-space families.
- [x] Apply the same frozen inference to sequencing S1–S3.
- [ ] Complete the separately labelled current-code causal universe only after timestamp alignment is finalized.
- [ ] Run nested walk-forward only under a preregistered candidate set.

## Phase 5 — Pine and execution parity

Status: **blocked**

- [ ] Port only a fresh-data-supported finalist to Pine Script v6.
- [ ] Reconcile Python and Pine signals and trades one-for-one over a controlled period.
- [ ] Validate session boundaries, scheduled closes, costs, Bar Magnifier, and whole-contract risk.
- [ ] Complete paper-forward observation before any production decision.
