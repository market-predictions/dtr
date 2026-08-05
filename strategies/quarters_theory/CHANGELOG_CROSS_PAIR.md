# Cross-Pair Replication Changelog

## 2026-08-05 — Retained ten-pair source restored

- Corrected the source-discovery failure that caused redundant Dukascopy downloads to start.
- Confirmed the qualified Stacey Burke ten-pair universe contains EURUSD and USDJPY BID/ASK M1 for 2015-2025 plus 2026 YTD.
- Identified unexpired raw-source artifacts in workflow run `30129064261`, retained through 2026-10-22.
- Cancelled the redundant pair-year acquisition workflow.
- Replaced acquisition with authenticated restoration of the retained artifacts.
- Added checksum-preserving schema and quote-scale adaptation for the unchanged frozen Quarters engine.
- Removed the redundant cross-pair downloader from the PR.
- Added retained-source EURUSD identity-scale and USDJPY pip-equivalence tests.

Known limitation: the retained raw artifacts are time-limited GitHub artifacts rather than confirmed permanent Drive copies. Durable source governance must be repaired before artifact expiry.

## 2026-08-05 — QT-WP-20260805-02 opened

- Added EUR/USD and USD/JPY Stage-1 replication governance.
- Added deterministic quote normalization that preserves the frozen GBP/USD engine.
- Added a preregistered automated decision gate.

Known limitation: pair outcomes remain pending until the retained-source replication workflow completes.
