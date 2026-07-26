# Asian Sweep Context and Regime Atlas — Independent Artifact Audit

Date: 2026-07-26  
Evidence: authoritative run `30219172600`

## Audit scope

The downloaded decision artifact was independently inspected outside the workflow. The audit covered:

- pooled event identity and uniqueness;
- pair and year census;
- economic-eligibility census;
- state membership for `sweep_half_hour::0900_0929`;
- target counts and success rates;
- stressed payoff means and relative effects;
- pair/year attribution;
- passing-state census;
- family authorization logic;
- interaction and router boundaries.

## Reconciled invariants

- 2,900 pooled event ids; zero duplicates;
- exactly EURUSD and GBPUSD;
- exactly 2015 through 2021;
- 2,899 economically eligible events;
- 106 tested states;
- exactly one state passed all frozen gates;
- exactly one factor family passed;
- interaction authorization correctly failed because two independent passing families were required.

## Passing-state reconstruction

`sweep_half_hour::0900_0929` reproduced:

- 600 events;
- 155 successes;
- 25.8333% hit rate;
- 16.3448% pooled baseline;
- +9.4885 percentage-point lift;
- -0.394671R mean stressed payoff proxy;
- -0.568401R pooled baseline payoff;
- +0.173730R relative economic effect;
- 316 EURUSD and 284 GBPUSD events;
- positive relative pair effect for both pairs;
- positive relative year effect for all seven years.

The state summary, subgroup summary, family summary and JSON decision agree.

## Higher-timeframe and regime reconciliation

No state in the following families passed all gates:

- higher-timeframe direction;
- trend strength;
- trend change;
- volatility;
- causal location.

The closest broad state was `d1_efficiency_state::ORDERED`, but it failed the minimum hit-rate-lift threshold and full-atlas FDR correction. Its absolute mean payoff remained negative.

## Verdict

`APPROVE_FAIL_SINGLE_FACTOR_ATLAS_STOP_BEFORE_INTERACTIONS`

The negative higher-timeframe/regime conclusion and the limited session-timing attribution result are supported by the published evidence. No arithmetic or decision inconsistency was found.
