# Changelog — Stacey Burke FX Research

## v0.3.0-gate-b-rejection — 2026-07-25

### Changed

- Completed the frozen 2015–2021 matched-control event study across all ten pairs.
- Reproduced all 2,423 census events before exposing forward outcomes.
- Matched 2,393 observable events to 11,965 controls from five distinct dates per event.
- Added exact 60-minute reversal-signed midpoint outcomes normalized by ATR20.
- Added deterministic matching by pair, year, weekday and 15-minute London bucket using pre-event return and realized volatility.
- Added 10,000-iteration calendar-date block bootstrap and date-clustered matched-set permutation inference.
- Added pair and factor-block breadth gates.
- Independently reconstructed the complete Gate B artifact and every decision statistic.
- Archived source, census and controlled-study workflows as manual reproduction tools.

### Reason

The source and census gates established that the event was common enough to test. Gate B was required to determine whether the event delivered a broad, positive reversal effect beyond comparable non-event minutes.

### Result

- 2,393 matched events;
- mean event effect `-0.001709 ATR20` versus matched controls;
- 95% date-block interval `[-0.010309, +0.006900]`;
- clustered permutation p-value `0.670733`;
- four of ten pairs positive;
- one of four factor blocks positive;
- one of six scientific gates passed.

Decision: `FAIL_GATE_B_STOP_STACEY_BURKE_REVERSAL_PROGRAMME`.

### Known limitations

- The result addresses the exact frozen previous-day sweep-and-reclaim mechanism and 60-minute endpoint; it is not a universal test of every concept associated with Stacey Burke.
- Dukascopy is an OTC FX quote source rather than a centralized exchange tape.
- Thirty census events lacked a complete observable/matched endpoint under the exact requirements.
- 2022–2025 outcomes remain deliberately uninspected because discovery failed.

### Next

- Preserve the rejection and compact evidence for audit.
- Do not tune, validate, construct SB-1, or inspect holdouts.
- Consider a future Burke-related programme only if it starts from a genuinely independent mechanism and new preregistration.

## v0.2.0-census-and-study-contract — 2026-07-25

### Added

- Preregistered a causal previous-day high/low sweep-and-reclaim event.
- Added DST-safe New York FX-day and London-window handling.
- Added event, session and exclusion ledgers without forward outcomes.
- Added a pooled census gate for sample size, breadth and concentration.
- Completed the census with 2,423 retained events.
- Froze the controlled-study endpoint, matching contract, inference and Gate B before outcome inspection.

### Reason

A frequent descriptive pattern is not sufficient evidence of a tradable mechanism. The programme required a high-powered, controlled comparison before any strategy construction.

### Known limitations

- Census frequency does not imply directional edge.
- Same-day cross-pair dependence requires calendar-date clustering.

### Next

Execute the single frozen controlled study without parameter search.

## v0.1.1-incremental-source-retention — 2026-07-24

### Changed

- Preserved every successfully acquired pair before enforcing qualification.
- Uploaded qualification evidence even on failed gates.
- Added cache-backed retry and aggregate gating semantics.
- Corrected JSON date serialization and added regression coverage.

### Reason

A late pair or evidence-output failure must not discard already acquired multi-year source data.

### Known limitations

- Private source artifacts remain subject to GitHub retention periods.

### Next

Qualify all ten caches and authorize the event census only after aggregate source success.

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