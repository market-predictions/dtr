# Changelog — Stacey Burke FX Research

## v0.1.0-source-programme — 2026-07-24

### Added

- Created a separate Stacey Burke multi-asset FX namespace.
- Froze ten liquid FX pairs across four factor blocks.
- Added generic Dukascopy BID/ASK M1 acquisition with canonical BI5 field mapping.
- Preserved zero-volume provider records and explicit active-quote flags.
- Added annual source hashes, bounds, OHLC, synchronization, coverage and spread qualification.
- Added a source-only parallel GitHub Actions matrix.
- Preregistered 2015–2021 discovery, 2022–2023 validation, 2024–2025 holdout and 2026 YTD monitoring.

### Reason

Stacey Burke claims are multi-asset liquidity hypotheses. A single-pair backtest would confound the mechanism with pair-specific behaviour and would provide too few independent event dates.

### Known limitations

- Dukascopy is an OTC FX quote source rather than a centralized exchange tape.
- Cross-pair dependence remains and must be handled with date clustering and factor-block reporting.
- Source artifacts are initially retained privately in GitHub Actions; persistent Drive registration follows qualification.

### Next

Complete source qualification and freeze hashes. Then implement only the conditional previous-day high/low sweep-and-reclaim event census. Do not build SB-1 trade execution unless the pooled event gate passes.
