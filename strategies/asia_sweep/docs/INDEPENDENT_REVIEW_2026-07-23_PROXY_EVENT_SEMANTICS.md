# Asia Sweep Proxy Event Semantics — Independent Review

## Review method

A clean-room analytical and programmatic review was performed against PR #31, the canonical private proxy snapshots, the standalone roadmap, the frozen session/activity contracts, the event ledgers and deterministic 50-event samples. The review independently reconstructed all sampled events directly from the one-minute source without calling the production Asia Sweep signal builder.

This is an independent reasoning and implementation pass within the same AI work session. It is not an external human, legal or exchange-data audit.

## Verdict

`APPROVE_PROXY_EVENT_SEMANTICS_FOR_MERGE_BLOCK_EXECUTION_AND_PNL`

The proxy event-semantic layer may merge. Execution simulation, P&L, optimization, variant selection, portfolio combination and futures claims remain prohibited.

## Confirmed

- UTC-authoritative timestamps convert uniquely to `America/New_York` across spring and autumn DST changes.
- Asia and execution windows use local wall-calendar construction rather than elapsed-time arithmetic.
- Quote-grid completeness and source activity are separate integrity dimensions.
- The frozen activity threshold is one positive minute and no inactive run longer than 10 minutes.
- Causal pre-signal activity is evaluated only through the determining bar.
- Future inactivity cannot invalidate an earlier signal.
- `NO_SWEEP` requires full-window integrity and activity.
- Entries at or after window end are rejected.
- First-sweep ownership remains deterministic and cannot be replaced by a later sweep.
- Existing offset-free futures-manifest behavior remains unchanged.
- No active DTR signal or result file is modified.
- No market-data file is committed to Git.
- No execution result or P&L field exists in the ledgers or audit outputs.

## Independent reconstruction

The clean-room validator independently reproduced:

- all 50 NQ-proxy sampled records;
- all 50 ES-proxy sampled records;
- Asia high and low;
- Asia and execution activity metrics;
- first qualifying sweep and side;
- sweep depth and five-minute OHLC;
- wick ratio and direction-adjusted close location;
- AS-B morphology decisions;
- AS-C causal displacement decisions and delay;
- AS-D causal pivot/retest/break decisions;
- raw entry, stop and target geometry;
- entry-window boundary decisions.

Result: `100/100 exact, zero mismatches`.

## Defects found and resolved

### ER1 — End-of-window entry leakage

A bar beginning at 05:55 could close at 06:00 and be emitted as a London signal.

**Resolution:** require `entry_timestamp < execution_window_end`. One historical NQ AS-C candidate is now correctly rejected at 06:00.

### ER2 — DST wall-date drift risk

Subtracting a 24-hour elapsed `Timedelta` from timezone-aware dates could shift local calendar construction across a Sunday DST change.

**Resolution:** construct Asia and execution bounds from explicit New York wall-calendar dates and localize them with ambiguity/nonexistence checks.

### ER3 — Stale quotes conflated with missing bars

A complete Dukascopy quote grid can contain zero-volume carry-forward quotes. Treating those rows as absent would misclassify source structure.

**Resolution:** preserve grid completeness separately and add an independent activity audit with distinct failure reasons.

### ER4 — Full-window activity could erase a prior signal

Using only full execution-window activity would make later stale quotes alter an earlier observable decision.

**Resolution:** retain descriptive full-window activity, but gate an observed event only on the causal path through its determining bar.

### ER5 — Audit sample lacked retained OHLC paths

The initial deterministic sample contained event records but not the underlying price path required by the roadmap’s evidence rule.

**Resolution:** add a clean-room validator and private five-minute OHLC evidence for the complete Asia range and execution window of all 100 sampled records.

### ER6 — Audit artifact transport paths

Initial cross-run downloads assumed an incorrect artifact root and one CLI-specific path.

**Resolution:** use the native GitHub cross-run artifact action and the canonical `prepared/` directory.

### ER7 — Static-analysis formatting

Ruff found one over-length test line.

**Resolution:** apply the exact formatting correction; both CI tracks are green.

## Remaining blockers

1. No neutral post-entry execution adapter exists.
2. Same-minute stop/target and entry-stop collisions are not implemented.
3. Gap liquidation and time exits are not implemented.
4. The locked DTR benchmark must be reproduced before extracting shared execution utilities.
5. CME futures timestamp, continuous-contract, roll, volume, cost and fill validity remain unresolved.
6. Provider authorization for future automated proxy acquisition remains unresolved.
7. No strategy P&L has been generated or inspected.

## Recommendation

Merge PR #31 after exact-head repository CI, isolated Asia Sweep CI and both private reconstruction jobs pass. Freeze the event-semantic layer and open a separate neutral-execution work package. Do not calculate P&L in this work package.
