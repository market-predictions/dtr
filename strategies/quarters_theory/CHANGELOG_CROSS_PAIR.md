# Cross-Pair Replication Changelog

## 2026-08-05 — QT-WP-20260805-02 opened

- Added EUR/USD and USD/JPY Stage-1 replication governance.
- Added aligned Dukascopy M1 bid/ask acquisition with checksum manifests.
- Added deterministic quote normalization that preserves the frozen GBP/USD engine.
- Added a preregistered automated decision gate.
- Added synthetic EUR/USD identity-scale and USD/JPY pip-equivalence tests.

Known limitation: pair outcomes remain pending until the acquisition and replication workflow completes.
