# Asia Sweep Neutral Execution Contract — Independent Review

## Review identity

A clean-room analytical and programmatic review was performed against PR #32, the frozen Asia Sweep event specification, the synthetic-only simulator, the complete adversarial suite and the published branch diff.

This is an independent reasoning and implementation pass within the same AI work session. It is not an external human, exchange, broker, legal or production-readiness audit.

## Verdict

`APPROVE_SYNTHETIC_NEUTRAL_EXECUTION_FOR_MERGE_BLOCK_REAL_DATA_PNL`

The isolated synthetic execution contract may merge. No real proxy/futures source, event manifest or portfolio workflow may call it in this work package. Real-data P&L, optimization, variant selection, DTR combination and deployment remain prohibited.

## Strategic assessment

The execution layer now answers one narrow question: given an already-frozen Asia Sweep signal, what deterministic outcome follows under explicit one-minute information, conservative collision ordering, source-integrity controls and declared costs?

It does not:

- create, filter or replace signals;
- change first-sweep ownership or variant confirmation;
- inspect historical strategy performance;
- select parameters from outcomes;
- call active DTR signal logic;
- claim that proxy fills represent CME futures execution.

This boundary is appropriate. It keeps signal validity, execution validity and eventual performance inference as separate gates.

## Frozen execution semantics

### Entry

- The signal timestamp is the close of the determining five-minute bar.
- Entry requires an exact one-minute bar whose open timestamp equals the signal timestamp.
- Entry fills at that one-minute open plus adverse directional entry slippage.
- Missing or inactive entry minutes block the trade.
- An entry open at or beyond the fixed protective stop blocks the trade.
- Executed risk of one tick or less blocks the trade.
- The target ratio is locked to the preregistered `2.0R`; other values fail loudly.

### Stop and target

- The signal-layer stop remains fixed.
- The target is recalculated from the actual slipped entry and the fixed stop.
- Entry-minute and later-minute stop/target collisions use conservative stop-first ordering.
- Stop exits receive adverse slippage.
- Target limits fill at the target without favorable gap improvement.
- Stop and target gap behavior is symmetric for long and short signals.

### Missing and stale source data

- A missing post-entry timestamp makes the path unsafe immediately.
- Liquidation occurs at the first subsequent active observed bar open with adverse slippage.
- Inactive carry-forward quotes are not used as fills.
- The 11th consecutive inactive minute makes the path unsafe.
- Liquidation occurs at the first subsequent active bar open.
- If stale activity is already unsafe before a later missing timestamp, the first unsafe stale condition retains ownership of the exit reason.
- No observable active exit before the horizon produces an unresolved outcome with no manufactured return.

### Time exit and costs

- Time exit uses the one-minute bar open exactly at the execution-window end.
- Missing or inactive time-exit data produce an unresolved outcome.
- Entry, stop and market-exit slippage are explicit tick inputs.
- Commission is charged separately per side.
- Exited synthetic outcomes store gross points, gross R, commission R and net R.
- Blocked and unresolved outcomes contain no return.

## Adversarial coverage

The suite covers:

- long and short exact-minute entries;
- missing and inactive entry bars;
- gap-through-stop entry rejection;
- one-tick executed-risk rejection;
- entry-minute stop, target and collision cases;
- later-minute stop, target and collision cases;
- long/short stop-gap and target-gap symmetry;
- missing-minute liquidation after inactive carry-forward rows;
- missing paths with no active exit;
- 10-minute and 11-minute inactivity boundaries;
- stale paths with and without active resumption;
- first-unsafe-condition precedence;
- exact window-end time exits;
- missing/inactive time exits;
- commission and net-R arithmetic;
- target-RR lock;
- prefix replay for target, stop, data-gap, stale and time exits;
- signal and input immutability;
- duplicate, off-grid, non-finite and invalid OHLC rejection;
- signal/bar timezone-awareness compatibility;
- invalid configuration rejection;
- synthetic fixtures without activity metadata;
- absence of active DTR signal-engine calls;
- rejection of every unmarked source frame.

Exact-head isolated Asia Sweep result: `146 passed` on Python 3.11 and 3.12.

## Defects found and resolved

### EX1 — Test fixtures did not isolate their claimed boundary

The first tight-risk fixture still had half a point of risk after entry slippage, and the first stale fixture contained only ten inactive minutes before the window boundary.

**Resolution:** rewrite the fixtures so one-tick risk and the 11th inactive minute are the actual determining conditions.

### EX2 — Static import formatting remained ambiguous

Manual import reordering did not match the pinned Ruff formatter exactly.

**Resolution:** run a temporary branch-only diagnostic with Ruff 0.15.22, apply its exact diff and delete the diagnostic workflow before review.

### EX3 — Invalid source geometry could enter the simulator

The first implementation rejected duplicate and off-grid timestamps but did not reject non-finite prices or invalid OHLC relationships.

**Resolution:** add strict numeric, finite, OHLC and clock-compatibility validation.

### EX4 — Missing-data liquidation could use an inactive quote

The first implementation selected the first observed row after a missing timestamp, even when that row was a zero-activity carry-forward quote.

**Resolution:** liquidate only at the first subsequent active observed bar open. If none appears by the horizon, return an unresolved outcome.

### EX5 — Later missing data could overwrite an already-unsafe stale path

After an 11-minute stale run, a later missing timestamp could relabel the root cause as a generic data gap.

**Resolution:** freeze first-unsafe-condition ownership. The stale reason persists and its duration includes the later missing interval.

### EX6 — Target ratio remained an unnecessary free parameter

Although the strategy specification freezes a 2.0R target, the first signal model accepted arbitrary positive ratios.

**Resolution:** accept only the preregistered 2.0R value in this contract.

## Operational assessment

- New implementation is confined to `src/dtr_lab/strategies/asia_sweep/execution.py`.
- Tests remain under the isolated Asia Sweep suite.
- No manifest, runner or workflow connects real source data to execution.
- The simulator requires the explicit `SYNTHETIC_TEST_FIXTURE` frame attribute.
- The marker is a deliberate workflow guard, not a cryptographic or security boundary; future real-data integration requires a separate reviewed adapter.
- Signal dataclasses and input frames remain unchanged after simulation.
- Prefix replay reproduces every tested determining exit.
- Branch comparison contains no active DTR signal, benchmark or result modification.

## Remaining blockers

1. No real-data event-to-execution adapter exists.
2. No proxy or futures P&L has been generated or inspected.
3. Proxy price-grid normalization and any futures tick-alignment policy are not connected.
4. CME futures timestamp, continuous-contract, roll, volume, commission, slippage and fill validity remain unresolved.
5. Portfolio-level simultaneous NQ/ES exposure and risk limits are not implemented.
6. MFE, MAE and reporting integration are not implemented.
7. The locked DTR benchmark must be reproduced before any shared execution infrastructure is extracted.
8. Existing NumPy/pandas timedelta deprecation warnings remain repository-wide warning debt; they do not change this contract's test result.
9. The synthetic marker can be applied deliberately by code and therefore prevents accidental—not malicious—real-data use.

## Recommendation

Merge PR #32 only after exact-head Ruff, full repository tests, isolated Asia Sweep tests and unchanged event-audit workflows pass. Freeze this simulator as synthetic-only. Open a separate integration work package that maps frozen event records into execution inputs and proves trade-for-trade deterministic replay before authorizing any development-period P&L.
