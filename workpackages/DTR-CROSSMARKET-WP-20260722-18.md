# DTR-CROSSMARKET-WP-20260722-18 — NQ versus USA500 parallel replication framework

## Objective

Build and execute a provider-neutral parallel test framework that applies the identical frozen DTR reversal logic to NQ futures and the qualified Dukascopy USA500 bid-CFD proxy, while keeping performance, costs, risk and conclusions separate by instrument.

## Primary comparison period

Use the exact common canonical Eastern Time interval available to the frozen NQ study:

- start: 2022-12-26 18:00 ET;
- end: 2025-12-10 23:58 ET;
- Tuesday–Friday only;
- Asia, London and New York sessions unchanged.

## Arms

For each instrument run:

1. `E6` — exclude setups within 0.25 prior-day ATR of the prior-day directional extreme;
2. `E6_NO_FOMC_DAY` — the same E6 rule plus no entry whose ET calendar date is an official FOMC statement date.

Original E6 remains the cross-market control. `E6_NO_FOMC_DAY` remains the user-authorized working policy baseline.

## Engine contract

- Reuse the exact frozen signal, trade simulation and global one-open-position sequencing code.
- Preserve all dimensionless strategy parameters, session windows, weekday rules, entries, stops, targets, time exits and collision handling.
- No proxy-specific threshold, filter, session, event or parameter tuning.
- Normalize both sources to canonical bar-open Eastern Time before strategy processing.

## Instrument contracts

### NQ

- source: registered NQ futures archive;
- vendor bar-close labels shifted back one minute;
- tick size: 0.25 points;
- point value: $20;
- commission: $2.25 per side;
- slippage scenarios: one, two and four ticks per side.

### USA500 proxy

- source: qualified Dukascopy `USA500.IDX/USD` one-minute bid candles;
- timestamps treated as UTC bar-open labels and converted with `America/New_York` daylight-saving rules;
- structural tick geometry: 0.25 index points, matching ES price increments;
- synthetic ES-equivalent point value: $50 solely for commission-to-R conversion;
- commission: $2.25 per side;
- slippage scenarios: one, two and four 0.25-point increments per side;
- result label: bid-CFD S&P 500 proxy replication, never ES futures validation.

## Data-integrity adapters

- NQ keeps the accepted causal gap classifier unchanged.
- USA500 removes synthetic flat zero-volume rows and does not treat 2–5 minute quote-absence intervals as price gaps.
- USA500 session ranges require at least 95% active-minute coverage.
- USA500 gaps longer than five minutes reset signal state; open trades crossing unscheduled gaps longer than five minutes liquidate at the first observable post-gap price.
- Scheduled daily maintenance, weekends and holidays remain non-tradable/reset boundaries.

## Required outputs

- exact NQ regression gates for E6 and E6 no-FOMC;
- per-instrument signal funnel, qualifying signals and executed trade streams;
- trades, net R, expectancy, profit factor, win rate, median R, maximum drawdown R and return/DD;
- results by year, session and direction;
- one-, two- and four-tick execution stress;
- opportunities and trades per 100 eligible session dates;
- separate date-block uncertainty for each instrument and arm;
- no pooled portfolio, combined equity curve or dollar-performance comparison;
- changed-trade attribution for the FOMC overlay;
- deterministic repeat and independent reconstruction.

## Replication classification

For USA500 E6:

- `DIRECTIONAL_REPLICATION_SUPPORTED`: positive normal-cost expectancy and net R, positive profit factor above 1, positive net R in at least two calendar years, and positive two-tick expectancy;
- `PARTIAL_COST_FRAGILE_REPLICATION`: positive normal-cost expectancy and net R but one or more stability gates fail;
- `NO_REPLICATION`: normal-cost expectancy or net R is non-positive.

The FOMC overlay is reported separately and cannot be optimized or redefined from proxy results.

## Decision boundary

This study evaluates whether the market logic transfers directionally. It does not establish CME ES execution validity, permit pooling instruments, authorize live sizing, change E6, or authorize Pine/deployment.
