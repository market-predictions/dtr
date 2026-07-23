# Asia Sweep Standalone Strategy Specification

## Status

`FOUNDATION_SPEC_FROZEN_BEFORE_PNL`

## Market question

Does failure to hold beyond the completed Asia-session high or low create a repeatable reversal edge during London or New York in NQ and ES?

## Session model

All timestamps are interpreted in `America/New_York` pending source-semantic resolution.

- Asia range: 18:00 previous calendar day to 02:00 trade date, half-open.
- London execution window: 02:00 to 06:00, half-open.
- New York execution window: 08:30 to 11:30, half-open.

## Primary signal rules

A sweep requires penetration of at least two ticks beyond the Asia high or low. A five-minute bar that sweeps both sides is rejected as ambiguous.

### AS-A aggressive reclaim

- downside sweep: close at or above Asia low;
- upside sweep: close at or below Asia high;
- entry timestamp: after the reclaim candle closes.

### AS-B wick-qualified reclaim

AS-A plus:

- rejection wick ratio at least 0.50;
- direction-adjusted close-location value at least 0.60.

### AS-C displacement

AS-A plus an opposing candle within three subsequent five-minute bars:

- directional body agrees with reversal;
- body at least 1.25 times the causal trailing median body;
- close passes the sweep-candle midpoint;
- close remains back inside the Asia range.

### AS-D failed retest

AS-A followed by:

- a one-right-bar confirmed reaction swing;
- a later retest toward the swept level that remains strictly inside the original sweep extreme;
- a later close through the confirmed reaction swing.

The reaction swing is unavailable until the right-side confirmation bar closes.

## Raw risk construction

- stop: two ticks beyond the original sweep extreme;
- target: 2.0R;
- primary exit: full position, no partials, no breakeven move;
- final execution semantics will use next-executable one-minute prices, adverse slippage and conservative stop-first same-minute collisions.

## Portfolio rules

- maximum one open position per instrument;
- first valid signal per execution window wins;
- maximum one trade per London window and one per New York window;
- no same-window re-entry in the primary specification.

## Non-goals

The foundation does not claim profitability, does not optimize parameters, does not compare combined DTR/Asia portfolios and does not authorize Pine or live use.
