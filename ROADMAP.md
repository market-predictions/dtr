# DTR Optimization Lab Roadmap

## Phase 0 — Data and execution validity

Status: **working timestamp interpretation resolved; contract provenance still deployment-blocking**

- [x] Register dataset checksum, schema, gaps and export-cap warning.
- [x] Correct retrospective post-entry gap rejection.
- [x] Preserve the 495-trade execution regression benchmark.
- [x] Run maintenance-boundary timestamp census.
- [x] Confirm 732 normal `17:00 → 18:01` pairs and zero normal `16:59 → 18:00` pairs.
- [x] Retain shift-minus-one as the working bar-close interpretation.
- [x] Add rollover, uncertainty, concentration and cost evidence.
- [x] Qualify temporary Dukascopy USA500 data and build provider-neutral adapters.
- [ ] Resolve NQ continuous-contract roll and adjustment methodology.
- [ ] Obtain authoritative source documentation where possible; this is no longer a binary engine-choice blocker after the census.

## Phase 1 — Scientific reference and evidence hierarchy

Status: **corrected and frozen**

- [x] Preserve `DTR_CAUSAL_BAR_CLOSE_RANGE_SHIFT_MINUS1` as the 477-trade scientific NQ reference control.
- [x] Preserve original E6 as a frozen historical challenger.
- [x] Relabel `E6_NO_FOMC_DAY` as the user-selected working policy candidate.
- [x] State explicitly that no deployment baseline exists.
- [x] Recalculate fixed-fraction risk on the neutral 477-trade reference.
- [x] Retain all filtered risk curves as conditional scenario analyses only.

Decision: `CONTINUE_RESEARCH_DO_NOT_DEPLOY`.

## Phase 2 — Historical NQ programme

Status: **closed against further hypothesis search**

- [x] Complete context, session, sequencing, path, event, rollover and risk diagnostics.
- [x] Apply within-stage multiple-testing controls where reconstructible.
- [x] Classify the original 904-selection chronology as permanently unreconstructible from surviving artifacts.
- [x] Freeze further 2023–2025 NQ threshold, weekday, session, event, entry, exit, sequencing, interaction and sizing searches.

Do not use the current NQ sample to create another candidate rule.

## Phase 3 — Dukascopy Nasdaq-proxy source validation and fresh evidence

Status: **preregistered; acquisition and execution in progress**

- [x] Freeze the source-validation and 2026 OOS design before downloading or inspecting 2026 proxy performance.
- [ ] Acquire temporary `usatechidxusd` one-minute data from 2022-01-01 through 2026-07-23 end-exclusive.
- [ ] Audit annual hashes, timestamps, OHLC, missing intervals, DST conversion, session coverage and discontinuities.
- [ ] Attempt matching ask data; otherwise use bid data with explicit conservative costs.
- [ ] Compare 2022–2025 NQ futures and proxy one-minute/five-minute/daily returns, session ranges, ATR and strategy decisions.
- [ ] Determine whether Dukascopy is a credible research-continuation proxy for NQ.
- [ ] Run sealed 2026 proxy OOS arms: unfiltered reference, fixed E6 and fixed E6 no-FOMC.
- [ ] Compare E6 incrementally against the unfiltered control and no-FOMC incrementally against E6.
- [ ] Delete raw proxy data after research completion and preserve only hashes, audits and compact evidence.
- [ ] Acquire qualified fresh CME NQ data when available; proxy evidence cannot replace futures validation.

## Phase 4 — Repository consolidation and independent review

Status: **active**

- [x] Freeze the deep stack while the timestamp gate was reviewed.
- [ ] Create a squashed consolidated research snapshot against `main` after final six-step evidence is committed.
- [ ] Close or mark PRs #7–#18 as superseded by the consolidated snapshot while preserving links and auditability.
- [ ] Require an independent verifier to reconstruct census, risk, proxy qualification, concordance and OOS results.
- [ ] Require the independent verifier to audit completion against this roadmap.

## Phase 5 — Pine and execution parity

Status: **blocked**

- [ ] Port only a fresh-data-supported finalist to Pine Script v6.
- [ ] Reconcile Python and Pine signals and trades one-for-one.
- [ ] Validate session boundaries, scheduled closes, costs, Bar Magnifier and whole-contract risk.
- [ ] Complete paper-forward observation before any production decision.
