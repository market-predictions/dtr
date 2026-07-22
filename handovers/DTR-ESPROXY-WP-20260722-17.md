# Handover — DTR-ESPROXY-WP-20260722-17

## Status

Data acquisition and qualification complete.

## Decision

`QUALIFIED_WITH_PROXY_LIMITATIONS`

## Temporary local dataset

- Instrument: Dukascopy `USA500.IDX/USD` bid CFD proxy.
- Period: 2022-01-02 23:00 UTC through 2025-12-31 21:13 UTC.
- Active one-minute candles: 1,348,078.
- Active CSV SHA-256: `199d63e6f284eb1ffb93003e9020bf2852f5d96bf78f0efe50c3bdd09c11a47b`.
- Active gzip SHA-256: `0b8fbc0f58071058f8719eae56098a841123234f5bc893764e9611f0ddbec7ae`.
- Raw market data is not in GitHub and must be deleted after testing.

## Next work

Run original E6 and `E6_NO_FOMC_DAY` unchanged and side by side. Treat the result strictly as a bid-CFD S&P 500 proxy replication. Use conservative explicit costs, retain all fixed definitions, and do not optimize against the proxy.
