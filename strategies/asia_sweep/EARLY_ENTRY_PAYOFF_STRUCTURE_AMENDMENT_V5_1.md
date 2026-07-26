# Asian Sweep Early-Entry Payoff-Structure Amendment v5.1

Date: 2026-07-26  
Branch: `agent/asia-sweep-early-entry-research`

## Status

`FROZEN_BEFORE_LANDMARK_OUTCOME_OR_POLICY_PNL_INSPECTION`

This amendment is binding on the conditional execution-policy stage described in `EARLY_ENTRY_INFORMATION_FRONTIER_PREREGISTRATION_V5_0.md`.

## Purpose

The Asian midpoint is a first objective, not necessarily the correct liquidation point for the full position. If a pre-T5 landmark passes the information-payoff viability gate, the execution-policy programme must compare three fixed position structures:

1. `TP1_50_RUNNER_50`: close 50% at the Asian midpoint and retain 50%;
2. `TP1_25_RUNNER_75`: close 25% at the Asian midpoint and retain 75%;
3. `NO_TP1_FULL_RUNNER`: do not reduce at the midpoint; retain 100% until the frozen final target, stop or time exit.

These variants are not used to select the entry landmark. Phase 1 remains a no-P&L information-versus-payoff study.

## Separation of decisions

The programme is sequential:

1. select the earliest viable causal landmark using only out-of-fold predictive information and executable entry geometry;
2. freeze one final-target family, time-exit family and stop-management family without using 2020–2025;
3. compare the three position structures through nested leave-one-year-out development on 2015–2019;
4. select a deployable structure only when it passes the complete breadth, cost, drawdown and stability gates;
5. open 2020–2021 only after the complete entry-and-payoff policy is frozen.

Entry landmark, entry threshold, TP1 fraction, final target, horizon and stop policy may not be optimized jointly in one unrestricted grid.

## Midpoint handling

- The midpoint remains a path landmark for every structure.
- For `TP1_50_RUNNER_50` and `TP1_25_RUNNER_75`, the partial exits on the first executable midpoint touch.
- For `NO_TP1_FULL_RUNNER`, midpoint passage is recorded but causes no position reduction.
- No structure may use knowledge of post-midpoint continuation when deciding whether to take TP1.

## Final-target and horizon boundary

The failed long-runner study established descriptive—not validated—interest around 3R–4R and later exits. Those results may inform the economic hypothesis but may not be imported as a selected policy.

A future execution-policy amendment must freeze a compact final-target and time-exit manifest before P&L. It must include a structural control and may include a small set of R-multiple targets, but it may not repeat the former 40-policy search unchanged or expand it after seeing results.

## Required attribution

For every position structure, report:

- total expectancy and stressed expectancy;
- TP1-leg and retained-position contribution;
- midpoint hit rate;
- post-midpoint continuation distribution;
- final-target, stop and time-exit frequencies;
- pair, year, weekday and sweep-side breadth;
- drawdown and return/drawdown;
- calendar-week bootstrap;
- contribution of the largest winner;
- incremental value relative to the other two structures on identical entries.

## Selection rules

A partial structure cannot win merely by increasing win rate. Selection must prioritize:

1. positive 0.10-pip-stressed expectancy;
2. both-pair and annual breadth;
3. drawdown and return/drawdown;
4. bootstrap confidence;
5. stability of the selected structure across outer folds;
6. lower management complexity as the final tie-breaker.

Complexity order for ties:

1. `NO_TP1_FULL_RUNNER`;
2. `TP1_25_RUNNER_75`;
3. `TP1_50_RUNNER_50`.

This order reflects fewer order-management actions, not an assumption that no TP1 is economically superior.

## Prohibitions

- no use of payoff results to select T0, T1, T2 or T3;
- no pair-specific TP1 fraction;
- no weekday-, side-, range-width- or score-bucket-specific fraction;
- no dynamic fraction selected from future path information;
- no post-hoc addition of 10%, 33%, 75% or other fractions;
- no opening 2020–2025 before the complete policy passes discovery;
- no Pine, alerts, paper trading or deployment before execution validation.

## Interpretation boundary

This amendment guarantees that the entry-optimization programme tests the user's intended alternatives—smaller partial profit-taking and letting the full position run—without allowing those alternatives to contaminate landmark discovery or become an unrestricted rescue grid.
