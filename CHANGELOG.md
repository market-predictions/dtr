# Changelog

## v0.3.1 — 2026-07-21

### Added

- Causal bullish and bearish three-candle FVG recognition.
- Later-close IFVG inversion without lookahead.
- Reset-epoch isolation so pre-gap FVG and IFVG state cannot cross unsafe data intervals.
- IFVG signal annotations, cohort analysis, implementable portfolio filtering, and changed-trade attribution.
- Strict IFVG manifest schema and canonical manifest runner.
- Predeclared `observe`, `confirm_any`, recent-three, recent-six, recent-twelve, and zone-touch variants.
- Cost-stress, age-neighbourhood, chronological, coverage, and portfolio-sequencing evidence.
- IFVG structural fixtures, manifest tests, full research report, independent review, compact evidence, and handover.

### Validated

- Frozen 491-trade gap-safe reversal baseline reproduced exactly.
- Two clean canonical runs produced 52 byte-identical artifacts.
- Pinned Ruff passed.
- Pytest passed on Python 3.11 and 3.12.
- Every removed and newly enabled portfolio trade was attributed; no unexplained differences remained.

### Research result

- Frozen baseline: 491 trades, 0.180236R expectancy, 88.495783R net, PF 1.381998, 14.107858R maximum drawdown.
- Any aligned IFVG: 455 trades and 0.168419R expectancy.
- Recent-three: 318 trades and 0.168385R expectancy.
- Recent-six: 367 trades and 0.157503R expectancy.
- Recent-twelve: 432 trades and 0.160347R expectancy.
- Zone touch: 212 trades and 0.153369R expectancy.
- One-, two-, and four-tick slippage preserved the same negative ranking.
- Strict filters enabled a small number of later trades; those added trades were net negative.

### Decision

- Record `REJECT_NO_INCREMENTAL_VALUE`.
- Retain the causal IFVG detector for diagnostics and reproducibility only.
- Do not add IFVG confirmation to the reversal candidate.
- Do not tune IFVG further or combine it with the held continuation lead on the current NQ sample.
- Advance to an independently scoped CISD entry-confirmation ablation.

### Known limitations

- Timestamp, daylight-saving, session-boundary, continuous-contract rollover, and supplied VWAP semantics remain provisional.
- No pristine post-December-2025 NQ sample exists.
- The rejection applies to the stated causal IFVG definition and frozen reversal architecture; it is not a universal claim about every discretionary IFVG interpretation.

## v0.3.0 — 2026-07-21

### Added

- Standalone, gap-safe NQ continuation engine.
- First-breakout event state with one-bar and two-bar acceptance.
- Immediate and first-pullback entry routes.
- Explicit return-inside, opposite-boundary, extension, expiry, failed-breakout, and unsafe-gap handling.
- Continuation-specific structural stops, partial target, runner, breakeven, event-end, and maximum-hold exits.
- Diagnostics for displacement, range extension, volume, VWAP, ER, ADX, and time since range completion.
- Strict continuation manifests, deterministic artifacts, fixtures, report, review, and handover.

### Research result

- All four unfiltered continuation variants were negative overall.
- Two-bar pullback was materially better than immediate entry but remained negative without timing selection.
- `CONT_A2_PULLBACK_LATE60` produced 147 trades, 0.108895R expectancy, 16.007565R net, PF 1.242960, and 8.003633R maximum drawdown.
- The 60–70 minute timing region formed a positive plateau, but four-tick slippage turned aggregate performance negative and bootstrap intervals included zero.

### Decision

- Record `HOLD_FOR_FRESH_DATA`.
- Retain the late two-bar pullback as a research lead only.
- Do not combine continuation with reversal and do not tune it further on the current sample.

## v0.2.3 — 2026-07-21

### Added and validated

- Full-dataset reference-versus-gap-safe comparison report.
- Compact machine-readable comparison summary with locked artifact hashes.
- Trade-level attribution for all 13 removed observations.
- Expected baseline for `DTR_PY_NQ_CANDIDATE_0_1_GAP_SAFE`.
- Frozen reference reproduced exactly: 504 trades, 84.164359R net, 14.107858R maximum drawdown.
- Gap-safe baseline: 491 trades, 88.495783R net, 14.107858R maximum drawdown.
- Nine trades were removed for contaminated session ranges and four for unsafe gaps during open positions.
- No trades were added and no unexplained differences remained.
- All required artifacts were byte-identical across clean reruns.

### Decision

- Close the baseline-integrity gate.
- Treat the 4.331424R sanitized improvement as a data-integrity consequence, not an optimization gain.
- Promote the project to independent continuation research.

## v0.2.2 — 2026-07-21

### Added

- Deterministic gap-state and unsafe-gap epochs on five-minute bars.
- Session-range rejection for contaminated source ranges.
- Setup-path truncation at reset boundaries.
- Open-trade rejection across unsafe missing-data intervals.
- Explicit `observe_only` and `reject_unsafe` manifest policies.
- Gap-safe manifest with identical strategy parameters to the frozen reference.
- Focused integrity tests and work-package governance artifacts.

### Changed

- Preserved `DTR_PY_NQ_CANDIDATE_0_1` as the machine-runnable observe-only reference.
- Routed ordinary research through the gap-safe execution layer.
- Deferred Dukascopy and other providers; NQ remains the sole optimization base.

## v0.2.1 — 2026-07-21

### Added

- Strict Pydantic research-manifest schema.
- Dataset SHA-256 verification.
- Frozen candidate manifest and deterministic runner.
- CSV, Parquet, JSON, funnel, half-year, session, weekday, and direction artifacts.
- Provenance and frozen-baseline regression checks.

### Changed

- Parked TradingView as the primary research environment.
- Prioritized Python reproducibility, integrity, independent modules, and later Pine validation.

## v0.2.0 — 2026-07-21

### Added

- Python reversal research and execution engine.
- Session ranges, sweeps, reclaims, protected pivots, BOS/MSS, acceptance, and entries.
- Regime, session, weekday, risk, stop, target, and time-close variants.
- Staged optimization packs and the first 904-configuration NQ research run.
- Initial candidate `DTR_PY_NQ_CANDIDATE_0_1` with chronological, cost, walk-forward, and Monte Carlo evidence.

## v0.1.0 — 2026-07-21

### Added

- Initial DTR Optimization Lab repository and Python package.
- Data-safe `.gitignore` excluding raw market data and generated bulk artifacts.
- NQ one-minute dataset catalog, checksum, schema, loader, audit, resampling, tests, and CI.

### Known limitations

- Continuous-contract rollover and adjustment semantics were unresolved.
- Source timestamps and session/VWAP semantics were provisional.
