# Work Package AS-WP-20260723-04 — Neutral Execution Contract and Adversarial Simulator Tests

## Objective

Freeze and implement an isolated, deterministic one-minute post-signal execution adapter for `ASIA_SWEEP_STANDALONE_V0` using synthetic test data only. The package must not calculate or inspect real proxy/futures P&L and must not reuse active DTR signal logic.

## Strategic boundary

The event layer answers whether a setup exists. The execution layer answers whether that already-frozen setup could be filled and exited under explicit one-minute rules. It may not alter signal eligibility, first-sweep ownership, variant confirmation or event timestamps.

## Frozen execution contract

### Signal and entry

- `signal_timestamp` is the close of the determining five-minute bar.
- Entry requires an exact one-minute bar whose open timestamp equals `signal_timestamp`.
- Raw entry fill is that one-minute open, not the already-observed five-minute close.
- Directional entry slippage is adverse by the configured number of ticks.
- If the first executable open is at or beyond the protective stop, the trade is blocked as `ENTRY_GAP_THROUGH_STOP`.
- If no exact entry-minute bar exists, the trade is blocked as `MISSING_ENTRY_MINUTE` rather than silently delayed.
- If the entry minute is inactive, the trade is blocked as `INACTIVE_ENTRY_MINUTE`.

### Stop and target

- The signal-layer stop remains fixed at the original sweep extreme plus/minus the frozen buffer.
- Executed risk is measured from the slipped fill to the fixed stop.
- The target is recalculated at the frozen `2.0R` from actual fill and fixed stop.
- Any target ratio other than 2.0 fails loudly.
- Nonpositive or one-tick-and-smaller executed risk blocks entry.

### Intrabar ordering

- One-minute OHLC does not reveal path ordering.
- If stop and target are both touched in one minute, stop wins.
- On the entry minute, entry is assumed at the open before evaluating high/low.
- Stop fills receive adverse exit slippage.
- Target limits fill at the target without favorable gap improvement.

### Gaps and unsafe source intervals

- A later bar opening beyond the stop exits at the bar open with adverse slippage and reason `STOP_GAP`.
- A later bar opening beyond the target exits at the target and reason `TARGET_GAP`.
- A missing timestamp after entry makes the path unsafe immediately.
- Missing-data liquidation occurs at the first subsequent active observed bar open with adverse slippage and reason `DATA_GAP_LIQUIDATION`.
- Inactive carry-forward quotes are never used as fills.
- A source-inactivity run becomes unsafe when its 11th consecutive inactive minute is observed.
- Stale liquidation occurs at the first subsequent active bar open with reason `STALE_ACTIVITY_LIQUIDATION`.
- The first unsafe condition owns the path: if stale activity is already unsafe before a later missing minute, the stale reason is preserved.
- If no active quote resumes before the hard horizon, return an unresolved outcome without manufactured return.

### Time exit

- If neither stop nor target exits the position, close at the first active one-minute bar open whose timestamp equals execution-window end.
- Directional exit slippage is adverse.
- Missing or inactive time-exit data produce an unresolved exit rather than using a stale quote.

### Validation, costs and output

- Reject unmarked source frames; the adapter is synthetic-test-only.
- Reject duplicate or off-grid timestamps.
- Reject non-finite prices and invalid OHLC relationships.
- Require compatible signal/bar timezone awareness.
- Commission is charged per side and remains separate from slippage.
- Store raw and executed entry/exit prices, gross R, commission R, net R, exit reason, collision flag, gap metadata and holding minutes.
- Blocked and unresolved outcomes contain no return.
- Synthetic tests may assert R arithmetic. Real-data P&L remains disabled by design and workflow separation.

## Completed adversarial coverage

1. Long and short exact-minute entries.
2. Missing and inactive entry minutes.
3. Entry open at/beyond stop.
4. One-tick executed-risk boundary.
5. Entry-minute stop only, target only and both touched.
6. Later-minute stop only, target only and both touched.
7. Long/short stop-gap and target-gap symmetry.
8. Missing-minute liquidation after inactive carry-forward rows.
9. Missing paths with no active exit.
10. Ten inactive minutes tolerated; the 11th triggers unsafe state.
11. Resumed active quote liquidation.
12. No resumed activity produces unresolved exit without return.
13. First-unsafe-condition precedence.
14. Exact window-end time exit.
15. Missing/inactive time-exit handling.
16. Commission and synthetic net-R arithmetic.
17. Frozen 2.0R target ratio.
18. Prefix replay for target, stop, data-gap, stale and time exits.
19. Signal and input immutability.
20. Duplicate, off-grid, non-finite and invalid-OHLC rejection.
21. Signal/bar timezone-awareness compatibility.
22. Invalid configuration rejection.
23. Optional activity metadata on generic synthetic fixtures.
24. Absence of active DTR signal-engine calls.
25. Rejection of every unmarked source frame.

## Prohibited

- real NQ/ES proxy or futures P&L;
- variant comparison or selection;
- parameter optimization;
- DTR/Asia portfolio combination;
- shared DTR execution extraction before locked benchmark replay;
- Pine Script implementation;
- deployment claims.

## Completion evidence

**Status:** `COMPLETE_SYNTHETIC_EXECUTION_FROZEN_REAL_DATA_PNL_BLOCKED`

- Simulator is confined to `src/dtr_lab/strategies/asia_sweep/execution.py`.
- The direct execution/precedence suite contains 37 tests.
- The complete isolated Asia Sweep suite contains 146 passing tests.
- Python 3.11 isolated suite: 146 passed.
- Python 3.12 isolated suite: 146 passed.
- Repository Ruff passed.
- Full repository tests passed on Python 3.11 and 3.12.
- Prefix replay passed for every declared determining exit class.
- Branch comparison modifies no active DTR signal, benchmark or result file.
- No manifest, CLI or workflow connects private proxy/futures data to execution.
- No real-data execution, P&L, optimization or variant selection was performed.

## Review identity

The independent review is a clean-room analytical and programmatic pass in the same AI work session. It is not an external human, exchange, broker, legal or production-readiness audit.

## Decision

`APPROVE_SYNTHETIC_NEUTRAL_EXECUTION_FOR_MERGE_BLOCK_REAL_DATA_PNL`

## Next gate

After merge, open `AS-WP-20260723-05 — Event-to-Execution Integration and Deterministic Replay Gate`. That package must define immutable event mapping, price-grid/source-kind policy and trade-for-trade deterministic replay before any real-data execution is enabled. If shared DTR infrastructure is proposed, reproduce the locked DTR benchmark before extraction. This package does not authorize real-data P&L.
