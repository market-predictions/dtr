# Asian Sweep Execution Research Roadmap

Updated: `2026-07-26`

## Current status

The fully validated T5 reversal fingerprint did **not** convert into a viable executable strategy under the frozen midpoint-target / adverse-barrier geometry.

Decision:

`FAIL_DISCOVERY_STOP_BEFORE_EXECUTION_VALIDATION`

The current execution formulation is closed. Validation and holdout P&L for 2020–2025 remain unopened.

## What was learned

1. The predictive model is real: higher scores identify midpoint completion more often.
2. The executable edge is not established: waiting until T5 consumes too much of the remaining payoff.
3. Probability of a successful outcome is not sufficient; entry price, remaining reward, stop distance and fill friction jointly determine expectancy.
4. Higher model scores often imply deeper reclaim and worse remaining reward/risk.
5. Passive limits at the boundary or halfway retracement did not solve the selection/payoff problem.
6. EURUSD was modestly positive while GBPUSD was negative, but pair selection is not authorised.

## Closed path

Do not continue this formulation through:

- threshold tuning;
- EURUSD-only selection;
- weekday/year/side filtering;
- stop or target optimisation;
- partial exits or trade-management additions;
- later-period P&L inspection;
- Pine, alerts or deployment.

## Candidate A — Earlier staged reversal execution

A future independent branch may test whether the mechanism can be entered before the full T5 confirmation has consumed the payoff.

Suggested branch:

`agent/asia-sweep-staged-reversal-execution`

Required new hypothesis:

- assign causal scores at T0, T1, T2, T3 and T5;
- allow a small or conditional entry before T5;
- cancel or exit promptly when later confirmation fails;
- preserve the Asian midpoint as the mechanism target initially;
- measure whether earlier entry improves reward/risk without increasing false-reversal losses excessively.

Required safeguards:

- new preregistration before inspecting 2020–2025 execution P&L;
- fixed staged decision policy learned only from 2015–2019;
- no borrowing the best retrospective entry minute;
- include spread, slippage and same-bar ambiguity from the start;
- validate on 2020–2021 before opening 2022–2025;
- use 2026+ or external-pair transfer if the design consumes existing partitions during redevelopment.

This is a genuinely different causal decision system, not a parameter adjustment to the failed T5 strategy.

## Candidate B — Continuation / fake-rejection triage

The separate roadmap remains:

`FINGERPRINT_CONTINUATION_TRIAGE_ROADMAP.md`

The eventual system should estimate:

1. reversal probability;
2. continuation probability;
3. abstention/conflict state.

It must not use `1 - P(reversal)` as continuation probability. Continuation needs a direct target and new independent evidence.

Potential causal continuation fingerprints include:

- no or shallow reclaim;
- repeated closes outside the Asian range;
- failed boundary retest;
- no reversal-side structure break;
- continued same-side liquidity consumption;
- residual liquidity beyond the sweep;
- cross-pair directional confirmation;
- adverse/favorable excursion imbalance after T5.

## Strategic priority

Recommended order:

1. preserve and merge the validated fingerprint research and negative execution evidence;
2. conduct the continuation-triage mechanism study as a separate programme;
3. consider staged early reversal execution only after its decision policy and untouched-evidence plan are fully specified;
4. do not invest in Pine or UI until one executable programme survives discovery, validation and holdout.

## Stop criterion

If neither staged reversal execution nor direct continuation modelling produces positive, stable, cost-aware results on unseen evidence, close the Asian Sweep strategy family and move to another mechanism family rather than iterating indefinitely.
