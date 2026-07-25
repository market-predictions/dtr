# Stacey Burke Controlled Event Study — Frozen Execution Contract

Version: `v1.0.0`  
Date frozen: `2026-07-25`  
Work package: `SB-WP-20260725-03`  
Status: `FROZEN_BEFORE_FORWARD_OUTCOME_INSPECTION`

This contract implements the controlled study authorized by the successful 2015–2021 event census. It supplements, but does not alter, `EVENT_CENSUS_PREREGISTRATION.md`.

## Frozen census identity

The discovery study is allowed to calculate outcomes only after reproducing these pair counts exactly:

| Pair | Events |
|---|---:|
| EURUSD | 277 |
| GBPUSD | 294 |
| USDCHF | 313 |
| AUDUSD | 215 |
| NZDUSD | 177 |
| USDCAD | 162 |
| USDJPY | 173 |
| EURJPY | 252 |
| GBPJPY | 254 |
| EURGBP | 306 |

The frozen aggregate census ledger SHA-256 is:

`862ec9c28f6e8450b59f6a34da2571a4a3c25075013f11492be8cfc946653533`

Any detector drift blocks the controlled study.

## Primary outcome

For an event reclaimed at minute close `t`, the endpoint is the synchronized active midpoint close exactly 60 minutes after `t`.

- Long reversal outcome: `(midpoint close[t+60] - midpoint close[t]) / ATR20`.
- Short reversal outcome: `(midpoint close[t] - midpoint close[t+60]) / ATR20`.

An event is unobservable if the exact endpoint or required pre-event features are unavailable. No nearest-future fill is permitted.

## Pre-event matching features

At the reclaim close:

- 15-minute return is `log(close[t] / close[t-15])`;
- trailing 60-minute realized volatility is the square root of the sum of the preceding 60 exact one-minute squared log returns, including the return ending at `t`.

Missing or inactive exact-minute inputs make the observation ineligible.

## Control universe

A candidate control minute must:

- be from the same instrument;
- fall in the same analysis partition;
- be inside 07:00 inclusive through 10:00 exclusive in `Europe/London`;
- belong to an eligible session with no retained event and no ambiguity;
- have synchronized active quotes at the candidate close;
- have exact pre-event feature inputs and an exact active 60-minute endpoint.

For each event, controls must share:

- calendar year;
- weekday;
- 15-minute London time bucket.

The event's own London date is excluded.

## Deterministic nearest matching

The two matching features are standardized by the candidate-stratum population standard deviation. Euclidean distance is then calculated in the standardized two-feature space.

Candidate minutes are ordered by distance and timestamp. Only the nearest candidate from each London date remains. The five nearest distinct London dates are selected. There is no outcome-based caliper and no threshold search.

Controls may be reused by different events. Every event-minus-control observation is clustered by its event London date in inference.

## Primary effect

Each control outcome is reversal-signed using the direction of its matched event and normalized by the control's own pre-event ATR20.

For each event:

`effect = event outcome - mean(five matched control outcomes)`.

The pooled arithmetic mean of event-level effects is the single primary discovery statistic.

## Discovery inference and Gate B

- Bootstrap: 10,000 calendar-date block resamples with replacement, seed `20260725`.
- Label permutation: 10,000 matched-set permutations, seed `20260726`.
- One pseudo-event label is selected from the event plus five controls.
- The same pseudo-label position is used for all events sharing an event London date, preserving same-day cross-pair dependence.
- The permutation p-value is one-sided with the finite-sample `+1` correction.

Gate B is unchanged from the original preregistration and requires all six predicates:

1. at least 400 matched observable events;
2. pooled mean effect at least `+0.02 ATR20`;
3. 95% date-block bootstrap lower bound above zero;
4. one-sided date-clustered matched-set permutation p-value no greater than 0.05;
5. positive pair estimates for at least 7 of 10 pairs;
6. positive factor-block estimates for at least 3 of 4 blocks.

Failure stops this Stacey Burke reversal programme. No alternative horizon, matching rule, session, threshold or subgroup may replace the failed primary result.

## Frozen 2022–2023 validation gate

Only a Gate B pass authorizes the untouched 2022–2023 validation run. The event definition, endpoint, controls, matching, seeds and inference methods remain unchanged.

The validation source load includes 2021 only as causal warm-up. Outcomes and controls are restricted to 2022–2023.

Gate C requires all of the following:

1. at least 400 matched observable validation events;
2. pooled mean event-minus-control effect strictly above zero;
3. 95% calendar-date block-bootstrap lower bound above zero;
4. one-sided date-clustered matched-set permutation p-value no greater than 0.05;
5. positive pair estimates for at least 7 of 10 pairs;
6. positive factor-block estimates for at least 3 of 4 blocks.

The discovery minimum-effect threshold of `+0.02 ATR20` is not repeated as a validation magnitude gate; validation must independently establish a positive effect with blocked uncertainty and broad attribution.

Failure at Gate C rejects the mechanism and blocks SB-1. A pass authorizes design of one global executable SB-1 contract, while 2024–2025 remains untouched.

## Prohibited outputs

The controlled study may report midpoint event outcomes, control outcomes, matched differences, inference and attribution. It may not calculate:

- entries or fills;
- stops or targets;
- R multiples;
- commissions, spreads or slippage economics;
- strategy P&L, drawdown, profit factor or expectancy;
- position sizing;
- pair selection or parameter optimization.

Those outputs remain blocked until both Gate B and Gate C pass.