# Research Registry Changelog

## v1.0.0 — 2026-08-08

### Added

- Canonical research name **Dukascopy FX Cash** and machine ID `dukascopy_fx_cash_m1_bid_ask_v1`.
- Durable study/result object model with immutable `DFXC-*` study IDs.
- Machine-readable and human-readable master indexes.
- Branch-resident evidence contract using exact Git commit SHAs.
- Falsification, holdout, assurance, negative-result and prohibited-rescue fields.
- Registry validator, deterministic index renderer and CI-covered tests.
- Retrospective normalized entries for Quarters Theory Stage-1, ten-pair Quarters confirmation, classic-pivot target/stall/reversal falsification and pivot spatial-zone follow-up.
- Historical migration queue for older Dukascopy FX branches.

### Compatibility

- Existing permanent private cache, Drive folder, source checksums and legacy catalog key remain unchanged.
- Strategy-specific implementations remain in their existing locations.
- No raw market data is added to Git.
- No protected holdout is opened.

### Governance

This candidate is implementation-complete but requires independent assurance before merge to `main`.
