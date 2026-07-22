# Changelog

## Unreleased — 2026-07-22 E6 advanced test framework

### Added

- Formal baseline hierarchy separating the 495-trade engine regression benchmark, 477-trade non-selectable control and 304-trade E6 working research baseline.
- Frozen E6 mechanism audit, path-quality family P1–P3, reward-space family R1–R2, sequencing family S1–S3 and single shadow interaction I1.
- Official-event, holiday, rollover and fixed-fraction equity-risk diagnostic blocks.
- Machine-readable preregistration with fixed metrics, cost scenarios, sample gates, multiplicity controls, stopping rules and execution order.
- Work package, claim, handover, roadmap, status and research-decision-ledger entries.

### Decision

- Record `FRAMEWORK_FROZEN_EXECUTION_NOT_STARTED`.
- Use E6 as the working baseline for bounded historical research while preserving the unfiltered comparator in every report.
- Allow historical evidence to nominate fresh-OOS challengers only; no Pine or deployment promotion.

### Known limits

- Fresh post-2025 NQ data is unavailable.
- Timestamp and continuous-contract methodology remain unresolved.
- The framework definitions are frozen, but no advanced-test result has yet been generated.

## Unreleased — 2026-07-22 advanced context research

### Added

- Timing-corrected exploratory baseline `DTR_CAUSAL_BAR_CLOSE_RANGE_SHIFT_MINUS1` at 477 trades, 42.577515R net, 0.089261R expectancy, and 16.426493R maximum drawdown.
- Causal D1, H4 and weekly context features for direction, volatility, trend strength, range quality, location, gap, volume and VWAP research.
- Twelve univariate families, six frozen broad exclusions and six capped two-factor interactions.
- Familywise edge tests, paired per-session incremental tests, cost stress, period stability and concentration diagnostics.
- Fixed threshold-sensitivity surface that cannot select a replacement threshold.
- Independent reconstruction, causality audit, paired date-block bootstrap and deterministic repeat evidence.
- Supplementary fresh-OOS preregistration for unfiltered Arm 0, compressed-range Arm A, prior-day-proximity Arm B and shadow combined Arm C.

### Research result

- No context filter passed the complete historical promotion gate.
- Excluding compressed ranges retained 335 trades, produced 49.464423R at 0.147655R expectancy, and reduced drawdown to 9.470457R.
- Excluding setups within 0.25 D1 ATR of the prior-day directional extreme retained 304 trades, produced 48.937550R at 0.160979R expectancy, and reduced drawdown to 8.632571R.
- The combined frozen interaction produced 56.774134R at 0.258064R expectancy and 8.554419R drawdown, but retained only 220 trades.
- Paired incremental bootstrap intervals include zero for every broad rule and interaction.

### Decision

- Record `NO_HISTORICAL_PROMOTION_CONTINUE_FRESH_OOS_RESEARCH`.
- Retain Arm A and Arm B as independent fresh-OOS challengers.
- Keep the combined Arm C shadow-only.
- Do not implement context filters in Pine or increase risk based on historical drawdown improvements.

### Known limits

- The 42.58R baseline was selected after historical timing sensitivity.
- Authoritative timestamp and continuous-contract metadata remain unresolved.
- No qualified untouched 2026 result or Python/Pine parity evidence exists.

## v0.4.0 — 2026-07-22

### Corrected

- Replaced retrospective post-entry gap rejection with causal first-observable conservative liquidation.
- Added gap-through-stop execution, resume-time portfolio sequencing, and explicit gap metadata.
- Refroze the active NQ reversal benchmark at 495 trades, 0.173747R expectancy, 86.004761R net, PF 1.366383, and 14.107858R maximum drawdown.
- Separated raw BOS detections from impulse-qualified BOS in the funnel and removed misleading dead invalidation wording.
- Replaced the quadratic session-window scan with an exact searchsorted-equivalent builder.

### Added

- Timestamp/VWAP hypothesis tests, rollover sensitivity, roll discontinuity diagnostics, session×weekday attribution, and leave-one-group-out concentration tests.
- Fixed-seed trade, month-block, and session-date bootstrap code plus selection-pressure primitives.
- Deterministic baseline validity runner and compact evidence package.
- No-retune causal reruns for continuation, IFVG, CISD, and entry routing.
- Fresh 2026 NQ out-of-sample preregistration.

### Validated

- Historical observe-only 504-trade and retrospective 491-trade references remain reproducible.
- Corrected benchmark clean repeat is exact; baseline validity artifacts are 15/15 byte-identical.
- IFVG 52/52, CISD 52/52, continuation structural 30/30, continuation late-60 30/30, and entry routing 33/33 artifacts are byte-identical.
- Local suite: 75 tests passed before final GitHub CI.

### Decisions

- Baseline: `CONTINUE_RESEARCH_DO_NOT_DEPLOY`.
- Continuation: `HOLD_FOR_FRESH_DATA`.
- IFVG: `REJECT_NO_INCREMENTAL_VALUE`.
- CISD: `REJECT_NO_INCREMENTAL_VALUE`.
- Entry routing: `REJECT_NO_INCREMENTAL_VALUE`, pending PR #5 rebase/publication.

### Known limits

- Bar-open versus bar-close semantics remain unresolved.
- Continuous-contract roll/adjustment methodology remains unresolved.
- The 904-configuration selection process lacks an aligned return matrix for familywise correction.
- No qualified pristine 2026 OOS test or Python/Pine parity run has been completed.

## v0.3.2 — 2026-07-22

### Added

- Causal bullish and bearish CISD sequence detector.
- Explicit sequence-anchor and final-candle-anchor confirmation contracts.
- Stale-state expiry when newer opposite delivery begins, including previously confirmed state.
- Reset-epoch isolation, sequence timing, displacement, anchor-distance, and retest diagnostics.
- Strict CISD manifest schema, checksum verification, canonical runner, fixtures, and compact evidence.
- Cohort-versus-implementable portfolio attribution, cost stress, bootstrap, permutation, and timing-decomposition analysis.

### Validated

- Frozen 491-trade gap-safe reversal baseline reproduced exactly.
- Two clean canonical runs produced 52 of 52 byte-identical artifacts.
- Broad sequence and last-candle confirmation each reduced expectancy to 0.144100R.
- Recent-three and recent-six variants were weaker than baseline.
- The retest portfolio remained positive under cost stress but retained only 75 trades and had lower return-to-drawdown.
- Incremental retest uplift confidence intervals crossed zero; one-sided permutation p-value was 0.210289.
- Every removed and newly enabled portfolio trade was attributed.

### Decision

- Record `REJECT_NO_INCREMENTAL_VALUE`.
- Retain CISD and the retest flag for diagnostics only.
- Do not add a CISD filter or sizing rule, combine it with IFVG or continuation, tune it further on the current sample, or port it to Pine as strategy logic.
- Advance to reversal entry-routing ablation.

### Known limitations

- Timestamp, daylight-saving, session-boundary, rollover, and supplied VWAP semantics remain provisional.
- No pristine post-December-2025 NQ sample exists.
- The rejection applies to the explicit causal contracts tested, not every discretionary interpretation of CISD.

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
