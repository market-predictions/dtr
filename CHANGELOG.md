# Changelog

## v0.3.0 — 2026-07-21

### Added

- Standalone, gap-safe NQ continuation engine.
- First-breakout event state with one-bar and two-bar acceptance.
- Immediate and first-pullback entry routes.
- Return-inside, opposite-boundary, extension, expiry, failed-breakout, and unsafe-gap handling.
- Continuation-specific structural stops, partial target, runner, breakeven, event-end, and maximum-hold exits.
- Diagnostics for displacement, range extension, volume, VWAP, ER, ADX, and time since range completion.
- Strict continuation manifest schema and canonical manifest runner.
- Structural baseline and late-60 stress manifests.
- Deterministic CSV, Parquet, JSON, funnel, and attribution artifacts.
- Structural fixtures, manifest tests, full research report, independent review, and handover.

### Research result

- All four unfiltered continuation variants are negative overall.
- Two-bar pullback is materially better than immediate entry but remains negative without a timing condition.
- `CONT_A2_PULLBACK_LATE60` produced 147 trades, 0.108895R expectancy, 16.007565R net, PF 1.242960, and 8.003633R maximum drawdown.
- The 60–70 minute timing region is a positive parameter plateau across development, validation, and later research.
- All 12 predeclared risk/exit variants on the late-60 population remained positive across the three main periods.
- Four-tick slippage turns the aggregate result negative.
- Trade and month-block bootstrap intervals include zero.
- Expanding threshold selection was negative in 2025H1 and had only nine trades in the final fold.

### Decision

- Complete the continuation-engine work package.
- Record `HOLD_FOR_FRESH_DATA`.
- Retain the late two-bar pullback as a research lead only.
- Do not combine continuation with reversal and do not tune it further on the current NQ sample.
- Advance the roadmap to IFVG entry-confirmation ablation.

### Known limitations

- The continuation lead was discovered through diagnostic screening on a finite research dataset.
- No pristine post-December-2025 sample exists.
- Cost sensitivity is material.
- Continuous-contract rollover, timestamp, daylight-saving, session, and VWAP semantics remain provisional.
- The existing commission convention charges one round trip even when the position exits in multiple legs.

### Next

- Open `DTR-NQ-WP-20260721-03` for IFVG entry-confirmation ablation.
- Test IFVG first against the frozen gap-safe reversal baseline.
- Preserve removal attribution and opportunity coverage before any composite use.

## v0.2.3 — 2026-07-21

### Added

- Full-dataset reference-versus-gap-safe comparison report.
- Compact machine-readable comparison summary with locked artifact hashes.
- Trade-level attribution for all 13 removed observations.
- Expected baseline for `DTR_PY_NQ_CANDIDATE_0_1_GAP_SAFE`.
- Final independent review and completed work-package handover.

### Validated

- Frozen reference reproduced exactly: 504 trades, 84.164359R net, 14.107858R maximum drawdown.
- Gap-safe baseline: 491 trades, 88.495783R net, 14.107858R maximum drawdown.
- Nine trades were removed for contaminated session ranges.
- Four trades were removed for unsafe gaps during open positions.
- No trades were added and no unexplained differences remained.
- All required artifacts were byte-identical across clean reruns.

### Decision

- Close the baseline-integrity gate.
- Promote the project to an independent continuation-engine work package.
- Treat the 4.331424R sanitized improvement as a data-integrity consequence, not an optimization gain.

### Known limitations

- Continuous-contract rollover and adjustment methodology remain unresolved.
- Timestamp, daylight-saving, session-boundary, and VWAP-reset semantics remain provisional.
- No post-December-2025 paper-forward sample is available.
- The gap-safe policy excludes missing-data execution rather than estimating hypothetical fills.

### Next

- Develop the continuation engine independently under `DTR-NQ-WP-20260721-02`.
- Test accepted breakouts, immediate versus first-pullback entries, failed-breakout invalidation, and continuation-specific risk logic.
- Require independently positive walk-forward evidence before any combination with reversal.

## v0.2.2 — 2026-07-21

### Added

- Deterministic gap-state and unsafe-gap epochs on derived five-minute bars.
- Session-range rejection when source-data reset boundaries contaminate the defining range.
- Signal-path truncation at the first reset boundary after a session range.
- Open-trade rejection when a simulated position bridges an unsafe market-data gap.
- Integrity funnel counters for range rejections, path truncations, rejected trade bridges, and observed bridges.
- Explicit manifest `gap_policy` values: `observe_only` and `reject_unsafe`.
- A gap-safe manifest for `DTR_PY_NQ_CANDIDATE_0_1_GAP_SAFE` using exactly the same strategy parameters as the frozen candidate.
- Focused tests for intra-bucket missing bars, session contamination, setup resets, trade bridges, clean-data preservation, and policy separation.
- Work-package, claim, status, independent-review, and handover artifacts for the baseline-integrity closure.

### Changed

- `DTR_PY_NQ_CANDIDATE_0_1` is explicitly preserved as the `observe_only` reference run so its 504-trade regression remains reproducible.
- Optimization and ordinary research runs default to `reject_unsafe`; legacy manifests without a policy default to `observe_only` for backward compatibility.
- Standard package and direct engine entry points route through the integrity-safe execution layer.
- The NQ dataset remains the sole optimization base; Dukascopy and other providers are deferred to a future work package.
- The package version is now `0.2.2`.

### Why

The gap audit identified missing and offset intervals, but the strategy engine could still form setups or simulate trades across those boundaries. Optimizing before closing that contract could reward structures that were partly created by absent data. The split-policy design preserves historical reproducibility while producing a separate sanitized result without retuning parameters.

### Independent review finding

The initial implementation routed the frozen manifest directly through the new rejection policy. That would have intentionally changed the trade set while causing the historic 504-trade regression to fail, without preserving a machine-runnable reference. The review required two explicit manifests and separate observe-only versus reject-unsafe semantics before promotion.

### Known limitations

- The raw NQ dataset is excluded from Git, so the full reference and gap-safe reruns must execute where the checksum-matched local archive is available.
- Gap-safe aggregate metrics and changed-trade attribution are not yet locked.
- Continuous-contract rollover, back-adjustment, timestamp meaning, daylight-saving boundaries, and supplied VWAP semantics remain unresolved.
- A rejected trade bridge is excluded from primary results rather than assigned a hypothetical fill through missing data.
- Continuation, IFVG/CISD, H1Vol, Weekly VWAP, higher-timeframe scoring, and footprint are not yet included.

### Next

- Run `configs/manifests/nq_candidate_0_1.yaml` and confirm the frozen regression.
- Run `configs/manifests/nq_candidate_0_1_gap_safe.yaml` and generate the complete comparison report.
- Lock gap-safe artifact hashes, funnel deltas, and regression tolerances.
- Begin the independent continuation engine only after the comparison is reviewed.

## v0.2.1 — 2026-07-21

### Added

- Strict Pydantic research-manifest schema.
- Dataset SHA-256 verification before a research run.
- Frozen candidate manifest for `DTR_PY_NQ_CANDIDATE_0_1`.
- Deterministic manifest runner.
- Generated CSV, Parquet, JSON, funnel, half-year, session, weekday, and direction artifacts.
- Code, manifest, and dataset provenance in each run summary.
- Frozen-baseline regression checks for trade count, net R, and maximum drawdown.
- Manifest and checksum integrity tests.

### Changed

- TradingView is formally parked as the primary research environment.
- The roadmap now prioritizes Python reproducibility, data integrity, continuation research, context ablation, adaptive routing, and later Pine implementation.
- Repository documentation now describes manifest-driven research runs.

### Why

The first optimized reversal result must be reproducible from one versioned command before additional modules or parameter searches are trusted. This release turns the candidate from a documented result into a machine-checkable research specification.

### Known limitations

- The full candidate rerun still requires the local Kaggle dataset because raw market data is excluded from Git.
- Continuous-contract rollover and back-adjustment semantics remain unresolved.
- Timestamp semantics remain provisional.
- Continuation, IFVG/CISD, H1Vol, Weekly VWAP, higher-timeframe scoring, and footprint are not yet included.

### Next

- Execute and lock the manifest-driven candidate rerun.
- Classify data gaps and probable rollover discontinuities.
- Add safeguards around unexplained gaps.
- Begin the independent continuation engine after the reproducibility gate passes.

## v0.2.0 — 2026-07-21

### Added

- Python reversal research and execution engine.
- Session ranges, sweeps, reclaims, protected pivots, BOS/MSS, acceptance, and entries.
- Regime, session, weekday, risk, stop, target, and time-close variants.
- Staged optimization packs for BOS, sweep, regime, timing, risk, and exits.
- First 904-configuration NQ research run.
- Half-year, session, weekday, direction, cost-stress, walk-forward, and Monte Carlo results.
- Initial research candidate `DTR_PY_NQ_CANDIDATE_0_1`.

### Why

The known DTR concept can be tested more thoroughly in Python than through repeated manual TradingView configuration changes.

### Known limitations

- The engine is a research interpretation rather than an exact Pine clone.
- No pristine post-research holdout or paper-forward data is available yet.

### Next

- Make the research result reproducible through a strict manifest and regression gate.

## v0.1.0 — 2026-07-21

### Added

- Initial DTR Optimization Lab repository structure.
- Python packaging and dependency configuration.
- Data-safe `.gitignore` that excludes raw market data and generated artifacts.
- NQ one-minute dataset catalog with checksum, schema, date range, and audit findings.
- CSV/ZIP loader with strict schema validation.
- OHLCV resampling utility for one-minute to five-minute research bars.
- Deterministic dataset audit model and command-line interface.
- Unit tests for audit and resampling semantics.
- GitHub Actions CI for Python 3.11 and 3.12.

### Why

The DTR strategy requires systematic funnel diagnostics and controlled optimization outside TradingView. The first release established reproducible data handling before strategy research.

### Known limitations

- Contract rollover and back-adjustment semantics were unresolved.
- Source timestamps were timezone-naive pending bar-open/bar-close verification.
- The uploaded dataset appeared capped at the Excel worksheet row limit and ended mid-session.
- No DTR strategy logic had been ported yet.

### Next

- Complete the NQ dataset integrity and contract-continuity audit.
- Implement session-range and sweep primitives.
- Build the baseline setup funnel before testing parameter alternatives.
