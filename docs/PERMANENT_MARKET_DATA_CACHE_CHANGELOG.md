# Permanent Market Data Cache Changelog

## v1.0.0 — 2026-08-06

### Added

- Established one canonical private Google Drive hierarchy for the qualified ten-pair Dukascopy M1 BID/ASK universe.
- Migrated exact source artifacts for all ten registered pairs.
- Preserved complete 2015–2025 data plus 2026 YTD ending exclusive 2026-07-24.
- Split archives byte-for-byte into 64 MiB parts without changing original bytes.
- Registered original archive and part sizes and SHA-256 values.
- Added deterministic verification, reconstruction and safe extraction.
- Added root-level cache-first controls and CI policy protection.
- Added mandatory cache-miss authorization to the legacy Dukascopy static-proxy downloader.

### Validated

- Drive root contains all ten pair folders.
- Canonical folder is private, not shared and owner-only.
- EURUSD restore drill reconstructed the exact source archive and extracted safely.
- Reconstructed EURUSD SHA-256: `ce7a82e08c1088e003917b1cd4908f194c9fa8245d30ef61fa5401f7571a042d`.
- Isolated cache-control suite: 8 tests passed.
- Full repository CI run `31056524718`: success.
- Ruff passed.
- Full repository tests passed on Python 3.11 and Python 3.12.
- Pull request #68 squash-merged into `main` as `29028e757d98bb92d8047fc95db686567c5d9fb8`.

### Decision

`PERMANENT_PRIVATE_FX_CACHE_ACTIVE_AND_MANDATORY`

### Known limitations

- A second encrypted off-provider mirror is not yet configured.
- Automated CI retrieval requires authenticated private Drive access or a pre-materialized cache.

### Next

- Add a second encrypted mirror.
- Add periodic permission, inventory and reconstruction audits.
- Register incremental post-2026-07-24 partitions without mutating frozen history.
