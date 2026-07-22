# DTR Optimization Lab Roadmap

## Phase 0 — Data and execution validity

Status: **active; deployment-blocking**

- [x] Register dataset checksum, schema, gaps, and export-cap warning.
- [x] Preserve the 504-trade observe-only reference.
- [x] Identify and correct retrospective post-entry gap rejection.
- [x] Refreeze the causal 495-trade benchmark.
- [x] Add timestamp/VWAP hypothesis tests.
- [x] Run maintenance-boundary census and fixed timing sensitivity.
- [x] Add rollover, uncertainty, concentration and cost evidence.
- [x] Qualify a temporary Dukascopy USA500 one-minute proxy dataset.
- [x] Add provider-neutral source adapters and data-integrity contracts.
- [ ] Resolve NQ timestamp semantics from authoritative metadata or replacement data.
- [ ] Resolve NQ continuous-contract roll and adjustment methodology.
- [ ] Acquire actual contract-audited ES futures data.

## Phase 1 — Reversal baseline

Status: **causal reference complete; timing-corrected exploratory baseline added**

- [x] Implement and validate the reversal engine.
- [x] Lock the 495-trade causal regression reference.
- [x] Freeze the 477-trade timing-corrected comparator.
- [ ] Complete current-code causal selection inference after timestamp scope is finalized.

Decision: `CONTINUE_RESEARCH_DO_NOT_DEPLOY`.

## Phase 2 — E6 historical programme

Status: **complete**

- [x] Complete advanced context research and freeze E5/E6 challengers.
- [x] Retain Tuesday–Friday and all three sessions.
- [x] Support the E6 mechanism without changing the 0.25 ATR threshold.
- [x] Complete path, reward-space, sequencing, event, rollover and risk diagnostics.
- [x] Promote `E6_NO_FOMC_DAY` as the user-mandated NQ working baseline while preserving E6 as control.
- [x] Recalibrate 0.50%, 1.00% and 1.50% risk on the no-FOMC baseline.
- [x] Preserve 0.50% and 1.00% as paper-research envelopes; classify 1.50% as aggressive.

Do not add another historical filter, event buffer or sizing optimization to the 2023–2025 NQ sample.

## Phase 3 — Fresh out-of-sample and cross-market evidence

Status: **initial proxy replication complete; stronger evidence still required**

- [x] Commit the 2026 NQ OOS data qualification specification.
- [x] Define original E6 and E6 no-FOMC before fresh or cross-market inspection.
- [x] Qualify Dukascopy `USA500.IDX/USD` as an S&P 500 bid-CFD proxy.
- [x] Build a provider-neutral NQ-versus-USA500 parallel framework.
- [x] Reproduce both NQ baselines exactly through the parallel framework.
- [x] Run unchanged original E6 and E6 no-FOMC proxy replication.
- [x] Keep instruments separate and prohibit pooled performance.
- [x] Classify the initial proxy result as `PARTIAL_COST_FRAGILE_REPLICATION`.
- [ ] Extend the unchanged USA500 proxy test materially beyond 2022–2025.
- [ ] Acquire qualified NQ one-minute data through at least 2026-07-21.
- [ ] Acquire materially longer, contract-audited NQ history.
- [ ] Acquire and qualify actual ES futures data.
- [ ] Run unchanged E6 and E6 no-FOMC on actual ES.
- [ ] Extend forward rather than retune when evidence is ambiguous.

Passing any one replication gate authorizes continued paper research only.

## Phase 4 — Model-selection robustness

Status: **original reconstruction blocked; explicit current-code primitives implemented**

- [x] Historical chronological and rolling walk-forward slices.
- [x] Cost, block-bootstrap, concentration, rollover, event and fixed-fraction stress.
- [x] Independent reconstruction of E6 advanced blocks and no-FOMC calibration.
- [x] Independent reconstruction of the NQ-USA500 proxy comparison.
- [x] Deterministic repeat of all comparable cross-market artifacts.
- [ ] Complete the separately labelled current-code causal universe after timestamp alignment.
- [ ] Run nested walk-forward only under a preregistered candidate set.

## Phase 5 — Pine and execution parity

Status: **blocked**

- [ ] Port only a fresh-data-supported finalist to Pine Script v6.
- [ ] Reconcile Python and Pine signals and trades one-for-one.
- [ ] Validate session boundaries, scheduled closes, costs, Bar Magnifier and whole-contract risk.
- [ ] Complete paper-forward observation before any production decision.
