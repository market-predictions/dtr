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

Status: **completed as proxy evidence; CME validation remains open**

- [x] Freeze the source-validation and 2026 OOS design before downloading or inspecting 2026 proxy performance.
- [x] Acquire temporary `usatechidxusd` one-minute data from 2022-01-01 through 2026-07-23 end-exclusive.
- [x] Audit annual hashes, timestamps, OHLC, missing intervals, DST conversion, session coverage and discontinuities.
- [x] Attempt matching ask data; retain bid data with explicit conservative costs where the ask route was incomplete.
- [x] Compare 2022–2025 NQ futures and proxy one-minute/five-minute/daily returns, session ranges, ATR and strategy decisions.
- [x] Determine that Dukascopy is a credible research-continuation proxy for NQ.
- [x] Run sealed 2026 proxy OOS arms: unfiltered reference, fixed E6 and fixed E6 no-FOMC.
- [x] Compare E6 incrementally against the unfiltered control and no-FOMC incrementally against E6.
- [x] Delete raw proxy data after research completion and preserve only hashes, audits and compact evidence.
- [ ] Acquire qualified fresh CME NQ data; proxy evidence cannot replace futures validation.

## Phase 4 — USA500/ES baseline discovery

Status: **bounded proxy programme completed; no baseline promoted**

- [x] Start from the USA500 unfiltered core rather than the NQ E6 candidate.
- [x] Freeze and run the Monday × Asia factorial.
- [x] Confirm that Monday worsens the portfolio and removing Asia improves but does not repair it.
- [x] Preregister and run bounded session decomposition after no factorial arm passed.
- [x] Identify London-only as a positive diagnostic and New York/Asia as negative contributors.
- [x] Reject London-only promotion because 2022 and 2025 were negative, uncertainty crossed zero and four-tick expectancy was negative.
- [x] Test six fixed context rules without threshold search or interactions.
- [x] Test FOMC, CPI, NFP, monthly option-expiration and quarterly expiration policies one at a time.
- [x] Retain NQ E6 and NQ E6 no-FOMC as external controls only.
- [x] Complete independent calculation and roadmap review.
- [x] Apply the stop rule: no context or event optimization on London-only after the session gate failed.

Decision: `NO_VIABLE_USA500_CORE_BASELINE`.

Do not continue neighboring USA500 threshold, session-time, event-buffer or interaction searches on this sample.

### Next legitimate ES work

Choose one evidence path before reopening development:

1. acquire actual contract-audited ES one-minute futures data and replicate the frozen core and London diagnostic unchanged;
2. preregister a new ES-specific core-development programme with nested chronology: 2022–2023 development, 2024 confirmation and 2025 locked evaluation;
3. run a mechanism study explaining why London works better than New York and Asia before modifying the core.

## Phase 5 — Repository consolidation and independent review

Status: **active**

- [x] Freeze the deep stack while the timestamp gate was reviewed.
- [ ] Create a squashed consolidated research snapshot against `main` after final evidence is committed.
- [ ] Close or mark PRs #7–#21 as superseded by the consolidated snapshot while preserving links and auditability.
- [x] Require independent verifiers for census, risk, proxy qualification, concordance, OOS and USA500 decisions.
- [x] Require roadmap-compliance review for the USA500 programme.

## Phase 6 — Pine and execution parity

Status: **blocked**

- [ ] Port only a fresh-data-supported finalist to Pine Script v6.
- [ ] Reconcile Python and Pine signals and trades one-for-one.
- [ ] Validate session boundaries, scheduled closes, costs, Bar Magnifier and whole-contract risk.
- [ ] Complete paper-forward observation before any production decision.
