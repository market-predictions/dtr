# Changelog — Stoic Edge 1-2-3

## v0.3.0-research-complete — 2026-07-23

### Added

- Preregistered and executed `STOIC123-WP-20260723-02` on the checksum-qualified NQ futures archive.
- Both-direction, long-only, short-only, EMA-break-only, EMA-break-plus-retest, cost-stress, and delayed-entry scenarios.
- Fifty deterministic matched-time controls per candidate with frozen event-coverage and holding-period comparability gates.
- Cached validation simulator and matched-pool engine with exact parity tests against the reference execution engine.
- Exact source/config preflight, retained diagnostic artifacts, raw-data removal, compact result publication, and independent reconstruction.
- Final result report, decision JSON, compact summaries, mechanism evidence, inference, matched-control evidence, and veto output.

### Corrected

- Separated entry-direction restrictions from the two-direction management detector.
- Superseded the flawed informal long-only artifacts.
- Corrected the validation workflow session helper, NQ execution-model discriminator, manifest date serialization, and final matched-control coverage veto.
- Preserved the 90% matched-control coverage rule after one mapped arm exposed insufficient coverage; no matching rule was broadened after returns were inspected.

### Result

- No-map long-only: 555 trades, +75.71R, +0.136R expectancy; 4/9 gates.
- EMA-map long-only: 252 trades, -1.83R, -0.007R expectancy; 2/9 gates.
- Strict-close long-only: 226 trades, +10.97R, +0.049R expectancy; 4/9 gates.
- EMA-plus-breakout long-only: 147 trades, +41.56R, +0.283R expectancy; 5/9 gates.
- Every 95% date-block interval crossed zero.
- No arm passed all numerical gates.
- All four arms were vetoed by the matched-control contract.

### Decision

`NO_PROMOTION_STOP_NQ_LONG_ONLY_CURRENT_SAMPLE`

The actual NQ archive does not confirm the proxy-derived EMA-map long-only thesis. Strict close adds negligible expectancy over a simple EMA break. EMA-plus-breakout is historically interesting but chronologically unstable and statistically uncertain.

### Known limitations

- Continuous-contract roll and exact timestamp semantics remain unresolved.
- December 2022 is only a partial year.
- Matched-time controls are causal benchmarks, not complete factor models.
- The observed no-map short-side strength is post-hoc and cannot be selected on this sample.

### Next

- Stop same-sample long-only research and tuning.
- Retain directional asymmetry only as a fresh-data hypothesis.
- Require qualified unseen or materially longer contract-audited data before any new Stoic selection work.
- Keep Pine, sizing, alerts, paper deployment, and live use blocked.

## v0.2.0-research — 2026-07-23

### Added

- Checksum-gated canonical `NQ_PROXY` and `ES_PROXY` full-grid Dukascopy adapters.
- GBPUSD raw-cache and normalized-cache loaders with annual member checksum verification.
- Explicit repair for the source writer's BI5 `open, close, low, high` field order.
- Midpoint signal bars with side-correct bid/ask execution, stops, gap exits, and technical exits.
- Dynamic runner inputs for `NQ`, `NQ_PROXY`, `ES_PROXY`, and `GBPUSD` without pooled reporting.
- Cached resampling and indexed management exits.
- Array-based detector engine with exact equivalence against the original state machine.
- Four additional regression tests, bringing the dedicated total to fourteen.
- Full GBPUSD 2022-2025 phase-one result and independent reconstruction package.
- Canonical Drive data manifests for NQ proxy, ES proxy, and repaired GBPUSD.

### Changed

- Replaced pandas row-by-row state iteration with an equivalent NumPy-backed state machine.
- Replaced quadratic management-event lookup with sorted timestamp indexes.
- Replaced concatenation-heavy bootstrap arithmetic with block sums and counts.
- Preserved the frozen `phase1.yaml` byte-for-byte; SHA-256 remains `5d6909bd5740e1cdea9bd3d47a9818289a6faa8b9a61338726afdc53289ff805`.

### Reason

GBPUSD requires true bid/ask execution rather than a futures-style fixed cost approximation. The original detector and inference loops also became operationally impractical on four years of minute data. The changes preserve strategy logic while making the study executable and auditable.

### Result

All six GBPUSD arms are `NO_EDGE`. Net expectancy ranges from -0.451R to -0.788R per trade. No parameter tuning or second-stage GBPUSD search is authorized.

### Known limitations

- GBPUSD is one Dukascopy spot-FX quote stream, not a broker-neutral consolidated tape.
- NQ and ES proxy archives are bid-only CFDs, not CME futures.
- Provider volume is not centralized futures volume.

### Next

- Compare proxy results against qualified futures evidence.
- Stop GBPUSD research unless a genuinely different mechanism is preregistered.

## v0.1.0-research — 2026-07-23

### Added

- Separate `stoic_123_lab` package and strategy-governance tree.
- Frozen six-arm phase-one configuration.
- Checksum-gated NQ and Dukascopy USA500/`ES_PROXY` adapters.
- Causal 10/20 EMA Step-1 break detector using closes rather than wicks.
- Retest detection followed by a post-retest compact-base builder.
- Immutable base-boundary lock before Step 3.
- Close-confirmed Step 3 with next-open baseline fill.
- Declared 60-minute map, 5-minute execution, and 15-minute management timeframes.
- Protective stop, minimum-risk gate, gap liquidation, maximum hold, and opposite-sequence exit.
- Cost-aware R-multiple trade ledger.
- Summary, date-block bootstrap, classification, and no-pooling gates.
- Independent trade-ledger reconstruction.
- Ten synthetic regression and causality tests.

### Reason

The source article is strategically coherent but leaves its edge-bearing terms discretionary. This version converts those terms into explicit, auditable hypotheses without modifying the existing DTR strategy or using hindsight boundaries.

### Known limitations

- The first candidate family is a mechanical interpretation, not a claim that it exactly reproduces the author's visual discretion.
- The USA500 source is a bid-CFD proxy without CME volume, contract rolls, or historical ask prices.
- The technical exit may hold positions for long periods; a maximum-hold fail-safe is therefore separate and explicit.
- No partial-profit or climactic-extension model is included in phase one.

### Next

- Execute the frozen phase-one family on qualified sources.
- Review causal examples and funnel attrition without changing the rules.
- Run cost, chronology, nearby-definition, and simple-control tests only after a viable baseline appears.
