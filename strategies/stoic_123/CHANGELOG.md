# Changelog — Stoic Edge 1-2-3

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
- Full GBPUSD, NQ-proxy, and ES-proxy phase-one result and independent reconstruction packages.
- Canonical Drive data and result manifests for NQ proxy, ES proxy, and repaired GBPUSD.

### Changed

- Replaced pandas row-by-row state iteration with an equivalent NumPy-backed state machine.
- Replaced quadratic management-event lookup with sorted timestamp indexes.
- Replaced concatenation-heavy bootstrap arithmetic with block sums and counts.
- Split index-proxy execution into clean instrument-isolated runs to prevent transition-state resource pressure.
- Preserved the frozen `phase1.yaml` byte-for-byte; SHA-256 remains `5d6909bd5740e1cdea9bd3d47a9818289a6faa8b9a61338726afdc53289ff805`.

### Reason

GBPUSD requires true bid/ask execution rather than a futures-style fixed cost approximation. Four years of minute data also required equivalent array-based iteration and indexed lookups. Instrument-isolated runs preserve scientific separation and remove unnecessary peak-memory coupling.

### Result

- GBPUSD: all six arms are `NO_EDGE`; expectancy ranges from -0.451R to -0.788R. Direct transfer is rejected.
- NQ proxy: five arms are positive; the strict-close arm leads at 0.204R expectancy, but its 95% date-block interval crosses zero.
- ES proxy: five arms are positive; EMA-plus-breakout leads at 0.115R and strict close produces 0.104R, but all intervals cross zero.
- Cross-proxy conclusion: strict close is the strongest robustness candidate, not a validated strategy.

### Known limitations

- GBPUSD is one Dukascopy spot-FX quote stream, not a broker-neutral consolidated tape.
- NQ and ES proxy archives are bid-only CFDs, not CME futures.
- Provider volume is not centralized futures volume.
- All positive proxy candidates remain statistically uncertain under date-block resampling.

### Next

- Execute preregistered nearby-definition, timeframe, chronology, and cost robustness tests.
- Compare proxy findings against the qualified NQ futures archive when mounted.
- Test mechanism value against simpler EMA-break and matched-entry controls.
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
