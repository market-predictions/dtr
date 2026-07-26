# Asian Sweep Continuation Geometry — Preregistration v6.3

Date: 2026-07-26
State: FROZEN_BEFORE_PHASE_A_DECISION
Branch: `agent/asia-sweep-sequential-triage`
Development: EURUSD and GBPUSD, 2015–2019
Protected: 2020–2025

## Decision problem

A continuation trade must be positively identified. It is not defined as `1 - P(reversal)` and it is not every failed or late reversal.

For an upper Asian-range sweep, continuation direction is long. For a lower sweep, continuation direction is short.

The selected Phase A continuation-protection landmark becomes the only eligible primary continuation decision landmark. No alternative landmark may be selected from continuation P&L.

## Entry

- signal is the frozen out-of-fold Phase A `CONTINUATION` decision;
- entry is the first active BID/ASK open after the selected landmark;
- long entries use ASK; short entries use BID;
- events already resolved before the landmark are excluded;
- at most one continuation order per pair/day;
- no same-bar flip from a closed reversal; the earliest continuation entry after a reversal exit is the next active minute.

## Invalidation

Primary continuation invalidation is a material reclaim inside the swept Asian boundary:
- upper sweep long: stop at `asian_high - 0.10 * asian_range`;
- lower sweep short: stop at `asian_low + 0.10 * asian_range`.

The stop is fixed at entry. No wider stop, averaging or post-hoc structural placement is permitted in the geometry gate.

## Frozen continuation objectives

Each objective is evaluated independently from the same entry and stop:

1. `CONT_RANGE_025_1000`
   - reaches `0.25 * asian_range` beyond the sweep extreme before stop by 10:00 Amsterdam;
2. `CONT_RANGE_050_1100`
   - reaches `0.50 * asian_range` beyond the sweep extreme before stop by 11:00;
3. `CONT_RANGE_100_1200`
   - reaches `1.00 * asian_range` beyond the sweep extreme before stop by 12:00;
4. `CONT_NEXT_LIQUIDITY_1200`
   - reaches the nearest confirmed same-side external-liquidity level beyond the sweep before stop by 12:00;
5. `CONT_FIXED_2R_1200`
   - reaches 2R from the executable continuation entry before stop by 12:00.

If an objective lies behind the executable entry or produces non-positive risk/reward geometry, that event is ineligible for that objective.

Same-minute stop/target ambiguity is stop-first and excluded from primary label-quality metrics.

## Geometry gate before P&L

For each objective report:
- eligible events and positive cases;
- unconditional target rate;
- actual entry-to-stop risk and target R:R;
- spread as a fraction of risk;
- target incidence within the frozen Phase A continuation decisions;
- lift versus all eligible events;
- pair/year/direction/weekday breadth;
- top-score versus bottom-score target incidence;
- median stressed expected-value proxy using +0.10 pip entry/exit stress.

An objective may proceed to continuation execution simulation only when:
- at least 400 eligible events and 75 positive cases;
- continuation-decision target rate >=1.60x base;
- positive lift in both pairs and at least four of five years;
- median R:R among selected events >=1.25;
- at least 35% of selected events retain >=1.50R;
- median +0.10-pip stressed expected-value proxy >0;
- no pair/year/direction concentration above 70%.

## Continuation execution gate

Opened only for an objective passing the geometry gate. The first simulation uses:
- one full-position market entry at the frozen next active open;
- the fixed continuation invalidation stop;
- full exit at the passed objective or its horizon;
- conservative stop-first ordering;
- actual BID/ASK;
- +0.10 and +0.25 pip stress.

Pass requirements:
- stressed expectancy >0R;
- positive net R in both pairs and at least four years;
- return/max drawdown >=1.5;
- maximum drawdown <=12R;
- at least 200 completed trades;
- bootstrap probability of positive expectancy >=0.90;
- no single pair/year contributes >45% of net R.

No target, stop, pair or landmark rescue is allowed after this preregistration.

## Relationship to reversal research

Continuation and reversal execution are developed and validated independently. They may be combined into a bidirectional triage engine only after both sides pass their own development and protected-period gates. Otherwise the validated side may operate alone with `ABSTAIN` for the rejected side.
