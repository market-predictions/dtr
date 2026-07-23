# Private Market Data Cache Policy

## Purpose

Downloaded Dukascopy OHLC datasets used by DTR research must be retained in a private persistent cache so failed or repeated analyses do not require another full download.

## Storage boundary

- The GitHub repository is public and must never contain raw Dukascopy candles.
- Raw and cleaned market data are stored outside GitHub in the private Drive folder `DTR Private Market Data Cache`.
- GitHub stores only manifests, SHA256 hashes, schema, provenance, cleaning diagnostics, and aggregate research outputs.

## Cache structure

- `GBPUSD/`
- `USA500_PROXY/`
- `USATECH_NQ_PROXY/`

Each instrument folder should contain annual compressed bid/ask or qualified active OHLC files plus a manifest.

## Required retained evidence

For every cached file retain:

- instrument and Dukascopy symbol;
- side: bid, ask, or midpoint-derived;
- timeframe;
- inclusive start and exclusive end timestamps;
- downloader/decoder version or workflow commit;
- raw and cleaned row counts;
- placeholder-removal counts;
- SHA256 checksum;
- schema and timezone;
- known gaps and limitations.

## Workflow rule

1. Check the private cache first.
2. Validate the cached checksum against the manifest.
3. Reuse the cached dataset when the requested period and construction match.
4. Download only missing years or an incremental extension.
5. Never delete the only qualified copy after an analysis failure.
6. Temporary runner copies may be deleted after the persistent cache upload and checksum verification succeed.

## Access and redistribution

The cache is for private DTR research use. Do not publish, commit, attach to public PRs, or redistribute raw market data. Compact evidence and non-reconstructive aggregate diagnostics may remain in GitHub.
