# Changelog — Stoic Edge 1-2-3

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
- Historical performance has not yet been run in this work package because raw data is not stored in Git.

### Next

- Execute the frozen phase-one family on the qualified NQ and `ES_PROXY` files.
- Review causal examples and funnel attrition without changing the rules.
- Run cost, chronology, nearby-definition, and simple-control tests.
- Decide whether the research remains fruitful before adding complexity.
