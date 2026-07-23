# Changelog — Stoic Edge 1-2-3

## v0.3.0-research-preregistered — 2026-07-23

### Added

- Preregistered `STOIC123-WP-20260723-02` for NQ long-only mechanism and futures replication.
- Dedicated validation design with frozen candidate roles and nine all-required promotion gates.
- Causal EMA-break-only and EMA-break-plus-retest controls.
- Deterministic matched-time controls preserving calendar, session, map eligibility, and risk width.
- Both-direction, long-only, and short-only full-sequence comparators.
- Two-tick cost stress, one-minute and five-minute entry delays, expanding-year folds, RTH/overnight attribution, concentration, and exposure-normalized reporting.
- Dedicated NQ validation workflow with exact source-checksum enforcement and raw-data removal.
- Eight direction, management, attribution, delay, and matched-control regression tests; 26 focused Stoic tests pass locally.

### Corrected

- Identified that the informal long-only counterfactual inherited `allow_short: false` into the management detector, unintentionally removing opposite short exit signals.
- The new contract restricts entry direction only; management remains two-directional.
- Earlier informal long-only results are superseded and cannot be promoted.
- Corrected compact summaries and inference are committed for NQ proxy, ES proxy, and GBPUSD; all 18 corrected ledgers passed independent review.
- The NQ EMA-map and strict-close trade streams were unchanged; only the no-map controls changed.

### Reason

A long-only historical improvement is not decision-useful until actual NQ futures reproduce it, the original technical-exit contract is preserved, and the full sequence beats simpler long-drift and EMA-break controls.

### Known limitations

- The registered NQ archive has unresolved continuous-contract roll and exact timestamp semantics.
- The source starts late in December 2022, so 2022 is only a partial year.
- The matched-time control is a causal benchmark, not a complete market-factor model.
- Each matched replicate must cover at least 90% of full-sequence events, but realized holding periods can still differ.

### Next

- Verify the exact NQ archive checksum.
- Execute the preregistered study without modifying the frozen design.
- Publish independent reconstruction and a pass/fail result for every promotion gate.

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
- The combined proxy phase-one run still requires a clean official execution package after the newly exposed transition-performance issue is resolved.

### Next

- Profile and resolve the proxy multi-source transition bottleneck without changing signal rules.
- Execute clean, separate official NQ-proxy and ES-proxy phase-one packages.
- Compare proxy results against the qualified NQ futures archive when mounted.
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
