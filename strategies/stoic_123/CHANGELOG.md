# Changelog — Stoic Edge 1-2-3

## v0.5.0-research-closed — 2026-07-24

### Added

- Preregistered and executed `STOIC123-WP-20260724-04` as a fresh-history RTH long falsification.
- Source-only qualification of Dukascopy USATECH 2010-2014 before performance execution.
- Frozen 2012-2013 fresh history and untouched 2014 holdout after source coverage showed no usable 2010 and only a one-week 2011 fragment.
- UTC-to-`America/New_York` daylight-saving-aware RTH entry classification.
- Fixed `09:30` inclusive through `16:00` exclusive entry window, with full-session management retained.
- RTH EMA-break primary, full 1-2-3 secondary, retest diagnostic, full-session and overnight comparators.
- Two-tick cost, one-minute and five-minute delay, annual, exposure, exit-reason, uncertainty and fifty-replicate matched-time controls.
- Dedicated RTH session and gate tests with full Python 3.11/3.12 CI coverage.
- Compact result package and independent reconstruction of 22 ledgers, 12 session files and 17 gates.

### Source result

- 2010: unavailable.
- 2011: insufficient 1,515-row fragment.
- 2012: 92,177 active rows beginning January 19.
- 2013: 194,528 active rows.
- 2014: 316,579 active rows reserved as holdout.
- Every executed source matched its frozen SHA-256 and had zero duplicate timestamps.

### Performance result

- RTH EMA break, 2012-2013: 858 trades, `-30.35R`, `-0.035R` expectancy, 106.95R drawdown.
- RTH EMA break, 2014 holdout: 522 trades, `-104.84R`, `-0.201R` expectancy, with a wholly negative date-block interval.
- Full RTH 1-2-3, 2012-2013: 76 trades, `-13.31R`, `-0.175R` expectancy.
- Full RTH 1-2-3, 2014 holdout: 49 trades, `-11.24R`, `-0.229R` expectancy.
- The full sequence underperformed EMA break by `0.140R` expectancy on fresh history and `0.029R` on holdout.
- EMA-break-plus-retest was negative in both partitions.
- Both matched-time candidate comparisons failed.
- Only two of seventeen gates passed, both sample-size gates.

### Decision

`REJECT_RTH_LONG_PROXY_HYPOTHESIS_NO_ACTUAL_NQ_VALIDATION`

The earlier positive RTH attribution did not transfer to fresh proxy history. RTH filtering reduced some full-sequence losses but did not produce positive expectancy. Additional actual-NQ validation is not justified for this formulation.

### Known limitations

- The validation source is a Dukascopy bid-CFD proxy, not CME NQ futures.
- 2012 is partial and starts on January 19.
- Fresh history contains only two calendar years before the one-year holdout.
- Matched-time controls are causal benchmarks, not complete factor models.

### Next

- Close the RTH long hypothesis without further session or parameter subdivision.
- Do not acquire paid actual-NQ data for this formulation.
- Start future research only from a genuinely different preregistered mechanism.
- Keep Pine, sizing, alerts, paper deployment and live use blocked.

## v0.4.0-research-closed — 2026-07-23

### Added

- Preregistered and executed `STOIC123-WP-20260723-03` as an unseen short-side falsification.
- Deterministic Dukascopy USATECH annual/YTD source acquisition and audit workflow.
- Exact source checksums for 2015-2021 and 2026 YTD, frozen before performance execution.
- Checksum-gated partition loader with explicit sample-overlap rejection.
- Mirrored causal short EMA-break and EMA-break-plus-retest controls.
- New-York-session-aware deterministic matched-time short controls.
- Twelve all-required gates covering sample size, expectancy, uncertainty, year breadth, concentration, costs, delay, mechanism value, and matched controls.
- Dedicated short-validation tests and full Python 3.11/3.12 CI coverage.
- Compact result package and independent reconstruction of 16 ledgers and 12 gates.

### Corrected

- Converted UTC source timestamps to New York time for RTH/overnight and half-hour matched-control attribution.
- Enlarged only synthetic test fixtures when the frozen matching contract correctly produced no alternative candidates; matching rules were not loosened.
- Kept raw market data outside Git and removed it before artifact upload.

### Result

- Older 2015-2021 short-only: 696 trades, `-86.13R`, `-0.124R` expectancy, 2/7 positive years.
- Older two-tick cost stress: `-142.73R`.
- Older one-minute delay: `-102.16R`.
- 2026 YTD short-only: 43 trades, `+2.12R`, `+0.049R` expectancy, but a very wide interval.
- Full sequence added only `+0.001R` expectancy over EMA break on older history and underperformed by `-0.031R` in 2026 YTD.
- Both matched-control tests failed.
- Four of twelve promotion gates passed.

### Decision

`REJECT_CURRENT_SHORT_SIDE_HYPOTHESIS_NO_PAID_NQ_VALIDATION`

The post-hoc actual-NQ short strength did not reproduce on the long unseen proxy history. The small fresh result is uncertain and weaker than a simpler control. The current mechanical Stoic family is closed without a finalist.

### Known limitations

- The unseen data are Dukascopy bid-CFD proxy quotes, not CME NQ futures.
- Proxy volume is not centralized futures volume.
- The 2026 partition is partial and contains only 43 full-sequence short trades.
- Matched-time controls are causal benchmarks, not complete factor models.

### Next

- Do not purchase actual-NQ data for this exact mechanical formulation.
- Do not perform direction, session, filter, stop, target, delay, timeframe, or exit retuning.
- Start a future project only for a genuinely different preregistered mechanism.
- Keep Pine, sizing, alerts, paper deployment, and live use blocked.

## v0.3.0-research-complete — 2026-07-23

### Added

- Preregistered and executed `STOIC123-WP-20260723-02` on the checksum-qualified NQ futures archive.
- Both-direction, long-only, short-only, EMA-break-only, EMA-break-plus-retest, cost-stress, and delayed-entry scenarios.
- Fifty deterministic matched-time controls per candidate with frozen event-coverage and holding-period comparability gates.
- Cached validation simulator and matched-pool engine with exact parity tests against the reference execution engine.
- Exact source/config preflight, raw-data removal, compact result publication, and independent reconstruction.

### Corrected

- Separated entry-direction restrictions from the two-direction management detector.
- Superseded the flawed informal long-only artifacts.
- Preserved the 90% matched-control coverage rule without broadening it after returns were inspected.

### Result

- No-map long-only: 555 trades, +75.71R, +0.136R expectancy; 4/9 gates.
- EMA-map long-only: 252 trades, -1.83R, -0.007R expectancy; 2/9 gates.
- Strict-close long-only: 226 trades, +10.97R, +0.049R expectancy; 4/9 gates.
- EMA-plus-breakout long-only: 147 trades, +41.56R, +0.283R expectancy; 5/9 gates.
- Every 95% date-block interval crossed zero and no arm passed all gates.

### Decision

`NO_PROMOTION_STOP_NQ_LONG_ONLY_CURRENT_SAMPLE`

## v0.2.0-research — 2026-07-23

- Added checksum-gated `NQ_PROXY`, `ES_PROXY`, and GBPUSD execution support.
- Corrected GBPUSD BI5 field ordering and used midpoint signals with side-correct bid/ask execution.
- Preserved frozen `phase1.yaml` SHA-256 `5d6909bd5740e1cdea9bd3d47a9818289a6faa8b9a61338726afdc53289ff805`.
- Rejected all six GBPUSD arms.

## v0.1.0-research — 2026-07-23

- Added the separate `stoic_123_lab` package, causal 1-2-3 detector, execution model, governance tree, frozen six-arm family, reporting, inference, and independent review.
