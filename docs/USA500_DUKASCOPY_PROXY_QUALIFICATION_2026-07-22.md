# USA500 Dukascopy Proxy Data Qualification — 2026-07-22

## Decision

`QUALIFIED_WITH_PROXY_LIMITATIONS`

A temporary 2022–2025 one-minute Dukascopy `USA500.IDX/USD` bid dataset was acquired with actively maintained `dukascopy-node` v1.49.0 and passed the structural qualification gate for a controlled S&P 500 CFD proxy study.

This is not CME ES futures data. It cannot validate ES trade prices, centralized volume, bid/ask spread, contract roll, or futures execution.

## Acquired sample

- Requested range: 2022-01-01 through 2026-01-01, end-exclusive.
- Actual active range: 2022-01-02 23:00 UTC through 2025-12-31 21:13 UTC.
- Downloaded rows before cleaning: 1,747,387.
- Synthetic flat zero-volume rows removed: 399,309.
- Retained active one-minute candles: 1,348,078.
- Duplicate timestamps: zero.
- Timestamp order: strictly increasing.
- OHLC integrity: passed.
- Active CSV SHA-256: `199d63e6f284eb1ffb93003e9020bf2852f5d96bf78f0efe50c3bdd09c11a47b`.
- Active gzip SHA-256: `0b8fbc0f58071058f8719eae56098a841123234f5bc893764e9611f0ddbec7ae`.

## Session coverage

- London range median completeness: 100%; at least 95% complete on 724 of 834 Tuesday–Friday dates.
- New York range median completeness: 100%; at least 95% complete on 823 of 834 Tuesday–Friday dates.
- Overnight trading is present on normal Sunday–Thursday evenings.
- Friday-evening absence reflects the expected weekend closure.
- Seven full holiday closures appeared in the London/New York range census.

## Cleaning decision

The temporary command included the package's `--flats` option. This inserted flat zero-volume placeholders for absent minutes. Every one of the 399,309 placeholders was removed before qualification; all retained candles have positive reported volume.

## Limitations

1. Price is the Dukascopy CFD bid, not an exchange-traded futures last price.
2. Volume is Dukascopy feed volume, not CME volume.
3. Large reopen and news gaps are preserved; the largest adjacent-candle gap was 210.764 index points.
4. Matching ask-candle retrieval failed consistently through the provider/package route. Historical midpoint and observed spread cannot therefore be reconstructed from this acquisition.
5. Subsequent replication must apply explicit conservative transaction costs and remain labelled a bid-CFD proxy study.
6. Raw data is temporary private research material, is not committed to GitHub, and must be deleted after testing.

## Next authorized test

Run original E6 and `E6_NO_FOMC_DAY` unchanged, side by side, on the cleaned proxy dataset. Do not tune thresholds, sessions, event definitions, filters, or costs to improve the proxy result. Do not pool proxy and NQ trades.
