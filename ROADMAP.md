# DTR Optimization Lab Roadmap

## Phase 0 — Repository and data foundation

Status: **in progress**

- [x] Initialize repository and Python package.
- [x] Exclude raw datasets and generated artifacts from Git history.
- [x] Register the uploaded NQ dataset with checksum and schema.
- [x] Add loader, audit, resampling, tests, and CI.
- [ ] Resolve source timestamp semantics.
- [ ] Determine continuous-contract, rollover, and adjustment methodology.
- [ ] Reconstruct and verify RTH/ETH session boundaries and VWAP resets.
- [ ] Produce a canonical five-minute Parquet dataset with provenance metadata.

## Phase 1 — TradingView parity baseline

- [ ] Freeze the Pine strategy version and input set used as the reference baseline.
- [ ] Export a TradingView trade list and performance summary for a controlled NQ period.
- [ ] Define matching market specification, commissions, slippage, and fill conventions.
- [ ] Implement DTR session ranges and state transitions.
- [ ] Implement sweep/watch creation and invalidation.
- [ ] Implement MSS/BOS, IFVG/CISD, entry, stop, target, partial, breakeven, and time close.
- [ ] Compare event timestamps and trade outcomes at trade level.
- [ ] Document accepted parity tolerances and unresolved differences.

## Phase 2 — Funnel instrumentation

- [ ] Count every setup stage from range creation through closed trade.
- [ ] Record one primary and all secondary blocker reasons.
- [ ] Attribute opportunities and results by session, direction, weekday, and regime.
- [ ] Export setup-level and trade-level Parquet/CSV logs.

## Phase 3 — Controlled experiment packs

Order of execution:

1. BOS/MSS definitions.
2. Sweep qualification.
3. Entry refinement and signal ageing.
4. Trend versus non-trend routing.
5. Session and weekday attribution.
6. Exit and holding-period logic.
7. Context filters and scoring.

Each pack must compare against the frozen baseline and report coverage, expectancy, drawdown, and robustness.

## Phase 4 — Robustness and walk-forward validation

- [ ] Chronological development, validation, and holdout folds.
- [ ] Rolling walk-forward tests.
- [ ] Transaction-cost and slippage stress.
- [ ] Parameter-neighbourhood stability.
- [ ] Bootstrap/Monte Carlo trade-sequence analysis.
- [ ] Cross-market validation on additional futures and FX datasets.

## Phase 5 — Pine candidate release

- [ ] Select no more than three robust candidates.
- [ ] Port candidate settings/logic to a clean Pine strategy branch.
- [ ] Validate with TradingView Strategy Tester and Bar Magnifier.
- [ ] Reconcile remaining Pine/Python differences.
- [ ] Release a production candidate with full changelog and known limitations.
