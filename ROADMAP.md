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

Status: **planned; non-blocking for the current NQ baseline**

Decision: retain the existing NQ futures dataset as the frozen reference for the current reversal candidate. Introduce Dukascopy later as a secondary provider for longer-history and cross-market structural validation. Dukascopy index CFDs must not be presented as CME futures data.

Assessment: `docs/DUKASCOPY_DATA_SOURCE_REVIEW_2026-07-21.md`

- [x] Review `giuse88/duka`, the underlying Dukascopy feed concept, current alternatives, and fit with the DTR architecture.
- [x] Decide not to adopt the legacy `giuse88/duka` package as a production dependency.
- [x] Define the preferred path: a Python adapter over approved official Dukascopy API access, with a pinned `dukascopy-node` run as an independent comparison oracle.
- [ ] Confirm and document API access, automation permission, data-use terms, and any required key before bulk acquisition.
- [ ] Define a provider interface and canonical schema that preserve provider, instrument type, UTC timestamps, bar semantics, bid/ask side, spread, volume meaning, point value, session calendar, and checksums.
- [ ] Add live instrument-catalog discovery and freeze the metadata used by each acquisition manifest.
- [ ] Implement resumable, rate-limited, cached, and checksum-verified one-minute acquisition without silently filling missing bars.
- [ ] Add provider-specific data audits for price scale, duplicates, gaps, session breaks, timestamp boundaries, bid/ask consistency, and volume semantics.
- [ ] Pilot `EURUSD`, `XAUUSD`, `USA500IDXUSD`, `USATECHIDXUSD`, and `USA30IDXUSD` when available in the live catalog.
- [ ] Derive canonical five-minute bars from one-minute source data and verify aggregation boundaries.
- [ ] Compare controlled pilot windows against an official Dukascopy/JForex reference and a pinned `dukascopy-node` result.
- [ ] Register approved canonical datasets in `data/catalog.yaml`; keep raw responses and bulk data outside Git.
- [ ] Promote Dukascopy to an approved research provider only after deterministic reruns reproduce canonical hashes and audit artifacts.

This workstream may proceed in parallel after the current NQ integrity gate. It does not block the continuation engine, but it must pass before Dukascopy data is used for Phase 5 cross-market claims or parameter selection.

## Phase 1 — Python reversal baseline

Status: **research candidate available; reproducibility gate in progress**

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
- [ ] Run the manifest end-to-end in CI/local research infrastructure.
- [ ] Lock generated artifact hashes and regression tolerances.

## Phase 2 — Data integrity and reproducibility gate

Status: **in progress**

- [ ] Classify maintenance, weekend, holiday, rollover, and unexplained gaps.
- [ ] Detect probable roll discontinuities and reset strategy state around unsafe gaps.
- [ ] Confirm daylight-saving and bar-open/bar-close assumptions.
- [ ] Verify session boundaries with targeted source-data fixtures.
- [ ] Reject trades that cross unexplained market-data gaps.
- [ ] Generate every committed result from a versioned manifest.
- [ ] Record code commit, dataset hash, manifest hash, and execution assumptions in every run.
- [ ] Add an independent regression-review checklist before candidate promotion.

## Phase 3 — Continuation engine

Status: **not started**

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
- [ ] Cross-market execution validation on additional licensed futures datasets.
- [ ] Fixed-candidate structural-proxy validation on approved Dukascopy index CFDs; do not pool or label these results as NQ/ES/YM futures performance.
- [ ] Cross-asset validation on approved FX and metals data using asset-specific sessions, spreads, point values, and cost models.
- [ ] Compare a common overlap window across markets before using each instrument's longer independent history.
- [ ] Permit asset-specific retuning only after the frozen candidate has been evaluated without retuning.
- [ ] Frozen paper-forward test on post-December-2025 NQ data.

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
