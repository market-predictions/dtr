# Research Registry Changelog

## v1.1.0 — 2026-08-08

### Added

- Prospectively preregistered `DFXC-20260808-001-pivot-multiscale-terminal`.
- Prospectively conditional `DFXC-20260808-002-pivot-wick-rejection`.
- Scale-aligned pivot/leg mapping test: D/H1, W/H4, M/D1, Q/W1, Y/MN1 plus H1 mismatch benchmarks.
- Strict later-bar endpoint-confirmation amendment to prevent wick/termination circularity.
- Compact multiscale and wick result records, final internal report, evidence manifest and implementation-validation record.

### Scientific state

- Daily/H1 and Weekly/H4 terminal-zone mappings pass the frozen internal structural gate.
- Monthly/D1, Quarterly/W1 and Yearly/MN1 fail; higher-timeframe scale alignment does not rescue those pivot horizons.
- Daily/H1 pivot-core wick interaction passes internally at +0.92 pp beyond generic wick exhaustion.
- Weekly/H4 wick interaction remains failed because its uncertainty interval crosses zero / p=0.0744.
- Protected 2022–2025 remains unopened.

### Governance

- Implementation validation is complete.
- Independent `governance_release_assurance` remains pending; no holdout, strategy or deployment authority is created by these internal results.

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

The initial registry candidate was implementation-complete and independently validated before merge to `main`.
