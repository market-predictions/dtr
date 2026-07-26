# Asian Sweep Staged and Extended Operational Amendment v6.2

Date frozen: 2026-07-26  
Applies to v6.0 and v6.1.

## 1. One event per pair/day

The source ledger may contain an upper and a lower sweep on the same instrument/date. Staged policies may not hold opposing positions or replace a failed first hypothesis with a later opposite-side event.

Frozen rule:

- retain the earliest T0 sweep per instrument/Amsterdam date;
- if upper and lower sweeps share the same T0 timestamp, classify the day as `SAME_MINUTE_SIDE_AMBIGUOUS` and do not trade it;
- once the first event is selected, ignore later opposite-side events for that instrument/date, even after the first trade exits;
- report excluded and ignored counts.

Extended-target discovery remains event-level because it is predictive research rather than a daily execution policy. It reports same-day dependence and uses Amsterdam-week groups.

## 2. Staged initial-entry rules

- `T0_QUARTERS`, `T0_CONCENTRATED`, `T0_LATE_WEIGHTED`, `T0_STATIC_025` and `T0_STATIC_100` may enter only when the frozen T0 provisional-eligibility condition is satisfied, except that static references are also reported on the unconditional earliest-event population as diagnostic comparators.
- `T1_QUARTERS` may initiate only when the T1 reversal-add condition is satisfied and no T1 continuation-cancel condition is active.
- later adds are permitted only if an initial tranche is already open;
- a missing landmark row means the event resolved before that decision and no later action is possible.

## 3. Concentrated add semantics

For `T0_CONCENTRATED`:

- if T2 is the first qualifying add, allocate `0.50R` at T2 and optionally `0.25R` at T3;
- if T3 is the first qualifying add, allocate a single `0.75R` tranche at T3;
- never create two separate tranches at the same timestamp and price.

## 4. Decision-time ordering

At each landmark:

1. simulate stop/target path up to but excluding the next decision bar;
2. at the next active quote open, apply continuation cancel first;
3. if no cancel, evaluate initial/add eligibility and enter at that open;
4. simulate that bar and subsequent path.

Thus the landmark decision occurs at the bar open before that minute's high/low is known.

## 5. Position and P&L accounting

For tranche allocation `a` in R units:

- unstressed units = `a / abs(entry_price - stop_price)`;
- market entry receives `0.10` pip adverse slippage;
- target limit receives no additional slippage;
- stop, cancel and time exits receive `0.10` pip adverse slippage;
- tranche P&L in R = units × signed stressed price change;
- portfolio trade R is the sum of tranche P&L;
- maximum sum of allocated tranche risk is `1.00R`.

Same-minute stop and target is `AMBIGUOUS_STOP_FIRST` and is scored as stop-first.

## 6. Extended-target path requirements

- T0/T1 entry must have valid positive risk and positive directional target distance;
- active quote path must extend to within two minutes of the specified horizon for close-dependent labels;
- first-passage labels do not require full-horizon coverage once target or stop is resolved;
- same-minute target/stop is excluded from that target's primary model and counted;
- target levels use executable quote sides: long targets/highs on BID and stops/lows on BID; short targets/lows on ASK and stops/highs on ASK;
- the 16:00 hold label uses the last active executable close before 16:00.

## 7. No protected access

These clarifications are frozen before any source-backed staged result or extended label is generated. All current work remains 2015–2019 development only.
