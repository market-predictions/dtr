# NQ Continuation Engine Design — 2026-07-21

## Decision problem

The continuation branch must answer one operational question: after price leaves a session range, has the market accepted the new price area strongly enough that following the break has better expectancy than fading it or doing nothing?

A raw boundary cross is insufficient. It may be noise, a liquidity sweep, or the first leg of a reversal. The engine therefore separates break attempt, acceptance, entry routing, and failure.

## Strategic design

### Target use

- Instrument: NQ futures.
- Horizon: intraday.
- Source ranges: London 2AM, New York 9AM, Asia 7PM.
- Trader decision: follow an accepted break, wait for pullback confirmation, or remain flat.
- Research standard: independent value before combination with reversal.

### Null hypothesis

After realistic costs, accepted session-range breakouts do not provide stable, independently positive expectancy across chronological validation periods.

The branch must attempt to reject this null hypothesis rather than assume continuation exists.

## Tactical design

### State machine

1. `IN_RANGE`: range complete; no qualifying break.
2. `BREAK_ATTEMPT`: price closes outside the selected boundary.
3. `ACCEPTANCE_PENDING`: one-bar or two-bar confirmation is incomplete.
4. `ACCEPTED_BREAKOUT`: acceptance contract satisfied.
5. `ENTRY_ELIGIBLE`: immediate or pullback route is available.
6. `OPEN_TRADE`: continuation position is active.
7. `FAILED_BREAKOUT`: price returns inside or invalidates the continuation thesis.
8. `EXPIRED`: decision window closes without entry.

Every transition will carry an explicit timestamp, direction, boundary, reason, and source session.

### Baseline breakout contract

For direction `d ∈ {-1, +1}`:

- boundary is range low for shorts and range high for longs;
- break close must exceed the boundary by `max(tick_buffer, ATR_fraction)`;
- the breakout bar must occur inside a versioned decision window;
- any data reset terminates the event state.

### Acceptance variants

- **One-bar:** the break close itself is the accepted close.
- **Two-bar:** a second consecutive close remains outside the boundary and does not materially retrace into the range.

Acceptance duration is tested as a structural alternative, not combined into one score initially.

### Entry routes

- **Immediate:** enter at the accepted close with conservative one-minute execution.
- **First pullback:** wait for the first revisit of a boundary band; require outward rejection before entry.

The routes produce separate trade populations and reports.

### Failure contract

Before entry, invalidate when:

- price closes back inside the range;
- the opposite boundary breaks;
- extension exceeds a maximum entry distance;
- the decision window expires;
- an integrity reset occurs.

After entry, the structural stop and failed-breakout exit are reported separately so stop design is not hidden inside signal logic.

### Diagnostics before gates

The first baseline records, but does not hard-filter:

- breakout displacement relative to ATR and median range;
- volume expansion;
- distance from session boundary;
- ETH/session VWAP alignment and slope;
- efficiency ratio and ADX;
- range size and prior compression;
- time since range completion;
- session, weekday, direction, and volatility regime.

Only diagnostics showing stable independent value and reasonable opportunity coverage may become filters.

## Operational design

### Code boundaries

- New continuation module and dataclasses.
- Shared immutable market arrays and gap-safe execution utilities where appropriate.
- No modification to frozen reversal manifests or expected baselines.
- New continuation manifests and result namespace.

### Performance constraints

- Vectorize reusable features.
- Precompute session/event indices.
- Avoid repeated DataFrame slicing inside configuration loops.
- Keep candidate grids staged and bounded.
- Reuse immutable market arrays across configurations.

### Repainting and lookahead equivalent

The Python engine must only use information available at each bar close or one-minute intrabar timestamp. Acceptance bars, pivots, VWAP, and filters cannot reference future observations. Delayed confirmation must be recorded as entry latency, not retrospectively shifted.

### Testing

Fixtures will cover:

- upside and downside accepted breaks;
- one-bar versus two-bar acceptance;
- immediate and first-pullback entries;
- return-inside failures;
- opposite-side failures;
- extension expiry;
- integrity reset during each event state;
- conservative stop/target collisions;
- clean-data determinism.

### Promotion sequence

1. Structural fixtures and baseline engine.
2. Unfiltered full-dataset funnel.
3. Chronological period attribution.
4. Entry-route and acceptance ablations.
5. Risk/exit ablations.
6. Context diagnostics and limited filters.
7. Cost, neighbourhood, and walk-forward tests.
8. Independent review.

No adaptive routing or reversal combination is allowed before step 8.
