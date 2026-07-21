# NQ One-Minute Dataset Audit

Date: 2026-07-21

## Source artifact

- Archive: `NQ_Futures_-_1min_Bar_2022_2025.zip`
- Member: `Dataset_NQ_1min_2022_2025.csv`
- Archive SHA-256: `8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc`
- Archive size: 19,141,759 bytes
- CSV size: 72,522,264 bytes

## Observed schema

```text
timestamp ET
open
high
low
close
volume
Vwap_RTH
Vwap_ETH
```

## Coverage and integrity

- Rows: 1,048,575
- First timestamp: 2022-12-26 18:01 ET
- Last timestamp: 2025-12-11 20:52 ET
- Sorted ascending: yes
- Duplicate timestamps: 0
- Missing values: 0
- Invalid OHLC rows: 0
- Non-positive volume rows: 0
- Consecutive one-minute intervals: 99.91312019%
- Gaps over one minute: 910
- Gaps over five minutes: 772
- Gaps over one hour: 767
- Largest observed gap: 3 days 01:01

The majority of long gaps are plausibly explained by the normal daily maintenance break, weekends, and holidays. They still need to be classified against an exchange calendar before the data is approved.

## Critical findings

### 1. Probable Excel export cap

The dataset contains exactly 1,048,575 data rows. Together with one header row, this equals Excel's maximum worksheet size of 1,048,576 rows. The last record occurs at 20:52 ET rather than at a natural session boundary.

Working conclusion: the CSV was probably truncated by an Excel-row limit. The file remains useful for framework development, but its final date must not be treated as a complete trading day.

### 2. Contract continuity is unresolved

The file appears to be a continuous NQ price series, but the archive does not encode:

- source contract symbols;
- rollover dates;
- volume-based or calendar-based roll policy;
- back-adjustment method;
- treatment of roll gaps.

Large close-to-next-open gaps occur, especially around Sunday opens. They may reflect genuine weekend repricing, contract roll effects, or both. Optimization must not begin until these are classified sufficiently for the intended strategy horizon.

### 3. Timestamp semantics are unresolved

The column is labelled `timestamp ET`, but it is not yet known whether each timestamp represents:

- bar open time;
- bar close time;
- source-vendor display time;
- fixed EST or daylight-aware Eastern Time.

The loader deliberately leaves timestamps timezone-naive until this is resolved. An incorrect one-minute shift or fixed-EST assumption would alter DTR session ranges and setup timestamps.

### 4. Supplied VWAP columns are provisional

`Vwap_RTH` is zero on approximately 67.86% of rows, which is consistent with being populated only during a restricted session. `Vwap_ETH` is populated on all rows.

The Lab should reconstruct both VWAP variants from OHLCV and explicit session-reset rules. Supplied VWAP values can then be used as a comparison target, not as unquestioned model input.

## Approval status

Approved for:

- data-pipeline development;
- resampling tests;
- session-calendar analysis;
- intrabar execution research;
- preliminary DTR parity work.

Not yet approved for:

- production performance claims;
- final parameter optimization;
- automatic transfer of findings to FX;
- conclusions sensitive to rollover or exact session timestamps.

## Next audit gates

1. Identify timestamp convention using known session opens and TradingView comparison bars.
2. Classify every non-one-minute gap against maintenance, weekend, holiday, or unexplained categories.
3. Detect probable roll dates and quantify discontinuities.
4. Compare reconstructed RTH/ETH VWAP to supplied columns.
5. Exclude the incomplete final session from canonical datasets.
6. Write normalized one-minute and five-minute Parquet files with metadata and checksums.
