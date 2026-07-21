# DTR Optimization Lab Roadmap

## Phase 0 — Repository and data foundation

Status: **partially complete**

- [x] Initialize repository and Python package.
- [x] Exclude raw datasets and generated artifacts from Git history.
- [x] Register the uploaded NQ dataset with checksum and schema.
- [x] Add loader, audit, resampling, tests, and CI.
- [x] Exclude the incomplete final source date from research runs.
- [ ] Resolve source timestamp semantics conclusively.
- [ ] Determine continuous-contract, rollover, and adjustment methodology.
- [ ] Reconstruct and verify RTH/ETH session boundaries and VWAP resets.
- [ ] Produce canonical one-minute and five-minute Parquet datasets with provenance metadata.

## Phase 0B — Provider-neutral market-data acquisition

Status: **deferred; not part of the current NQ optimization phase**

Decision: retain the existing NQ futures dataset as the sole optimization base for the current program. Dukascopy and other providers remain documented future options; no acquisition implementation is scheduled before a future explicit work-package decision.

Assessment: `docs/DUKASCOPY_DATA_SOURCE_REVIEW_2026-07-21.md`

- [x] Review the legacy Duka package, underlying Dukascopy feed concept, current alternatives, and architectural fit.
- [x] Decide not to adopt the legacy package as a production dependency.
- [x] Define a possible provider-neutral integration path for later use.
- [ ] Resume only after an explicit future work-package decision.

## Phase 1 — Python reversal baseline

Status: **complete; reference and gap-safe baselines frozen**

- [x] Implement the three DTR session ranges.
- [x] Implement first one-sided sweep, reclaim, and protected-pivot logic.
- [x] Implement configurable BOS/MSS, impulse, and acceptance logic.
- [x] Implement break-close and retest entries.
- [x] Implement regime, weekday, and session filters.
- [x] Implement structural/ATR stops, TP1, runner, breakeven, time close, and maximum hold.
- [x] Implement one-minute intrabar execution with conservative collision handling.
- [x] Build setup-funnel and attribution reporting.
- [x] Produce the first NQ reversal research candidate.
- [x] Add strict YAML manifests, dataset checksum verification, deterministic artifacts, and regression checks.
- [x] Preserve `DTR_PY_NQ_CANDIDATE_0_1` as the 504-trade observe-only reference.
- [x] Add and execute `DTR_PY_NQ_CANDIDATE_0_1_GAP_SAFE` with identical strategy parameters.
- [x] Lock the 491-trade gap-safe log, metrics, artifact hashes, funnel deltas, and regression tolerances.

## Phase 2 — Data integrity and reproducibility gate

Status: **baseline-integrity gate complete; timestamp and rollover research remain open**

- [x] Classify maintenance, weekend, holiday, offset, missing-data, and unexplained timestamp gaps.
- [x] Attach deterministic reset and unsafe-gap epochs to derived five-minute bars.
- [x] Reject session ranges containing reset boundaries under the gap-safe policy.
- [x] Truncate sweep/reclaim/BOS/acceptance paths at the first reset boundary.
- [x] Reject open trades that bridge unsafe gaps from primary performance results.
- [x] Report observed unsafe bridges without changing the frozen reference result.
- [x] Make gap policy explicit and versioned in every research manifest.
- [x] Add focused tests for range contamination, signal-path resets, trade bridges, and policy separation.
- [x] Record code, dataset, manifest, execution, and integrity provenance.
- [x] Run reference and gap-safe manifests and attribute every changed trade.
- [x] Complete independent review and deterministic clean-rerun hash lock.
- [ ] Detect probable contract-roll discontinuities and test state resets around them.
- [ ] Confirm daylight-saving and bar-open/bar-close assumptions.
- [ ] Verify session boundaries with targeted source-data fixtures.
- [ ] Reconstruct and validate supplied RTH/ETH VWAP fields.

## Phase 3 — Independent continuation engine

Status: **complete; no candidate promoted**

- [x] Implement accepted range breakouts.
- [x] Test one-bar and two-bar acceptance.
- [x] Test immediate breakout and first-pullback entries.
- [x] Record displacement, VWAP, efficiency-ratio, ADX, volume, extension, and timing diagnostics.
- [x] Add failed-breakout invalidation.
- [x] Test continuation-specific stops and exits.
- [x] Report performance by session, weekday, direction, entry route, and chronological period.
- [x] Run timing-neighbourhood, cost, session-removal, bootstrap, and walk-forward stress.
- [x] Perform independent review.

Decision: `HOLD_FOR_FRESH_DATA`. All unfiltered variants are negative. `CONT_A2_PULLBACK_LATE60` is retained as a research lead only; it may not be combined with reversal or tuned further on the current sample.

## Phase 4 — Entry and context modules

Status: **active; IFVG and CISD complete and rejected, entry routing next**

Research order and state:

1. [x] IFVG entry confirmation.
   - Decision: `REJECT_NO_INCREMENTAL_VALUE`.
   - Causal detector, manifest, tests, compact evidence, attribution, review, and handover retained.
   - No IFVG rule may enter the reversal candidate or be tuned further on the current sample.
2. [x] CISD entry confirmation.
   - Decision: `REJECT_NO_INCREMENTAL_VALUE`.
   - Broad confirmation reduces expectancy; the retest subset remains diagnostic only.
   - No CISD filter, sizing rule, or further tuning is authorized on the current sample.
3. [ ] First-pullback and hybrid entry routing — next work package.
4. [ ] Session VWAP as information, score, soft gate, and hard gate.
5. [ ] Weekly VWAP as information, score, soft gate, and hard gate.
6. [ ] H1Vol conditioning.
7. [ ] Higher-timeframe structure and context scoring.
8. [ ] Footprint only when suitable historical order-flow data is available.

Each module must demonstrate independent value, chronological stability, cost robustness, and acceptable opportunity coverage before entering a composite model. Rejected modules are not combined in search for a rescue effect.

## Phase 5 — Robustness and model selection

Status: **partially implemented**

- [x] Initial chronological development, validation, and later-research slices.
- [x] Initial rolling walk-forward tests.
- [x] Transaction-cost and slippage stress.
- [x] Initial parameter-neighbourhood analysis.
- [x] Bootstrap/Monte Carlo trade-sequence analysis.
- [x] Position-sequence attribution for filtered portfolios.
- [ ] Nested walk-forward selection with locked experiment manifests.
- [ ] Regime-removal and session-removal stress tests for any future promoted candidate.
- [ ] Frozen paper-forward test on post-December-2025 NQ data.
- [ ] Cross-market execution validation on additional licensed futures datasets after the NQ program.
- [ ] Cross-asset and structural-proxy validation only under a future approved provider work package.

## Phase 6 — Adaptive DTR model

Status: **not started**

- [ ] Route reversal only in regimes where reversal has demonstrated edge.
- [ ] Route continuation only if fresh data promotes the held continuation lead.
- [ ] Maintain a no-trade state when no branch is qualified.
- [ ] Compare one universal model against session-specific and regime-specific models.
- [ ] Select no more than three robust finalists.

## Phase 7 — Pine implementation and TradingView validation

Status: **parked**

- [ ] Port finalist logic to a clean Pine Script v6 strategy.
- [ ] Use market-aware whole-contract sizing and actual-risk reporting.
- [ ] Validate scheduled-close state consumption and fresh-setup lockout.
- [ ] Compare Python and Pine event timestamps on a controlled sample.
- [ ] Validate with realistic commission, slippage, and Bar Magnifier.
- [ ] Release a production candidate with full changelog, limitations, and roadmap.
