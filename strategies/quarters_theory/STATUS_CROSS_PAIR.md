# Cross-Pair Replication Status

- Work package: QT-WP-20260805-02
- State: retained-source restoration and frozen-engine execution
- Instruments: EURUSD, USDJPY
- Data window: 2015-2021 only
- Source: qualified ten-pair Stacey Burke Dukascopy BID/ASK M1 artifacts from workflow run `30129064261`
- Source artifact expiry: 2026-10-22
- Holdout: unopened
- Strategy work: blocked pending replication gate

## 2026-08-05 source correction

The initial implementation incorrectly started a new Dukascopy acquisition. Repository audit confirmed that EURUSD and USDJPY had already been acquired and qualified as part of the ten-pair 2015-2025 plus 2026-YTD source universe.

The redundant acquisition run was cancelled. The active workflow now restores the retained July 24 artifacts, verifies their annual source checksums, adapts only timestamp/schema and quote scale, and then invokes the unchanged frozen Stage-1 engine.
