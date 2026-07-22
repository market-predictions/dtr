# Fresh OOS Context Challenger Preregistration — 2026-07-22

## Status

`PREREGISTERED_DATA_NOT_INSPECTED`

This document supplements the existing fresh NQ OOS preregistration. No January–July 2026 performance data may be inspected before this specification is committed.

## Common strategy

All arms use the frozen causal strategy and timing interpretation:

`DTR_CAUSAL_BAR_CLOSE_RANGE_SHIFT_MINUS1`

No entry, BOS, sweep, stop, target, cost, exit, session, weekday or direction parameter may change.

## Arms

### Arm 0 — unfiltered comparator

No context filter.

### Arm A — exclude compressed initial range

At range completion:

1. compute `range_size / previous_completed_ETH_day_ATR20`;
2. compare with the previous 126 same-session observations, requiring at least 40 prior observations;
3. skip the signal when its percentile is below `1/3`;
4. pass through observations during feature warm-up rather than filtering them.

### Arm B — exclude near prior-day directional extreme

Before signal evaluation:

1. use the previous completed ETH-day high, low and ATR20;
2. for a prospective long reversal, use the distance from the initial-range low to the previous-day low;
3. for a prospective short reversal, use the distance from the initial-range high to the previous-day high;
4. skip the signal when absolute distance is `<= 0.25 × previous-day ATR20`;
5. pass through observations during feature warm-up.

### Shadow Arm C — both filters

Apply Arm A and Arm B simultaneously. This arm is descriptive and cannot displace A or B unless it accumulates at least 250 total trades across historical plus untouched forward data and separately passes the statistical gate.

## Primary comparison

For each arm report:

- completed trades;
- net R;
- expectancy per trade;
- R per 100 eligible session opportunities;
- profit factor;
- maximum drawdown R;
- return/DD;
- one-, two- and four-tick slippage stress;
- calendar-month and session-date block intervals;
- paired session-date return difference versus Arm 0;
- session and half-year concentration;
- funnel and trade-rate drift.

## Decision rule

A challenger may advance to frozen paper-forward research only when:

- it has at least 80 fresh completed trades, otherwise extend without retuning;
- fresh net R is positive;
- fresh expectancy is at least 0.08R;
- two-tick expectancy remains positive;
- the paired fresh per-session delta versus Arm 0 is positive;
- no unresolved data or contract event explains the result;
- trade-rate and feature-availability differences are documented;
- no parameter or threshold is changed after inspection.

A pass does not authorize deployment.
