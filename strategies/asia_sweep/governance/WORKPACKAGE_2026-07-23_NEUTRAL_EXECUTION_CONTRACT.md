# Work Package AS-WP-20260723-04 — Neutral Execution Contract and Adversarial Simulator Tests

## Objective

Freeze and implement an isolated, deterministic one-minute post-signal execution adapter for `ASIA_SWEEP_STANDALONE_V0` using synthetic test data only. The package must not calculate or inspect real proxy/futures P&L and must not reuse active DTR signal logic.

## Strategic boundary

The event layer answers whether a setup exists. The execution layer answers whether that already-frozen setup could be filled and exited under explicit one-minute rules. It may not alter signal eligibility, first-sweep ownership, variant confirmation or event timestamps.

## Frozen candidate contract for review

### Signal and entry

- `signal_timestamp` is the close of the determining five-minute bar.
- Entry becomes eligible only at the first one-minute bar whose open timestamp equals `signal_timestamp`.
- Raw entry fill is that one-minute open, not the already-observed five-minute close.
- Directional entry slippage is adverse by the configured number of ticks.
- If the first executable open is at or beyond the protective stop, the trade is not opened and is logged as `ENTRY_GAP_THROUGH_STOP`.
- If no exact entry-minute bar exists, the trade is blocked as `MISSING_ENTRY_MINUTE` rather than silently delayed.

### Stop and target

- The signal-layer stop remains fixed at the original sweep extreme plus/minus the frozen buffer.
- Executed risk is measured from the slipped fill to the fixed stop.
- The executed target is recalculated at the frozen `target_rr` from actual fill and fixed stop.
- Nonpositive or sub-tick executed risk blocks entry.

### Intrabar ordering

- One-minute OHLC does not reveal path ordering.
- If stop and target are both touched in one minute, stop wins.
- On the entry minute, entry is assumed at the open before evaluating high/low.
- If the entry minute touches the stop and target, stop wins.
- Stop fills receive adverse exit slippage.
- Target limits fill at the target price without favorable gap improvement; cost stress is handled separately.

### Gaps and unsafe source intervals

- A bar opening beyond the stop exits at the bar open with adverse slippage and reason `STOP_GAP`.
- A bar opening beyond the target exits at the target price and reason `TARGET_GAP`.
- A missing timestamp after entry liquidates at the first subsequent observed bar open with adverse slippage and reason `DATA_GAP_LIQUIDATION`.
- A source-inactivity run becomes unsafe when its 11th consecutive inactive minute is observed.
- Because a stale carry-forward quote is not executable, liquidation occurs at the first subsequent active bar open with reason `STALE_ACTIVITY_LIQUIDATION`.
- If no active quote resumes before the hard audit horizon, mark `UNRESOLVED_DATA_EXIT`; do not manufacture a return.

### Time exit

- If neither stop nor target exits the position, the trade closes at the first one-minute bar open timestamp equal to execution-window end.
- Directional exit slippage is adverse.
- Missing or inactive time-exit data produce an unresolved exit rather than using a stale synthetic quote.

### Costs and output

- Commission is charged per side from manifest economics.
- Slippage is explicit in ticks and never hidden in commission.
- Store raw and executed entry/exit prices, gross R, commission R, net R, exit reason, collision flag, gap metadata and holding minutes.
- Synthetic tests may assert R arithmetic. Real-data P&L remains disabled by design and workflow separation.

## Required adversarial tests

1. Long and short next-minute entry fills.
2. Missing exact entry minute blocks the trade.
3. Entry open at/beyond stop blocks entry.
4. Entry-minute stop only, target only and both touched.
5. Later-minute stop only, target only and both touched.
6. Stop gap and target gap behavior.
7. One-minute missing-data liquidation.
8. Ten inactive minutes tolerated; the 11th triggers unsafe state.
9. Resumed active quote liquidates a stale position.
10. No resumed activity produces unresolved exit without P&L.
11. Exact window-end time exit.
12. Missing/inactive time-exit handling.
13. Long/short slippage symmetry.
14. Commission and net-R arithmetic.
15. Prefix replay reproduces the same exit once its determining minute is present.
16. Event input is immutable and no DTR signal function is called.
17. Non-synthetic source frames are rejected.

## Prohibited

- real NQ/ES proxy or futures P&L;
- variant comparison or selection;
- parameter optimization;
- DTR/Asia portfolio combination;
- shared DTR execution extraction before locked benchmark replay;
- Pine Script implementation;
- deployment claims.

## Acceptance criteria

1. Contract reviewed and frozen before implementation changes are judged by outcomes.
2. Simulator lives under the standalone Asia Sweep namespace.
3. Every synthetic adversarial test passes on Python 3.11 and 3.12.
4. Conservative ordering and unsafe-data reasons are explicit and deterministic.
5. Prefix causality passes.
6. Existing event ledgers remain semantically stable.
7. Original repository CI remains green.
8. Real/private source frames cannot enter the synthetic execution adapter accidentally.
9. Independent same-session clean-room review is documented honestly.

## Next gate

After merge, a separate controlled-development work package may consider real-data execution only if the locked DTR benchmark has been reproduced where shared utilities are involved and all futures/proxy limitations remain explicit. This package itself does not authorize real-data P&L.
