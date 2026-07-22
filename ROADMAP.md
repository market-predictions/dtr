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

Status: **bounded E6 historical programme complete**

- [x] Continuation: `HOLD_FOR_FRESH_DATA`.
- [x] IFVG: `REJECT_NO_INCREMENTAL_VALUE`.
- [x] CISD: `REJECT_NO_INCREMENTAL_VALUE`.
- [x] Entry routing: `REJECT_NO_INCREMENTAL_VALUE`.
- [x] Complete D1/H4/weekly context study and reject historical promotion.
- [x] Freeze E5 and E6 as fresh-OOS challengers.
- [x] Retain Tuesday–Friday and all three sessions after factorial testing.
- [x] Freeze the E6 advanced-test framework.
- [x] Support the E6 mechanism without changing the 0.25 ATR threshold.
- [x] Complete P1–P3 path-quality and R1–R2 reward-space families; no new filter advanced.
- [x] Complete sequencing S1–S3; retain S0 global sequencing.
- [x] Complete official FOMC, CPI, NFP, expiration, early-close, holiday and rollover attribution.
- [x] Preserve FOMC-pre and expiration/roll overlap as fixed future risk-watch cohorts only.
- [x] Reject historical event exclusions and alternate event-window search.
- [x] Complete fixed-fraction equity and execution-cost stress for unchanged E6.
- [x] Preserve 0.50% and 1.00% as paper-research envelopes; classify 1.50% as aggressive.
- [ ] Footprint only with suitable historical order-flow data.

Do not add another historical filter, event rule or sizing optimization to the 2023–2025 NQ sample.

## Phase 3 — Fresh out-of-sample and replication evidence

Status: **preregistered; required data not acquired**

- [x] Commit the 2026 OOS data qualification and pass/fail specification.
- [x] Define Arms 0/A/B and shadow Arm C before fresh performance inspection.
- [ ] Acquire qualified NQ one-minute data through at least 2026-07-21.
- [ ] Freeze dataset checksum and audit before performance inspection.
- [ ] Run Arms 0/A/B with zero parameter changes.
- [ ] Carry FOMC-pre and expiration/roll-overlap as descriptive tags only.
- [ ] Report paired return, funnel, concentration, costs, roll and fixed-fraction risk attribution.
- [ ] Extend forward rather than retune when the sample is underpowered or ambiguous.
- [ ] Acquire materially longer, contract-audited NQ history for unchanged replication.
- [ ] Run unchanged E5/E6 and P3 replication on ES without pooling instruments.

Passing authorizes continued paper research only.

## Phase 4 — Model-selection robustness

Status: **original reconstruction blocked; explicit current-code primitives implemented**

- [x] Historical chronological slices.
- [x] Historical rolling walk-forward procedure.
- [x] Cost, block-bootstrap, concentration, rollover, event and fixed-fraction stress.
- [x] Classify original staged 904 reconstruction as blocked by missing leaderboards and stage bases.
- [x] Implement aligned return matrices, stream hashes, duplicate detection and max-t primitives.
- [x] Apply frozen inference to E6 path, reward-space and sequencing families.
- [x] Independently reconstruct event, rollover and equity-risk attribution.
- [ ] Complete the separately labelled current-code causal universe only after timestamp alignment is finalized.
- [ ] Run nested walk-forward only under a preregistered candidate set.

## Phase 5 — Pine and execution parity

Status: **blocked**

- [ ] Port only a fresh-data-supported finalist to Pine Script v6.
- [ ] Reconcile Python and Pine signals and trades one-for-one over a controlled period.
- [ ] Validate session boundaries, scheduled closes, costs, Bar Magnifier, and whole-contract risk.
- [ ] Complete paper-forward observation before any production decision.
