# Pivot Multiscale Terminal-Zone Study — Preregistration Amendment 01

Date: 2026-08-08
Programme: `PIVOT-MULTISCALE-TERMINAL-ZONE-V1`
Study ID: `DFXC-20260808-001-pivot-multiscale-terminal`
Status: `FROZEN_PRE_OUTCOME_CLARIFICATION`

This amendment resolves implementation details before any new outcome is computed. It does not change the market question, scale mapping, effect definition, gate, pair universe, ATR parameters, spatial regions or protected-holdout boundary.

## Archive and holdout handling

- Each locally restored split source archive must pass every registered part SHA-256 and the reconstructed full-archive SHA-256 before use.
- Only annual BID/ASK members for 2015 through 2021 may be opened for analysis.
- Members dated 2022 or later remain physically present in the archive but their contents are never read in this work package.

## M1 structural midpoint and activity handling

For timestamp-matched BID/ASK M1 rows:

- midpoint open = `(bid_open + ask_open) / 2`;
- midpoint high = `(bid_high + ask_high) / 2`;
- midpoint low = `(bid_low + ask_low) / 2`;
- midpoint close = `(bid_close + ask_close) / 2`.

Before filtering, BID and ASK annual timestamp grids must match exactly. Expected market-closure rows with `is_active_quote=0` are not data gaps. Only minutes with at least one active quote side are used to construct detector OHLC so weekend/holiday carry-forward rows do not depress ATR.

A source-grid mismatch, malformed row or checksum failure aborts that pair rather than being imputed.

## FX trading-date labels

The NY-17 trading date is the calendar date of `(timestamp converted to America/New_York) + 7 hours`.

- D1 groups by this FX trading date.
- W1 groups by the Friday-ending week of the FX trading date.
- MN1 groups by the calendar month of the FX trading date.
- Pair-year bootstrap cluster year is the year of the FX trading date attached to the detector observation.

## Detector-bar pivot-boundary integrity

A detector candle is eligible only when all of its source observations belong to one active pivot period for the tested pivot horizon. Any detector candle that straddles a pivot-period boundary is excluded for that horizon rather than assigned retrospectively to either side.

This is especially relevant for UTC-aligned H4 bars at weekly boundaries and W1 bars at quarter boundaries.

## Exact directional-change initialization and flip logic

After ATR24 becomes available, a neutral detector tracks running high and running low.

- If a bar close falls by at least the current `0.75 * ATR24_lag1` threshold from the running high, that running-high bar is confirmed as the first high endpoint and state becomes down.
- Else if a bar close rises by at least the current threshold from the running low, that running-low bar is confirmed as the first low endpoint and state becomes up.
- In up state, update the running high using the current bar high before testing the current close for a qualifying retracement. On confirmation, store that running-high bar and flip to down with the current bar low as the new running-low candidate.
- In down state, update the running low before testing the current close for a qualifying rise. On confirmation, store that running-low bar and flip to up with the current bar high as the new running-high candidate.

The confirmation threshold is always the lagged ATR value belonging to the confirmation bar, not the eventual endpoint bar.

## Spatial assignment details

Tested pivot levels are sorted numerically within each pivot period. An observation is assigned to the nearest tested level. Exact equidistance ties are assigned to the lower numerical level. Side-specific adjacent spacing is used for normalized distance; the sole adjacent spacing is extrapolated for the lowest/highest tested level.

## Five-bin coherence slope

The preregistered fitted slope uses unweighted ordinary least squares of pooled terminal rate against frozen distance-bin midpoints `5, 15, 25, 35, 45`. A negative coefficient satisfies the directional-coherence component of the gate; no monotonicity rescue or alternative weighting is allowed after outcomes.

## Bootstrap and p-value implementation

The pair-year cluster list is resampled with replacement, preserving all aggregated numerator/denominator observations within each selected cluster. Each draw recomputes the pooled core-minus-outer rate difference from summed counts.

The 95% interval is the percentile interval of the 5,000 bootstrap effects. The two-sided bootstrap p-value is `2 * min(P(effect <= 0), P(effect >= 0))`, capped at 1.0. Holm adjustment is then applied across the five frozen primary scale-aligned horizon hypotheses.

## Wick-study handoff

Wick fractions may be calculated and persisted as predictor fields during Study 1 processing for computational efficiency, but no wick outcome, threshold comparison or interaction may be inspected until Study 1 eligibility is frozen from its preregistered gate.
