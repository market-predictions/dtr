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

Decision: retain the existing NQ futures dataset as the sole optimization base for the current program. Dukascopy and other providers remain documented future options for longer-history and cross-market validation; no acquisition implementation is scheduled before the NQ roadmap reaches a significant research gate.

Assessment: `docs/DUKASCOPY_DATA_SOURCE_REVIEW_2026-07-21.md`

- [x] Review `giuse88/duka`, the underlying Dukascopy feed concept, current alternatives, and fit with the DTR architecture.
- [x] Decide not to adopt the legacy `giuse88/duka` package as a production dependency.
- [x] Define a possible provider-neutral integration path for later use.
- [ ] Resume only after an explicit future work-package decision.

## Phase 1 — Python reversal baseline

Status: **reference candidate frozen; gap-safe rerun pending local dataset execution**

- [x] Implement the three DTR session ranges.
- [x] Implement first one-sided sweep, reclaim, and protected-pivot logic.
- [x] Implement configurable BOS/MSS, impulse, and acceptance logic.
- [x] Implement break-close and retest entries.
- [x] Implement regime, weekday, and session filters.
- [x] Implement structural/ATR stops, TP1, runner, breakeven, time close, and maximum hold.
- [x] Implement one-minute intrabar execution with conservative collision handling.
- [x] Build setup-funnel and attribution reporting.
- [x] Produce the first NQ reversal research candidate.
- [x] Add a strict YAML research-manifest schema.
- [x] Add dataset checksum verification.
- [x] Add deterministic artifact generation and frozen-baseline checks.
- [x] Preserve `DTR_PY_NQ_CANDIDATE_0_1` as an explicit `observe_only` reference run.
- [x] Add `DTR_PY_NQ_CANDIDATE_0_1_GAP_SAFE` with identical strategy parameters and `reject_unsafe` execution.
- [ ] Execute both manifests against the local NQ dataset.
- [ ] Confirm the reference run reproduces 504 trades, 84.164359R net, and 14.107858R maximum drawdown.
- [ ] Lock the gap-safe trade log, artifact hashes, funnel deltas, and regression tolerances.

## Phase 2 — Data integrity and reproducibility gate

Status: **implementation complete; source-data rerun and timestamp/rollover work remain**

- [x] Classify maintenance, weekend, holiday, offset, missing-data, and unexplained timestamp gaps.
- [x] Attach deterministic reset and unsafe-gap epochs to derived five-minute bars.
- [x] Reject session ranges containing reset boundaries under the gap-safe policy.
- [x] Truncate sweep/reclaim/BOS/acceptance paths at the first reset boundary.
- [x] Reject open trades that bridge unsafe gaps from primary performance results.
- [x] Report observed unsafe bridges without changing the frozen reference result.
- [x] Make gap policy explicit and versioned in every research manifest.
- [x] Add focused tests for intra-bucket gaps, range contamination, signal-path resets, trade bridges, and policy separation.
- [x] Record code commit, dataset hash, manifest hash, execution assumptions, and integrity counters in generated runs.
- [x] Add an independent research-review checklist before candidate promotion.
- [ ] Run the reference and gap-safe manifests on the full local NQ dataset and compare every changed trade.
- [ ] Detect probable contract-roll discontinuities and test state resets around them.
- [ ] Confirm daylight-saving and bar-open/bar-close assumptions.
- [ ] Verify session boundaries with targeted source-data fixtures.
- [ ] Reconstruct and validate supplied RTH/ETH VWAP fields.

Promotion gate: Phase 3 may begin only after the reference rerun passes and the gap-safe result has a versioned comparison report. Timestamp and rollover limitations may remain open only if they are explicitly isolated from the first continuation experiments.

## Phase 3 — Independent continuation engine

Status: **next research phase after baseline-integrity rerun**

The continuation branch will be developed and measured independently before combination with reversal.

- [ ] Implement accepted range breakouts.
- [ ] Test one-bar and two-bar acceptance.
- [ ] Test immediate breakout and first-pullback entries.
- [ ] Add displacement, VWAP, efficiency-ratio, and distance-from-range filters.
- [ ] Add failed-breakout invalidation.
- [ ] Optimize continuation-specific stops and exits.
- [ ] Report performance by session, weekday, direction, and regime.
- [ ] Require independently positive walk-forward evidence before combination.

## Phase 4 — Entry and context modules

Status: **not started**

Order of research:

1. IFVG entry confirmation.
2. CISD entry confirmation.
3. First-pullback and hybrid entry routing.
4. Session VWAP as information, score, soft gate, and hard gate.
5. Weekly VWAP as information, score, soft gate, and hard gate.
6. H1Vol conditioning.
7. Higher-timeframe structure and context scoring.
8. Footprint only when suitable historical order-flow data is available.

Each module must demonstrate independent value and opportunity coverage before entering a composite model.

## Phase 5 — Robustness and model selection

Status: **partially implemented**

- [x] Initial chronological development, validation, and later-research slices.
- [x] Initial rolling walk-forward tests.
- [x] Transaction-cost and slippage stress.
- [x] Initial parameter-neighbourhood analysis.
- [x] Bootstrap/Monte Carlo trade-sequence analysis.
- [ ] Nested walk-forward selection with locked experiment manifests.
- [ ] Regime-removal and session-removal stress tests.
- [ ] Frozen paper-forward test on post-December-2025 NQ data.
- [ ] Cross-market execution validation on additional licensed futures datasets after the NQ program.
- [ ] Cross-asset and structural-proxy validation only under a future approved provider work package.

## Phase 6 — Adaptive DTR model

Status: **not started**

- [ ] Route reversal only in regimes where reversal has demonstrated edge.
- [ ] Route continuation only in regimes where continuation has demonstrated edge.
- [ ] Maintain a no-trade state when neither branch is qualified.
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
