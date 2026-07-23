# Work Package AS-WP-20260723-03 — Proxy Timezone, Activity and Event Semantics

## Objective

Make the registered Dukascopy USATECH and USA500 proxy snapshots safe for official Asia Sweep event-ledger generation without enabling execution simulation or P&L.

## Scope

1. Load UTC-authoritative full-grid proxy archives.
2. Convert timestamps causally to `America/New_York` while preserving DST identity.
3. Preserve quote-grid integrity and source-activity integrity as separate audit dimensions.
4. Apply the frozen activity rule independently to the Asia range, execution window and causal pre-signal path.
5. Reject any entry timestamp at or after the half-open execution-window end.
6. Add adversarial and causality tests.
7. Generate official no-P&L ledgers for NQ and ES proxies.
8. Produce deterministic 50-event audit packets per proxy.
9. Keep proxy evidence separate from CME futures evidence.

## Frozen activity contract

An audited interval is eligible only when:

- every expected one-minute timestamp exists;
- at least one minute has positive source activity;
- no consecutive run of zero-volume source rows exceeds 10 minutes.

Failure reasons remain distinct:

- `missing_minute_grid`;
- `no_positive_volume_activity`;
- `stale_quote_run_exceeded`.

The Asia range must pass in full. For an observable signal or rejection, only source information available through the determining bar may affect eligibility. A later stale run may not erase a prior causal decision. `NO_SWEEP` requires a complete and active full execution window.

## Frozen timestamp contract

- source clock: UTC;
- session clock: `America/New_York`;
- one-minute labels: bar-open timestamps;
- execution and Asia windows: half-open;
- offset-aware timestamps must remain unique through DST;
- session logic derives New York wall time from UTC rather than trusting offset-free local strings.

## Entry-boundary correction

A signal is executable only when:

`entry_timestamp < execution_window_end`

An otherwise valid setup at or after the boundary becomes `REJECTED` with reason `entry_at_or_after_window_end`.

## Tests

Minimum additions:

1. UTC-to-New-York conversion across spring and autumn DST changes.
2. A 10-minute inactive run passes and an 11-minute run fails.
3. An all-zero interval fails separately from a missing-grid interval.
4. A future stale run does not retroactively remove a prior signal.
5. A 05:55 London reclaim whose bar closes at 06:00 is rejected.
6. A late displacement or failed-retest confirmation is rejected at the boundary.
7. Prefix replay preserves activity and entry decisions.
8. Existing NQ/ES futures-manifest behavior remains unchanged.

## Prohibited

- strategy P&L;
- stop/target execution simulation;
- optimization or variant selection;
- combined DTR/Asia research;
- publication or redistribution of proxy market data;
- futures execution claims from proxy evidence.

## Acceptance criteria

1. Dedicated proxy manifests run only after the adapter is implemented and their hard blocks are removed deliberately.
2. All interval-integrity and activity outcomes are reproducible and separately classified.
3. No signal enters at or after the window end.
4. Official event ledgers contain `pnl_calculated: false` and no realized-return fields.
5. At least 50 deterministic audit records per proxy cover statuses, variants, directions, windows and edge cases.
6. Original repository CI and isolated Asia Sweep CI pass on Python 3.11 and 3.12.
7. Independent review confirms causality, isolation and the continuing P&L prohibition.

## Completion evidence

**Status:** `COMPLETE_EVENT_SEMANTICS_FROZEN_EXECUTION_AND_PNL_BLOCKED`

- Proxy manifests are enabled only for event-ledger generation; execution remains blocked.
- Four development ledgers were generated per proxy, with 780 records per variant.
- Deterministic audit samples contain 50 NQ-proxy and 50 ES-proxy records.
- A clean-room validator independently reconstructed all 100 sampled events directly from canonical one-minute data without calling the production signal builder.
- Validation result: 100/100 exact, zero mismatches.
- Private five-minute OHLC evidence contains 6,900 NQ rows and 6,888 ES rows.
- One NQ AS-C entry at exactly 06:00 is correctly rejected.
- Two ES signals remain valid despite later full-window staleness because their causal pre-signal paths are active.
- Repository Ruff/tests and isolated Asia Sweep tests pass on Python 3.11 and 3.12.
- Private audit workflow `30003836567` passes both proxy jobs and removes source data before artifact upload.
- No execution simulation, P&L, optimization or variant selection was performed.

## Review identity

The independent review is a clean-room analytical and programmatic pass in the same AI work session. It is not an external human, legal or exchange-data audit.

## Decision

`APPROVE_PROXY_EVENT_SEMANTICS_FOR_MERGE_BLOCK_EXECUTION_AND_PNL`

## Next gate

Successful completion freezes proxy event semantics and permits a separate neutral execution-adapter design work package. It does not authorize P&L. The execution work package must freeze collision, gap, cost and time-exit semantics and pass synthetic adversarial tests before real-data performance research is considered.
