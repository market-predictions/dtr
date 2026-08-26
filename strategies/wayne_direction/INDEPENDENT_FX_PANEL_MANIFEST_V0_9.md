# Independent FX Panel Manifest v0.9

Date: 2026-07-27  
Status: `FROZEN_BEFORE_WAYNE_OUTCOMES`  
Panel decision: `PASS_PANEL_QUALIFICATION`

## Admitted panel

| Pair | Minimum yearly coverage | Minimum trading days | Lowest median active minutes/day | Lowest P10 active minutes/day | Seven-year median relative spread | Q1–Q6 |
|---|---:|---:|---:|---:|---:|---|
| EURGBP | 98.86% | 260 | 1430 | 1415.9 | 0.01033% | PASS |
| EURJPY | 99.09% | 260 | 1434 | 1425.0 | 0.00495% | PASS |
| GBPJPY | 99.09% | 260 | 1434 | 1428.0 | 0.01020% | PASS |
| NZDUSD | 98.54% | 260 | 1426 | 1409.9 | 0.01623% | PASS |

All four pairs passed every binding source-quality gate for every year from 2015 through 2021.

## Integrity findings

- 14 required annual BID/ASK files were present and non-empty for every pair;
- compressed-file SHA-256 values matched the source audits;
- timestamps matched the complete UTC calendar-minute grids with no duplicates or annual overlap;
- BID and ASK timestamp alignment was 100%;
- invalid OHLC share was 0%;
- negative-spread observations were 0;
- no expected-open inactivity gap exceeded one trading day;
- no persistent two-month quote-activity collapse was detected.

## Frozen source records

| Pair | Artifact ID | Artifact digest |
|---|---:|---|
| EURGBP | `8609390279` | `sha256:76dd7d15740cb09acecf8c515fd5b23c8260ab5922148f299a8234f157658320` |
| EURJPY | `8607615180` | `sha256:ea6c0bf6796f0f5fb800e96acf503bc146c5de7d8483afa5580b7d1874443452` |
| GBPJPY | `8608715588` | `sha256:068d4ce85d86ce7c5295f994671ec9fcc41def3a47048d301b5958dded3b7fae` |
| NZDUSD | `8607197707` | `sha256:38c580cbad9e040cfa07fca39cb9bde299f0d57be6dc1868ad339b81237af2b1` |

Source workflow run: `30111481052`  
Source head: `6bebbfe07318535cb54569e8dcca1f5a84753ca2`

## Exclusions

The other 18 preregistered candidates were excluded at Q1 because no artifact for them exists in frozen qualified source run `30111481052`. They were not downloaded or selected after viewing Wayne outcomes.

| Excluded candidates | Reason |
|---|---|
| AUDCAD, AUDCHF, AUDJPY, AUDNZD, CADCHF, CADJPY, CHFJPY, EURAUD, EURCAD, EURCHF, EURNZD, GBPAUD, GBPCAD, GBPCHF, GBPNZD, NZDCAD, NZDCHF, NZDJPY | `Q1_NOT_AVAILABLE_IN_FROZEN_QUALIFIED_SOURCE_RUN_30111481052` |

## Governance

- no Wayne staged-sequence outcome was generated or viewed for these pairs before this manifest;
- the panel cannot be altered based on subsequent sequence performance;
- EURGBP, EURJPY, GBPJPY and NZDUSD form the primary independent replication panel;
- 2022–2025 remain excluded;
- yields, VIX, macro and seasonality remain excluded.

The machine-readable annual quality ledger and candidate ledger contain all annual diagnostics and raw-file hashes.
