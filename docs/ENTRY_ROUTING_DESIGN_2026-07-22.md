# Reversal Entry-Routing Design — 2026-07-22

## Decision problem

The frozen reversal strategy currently enters at the accepted structural break close. That route maximizes participation but may pay for extension, widen effective risk, and enter before price demonstrates that the broken structure can hold.

A pullback route can improve entry price and structural information, but waiting also creates three costs:

1. the trade may leave without filling;
2. a delayed fill may occur after the best part of the move;
3. removing or delaying one trade changes later portfolio eligibility.

The work package must therefore compare complete decision routes, not merely compare entry prices on trades that eventually pulled back.

## Strategic contract

- Market: NQ futures.
- Branch: frozen gap-safe reversal strategy.
- Decision point: the existing break-close signal has already become valid.
- Question: enter now, wait for the first valid pullback, or route causally between those choices.
- Null hypothesis: waiting for a pullback does not improve the implementable portfolio enough to compensate for missed opportunities and sequencing effects.

## Frozen components

The following must not change:

- session ranges;
- sweep, reclaim, protected-pivot, BOS/MSS, impulse, and acceptance logic;
- session, weekday, and non-trend filters;
- stop architecture;
- TP1, runner, breakeven, scheduled close, and maximum hold;
- commission, slippage, collision policy, and `reject_unsafe` integrity policy.

Only the entry decision and the causal state required to execute it may differ.

## Event-state model

1. `SIGNAL_ACCEPTED`: frozen break-close signal exists.
2. `ROUTE_SELECTED`: break-close, pullback, or hybrid decision is known using signal-bar information only.
3. `PULLBACK_PENDING`: price has not yet entered the eligible structural band.
4. `PULLBACK_TOUCHED`: the first causal band touch has occurred.
5. `PULLBACK_HELD`: the touch did not invalidate the reversal and has produced the required outward response.
6. `ENTRY_FILLED`: one-minute execution establishes the position.
7. `NO_FILL`: expiry, excessive extension, scheduled close, or route-window end occurs first.
8. `INVALIDATED`: price violates the structural premise before entry.
9. `RESET`: a data-integrity boundary terminates the route.

Every transition must record bar index, timestamp, direction, structural reference, reason, and reset epoch.

## Structural references

The pullback band must be derived entirely from frozen signal information:

- primary reference: the broken protected pivot or BOS level already used by the reversal signal;
- secondary reference for neighbourhood testing: the accepted-break close price;
- band width: greater of a tick allowance and a small fraction of ATR or session range;
- maximum permissible entry extension: explicit multiple of the original signal risk or ATR.

No future swing, future imbalance, or hindsight-selected level may define the band.

## Route definitions

### `ENTRY_BREAK_CLOSE`

Exact frozen baseline entry. This is the regression reference and must reproduce 491 trades and locked metrics.

### `ENTRY_FIRST_PULLBACK`

After the frozen signal:

1. wait for the first touch of the structural band;
2. reject the route if the original invalidation level is breached before fill;
3. require a causal outward response after touch;
4. fill using one-minute data only after that response is known;
5. expire after a versioned number of five-minute bars or at the existing session/time boundary;
6. record no-fill, invalidation, reset, excessive-extension, and scheduled-close outcomes separately.

The pullback cannot be backfilled at the touch price if the hold/rejection requirement becomes known later.

### `ENTRY_HYBRID_PREDECLARED`

At the break-close decision, compute extension from the broken structure relative to ATR and original structural risk.

- use break-close when extension is below a predeclared threshold;
- otherwise wait for the first pullback;
- never switch routes later based on realized outcome;
- threshold neighbourhoods are robustness tests, not permission to select an isolated optimum.

The baseline hybrid threshold will be declared before the full-result run.

## Execution and risk accounting

The route changes entry price, so risk must be reported in two ways:

1. **Frozen structural stop:** preserve the same underlying stop location and calculate actual points/ticks at risk from the new entry.
2. **R-normalized outcome:** calculate realized R using the route-specific actual entry-to-stop distance.

This avoids the hidden error of claiming better entries while silently preserving an obsolete denominator.

Required diagnostics:

- entry-price improvement in points and ticks;
- actual stop distance;
- latency from signal to entry;
- maximum adverse and favourable excursion after signal and after entry;
- missed move before fill;
- no-fill and invalidation rates;
- entry within the original signal bar versus later bars;
- changed scheduled-close exposure;
- route-specific gap and collision handling.

## Signal-level versus portfolio-level analysis

### Signal-level opportunity table

For every frozen signal, report:

- whether each route could fill;
- route entry time and price;
- no-fill reason;
- hypothetical route-specific trade outcome;
- latency, stop distance, MAE, MFE, and entry improvement.

This table answers execution quality independent of position overlap.

### Implementable portfolio table

Run each route chronologically with its own `next_free` state. Attribute:

- retained trades;
- replaced entries for the same signal;
- missed baseline trades;
- newly enabled later trades;
- delayed entries skipped because another route remains open;
- no-fill and invalidation outcomes;
- every net-R difference.

A signal-level advantage is insufficient if portfolio sequencing removes more value than it adds.

## Predeclared baseline parameters

Initial baseline values to be encoded before full-result inspection:

- band reference: broken structural pivot/BOS level;
- minimum width: four ticks;
- ATR width: 0.10 ATR;
- outward response: close back in the reversal direction after touch;
- pullback expiry: 12 five-minute bars;
- maximum extension before touch: 1.50 times original signal risk;
- hybrid break-close threshold: signal extension no greater than 0.35 ATR;
- same structural invalidation and scheduled-close rules as the frozen baseline.

Neighbourhoods:

- band width: 2, 4, 6, and 8 ticks plus 0.05/0.10/0.15 ATR;
- expiry: 6, 12, 18, and 24 bars;
- hybrid extension: 0.20, 0.35, 0.50, and 0.75 ATR.

Only broad stability—not the best cell—can support promotion.

## Tests

Fixtures must cover:

- bullish and bearish pullback symmetry;
- no touch and expiry;
- touch followed by valid outward response;
- touch followed by invalidation;
- response known only after touch, preventing retrospective fill;
- excessive extension before touch;
- reset between signal, touch, response, and entry;
- scheduled close before fill;
- conservative one-minute stop/target collisions after delayed entry;
- route-specific risk denominator;
- hybrid route frozen at the signal decision;
- exact baseline regression;
- changed-trade attribution.

## Promotion sequence

1. Structural fixtures and exact break-close regression.
2. Unfiltered signal-level routing funnel.
3. Implementable portfolio comparison.
4. Band and expiry neighbourhoods.
5. Hybrid-threshold neighbourhood.
6. Chronological and cost stress.
7. Walk-forward route-selection test.
8. Independent adversarial review.

No entry route may be combined with IFVG, CISD, continuation, VWAP, or regime logic before this sequence is complete.
