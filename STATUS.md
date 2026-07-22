# DTR Optimization Lab Status

## Current stacked work package

`DTR-NQ-WP-20260722-09 — Monday inclusion × Asia exclusion factorial research`

Status: **research complete; independent review passed; publication branch active**

Decision state: `RETAIN_TUE_FRI_AND_ASIA`

Base dependency: `DTR-NQ-WP-20260722-08 — Advanced Context Robustness` remains open and draft on PR #8.

## Active timing-corrected exploratory baseline

`DTR_CAUSAL_BAR_CLOSE_RANGE_SHIFT_MINUS1`

- 477 trades;
- 0.089261R expectancy;
- 42.577515R net;
- PF 1.178993;
- maximum drawdown 16.426493R;
- return/DD 2.592003.

The uploaded source archive reproduced the registered checksum and the baseline, E5 and E6 references exactly.

## Monday × Asia factorial result

Four frozen arms were run on the unfiltered strategy and repeated under E5 and E6:

- A0: Tuesday–Friday, Asia + London + New York;
- A1: Monday–Friday, Asia + London + New York;
- A2: Tuesday–Friday, London + New York;
- A3: Monday–Friday, London + New York.

Primary unfiltered results:

- A0: 477 trades, 42.577515R, 0.089261R expectancy;
- A1: 604 trades, 44.648086R, 0.073921R expectancy;
- A2: 349 trades, 27.826440R, 0.079732R expectancy;
- A3: 433 trades, 21.620906R, 0.049933R expectancy.

Findings:

- removing Asia reduced net R under unfiltered, E5 and E6;
- adding Monday did not produce a consistent improvement;
- Monday was positive only under E6, and that contribution was concentrated in Asia Monday;
- adding Monday while removing Asia was inferior under all three layers;
- all 12 metric reconstructions, arm contracts and position-overlap checks passed independent review.

Decision: retain Tuesday–Friday and all three sessions. E6+Monday may remain shadow-only coverage research.

## Frozen fresh-OOS challengers

- Arm 0: unfiltered timing-corrected baseline.
- Arm A: exclude initial ranges below the 33.3rd trailing same-session range/D1-ATR percentile.
- Arm B: exclude setups within 0.25 previous-day ATR of the prior-day directional extreme.
- Arm C: apply A and B together; shadow-only.

The Monday/Asia study does not alter the primary fresh-OOS specification. An E6+Monday series may be recorded separately as a non-decision shadow diagnostic.

## Selection work package status

- original staged 904 chronology: `EXACT_RECONSTRUCTION_BLOCKED`;
- explicit causal execution contract: implemented on PR #7;
- current-code causal 904 universe: paused pending final timestamp-alignment decision;
- no claim that the Monday/Asia study repairs historical selection contamination.

## Existing unresolved gates

- authoritative timestamp metadata or qualified replacement dataset: `UNRESOLVED`;
- continuous-contract methodology: `UNRESOLVED`;
- original 904-search familywise adjustment: `UNRESOLVED_EXACT_RECONSTRUCTION_BLOCKED`;
- qualified fresh OOS Arms 0/A/B: `NOT_RUN_PREREGISTERED`;
- Python/Pine parity: `NOT_RUN`.

## Scope restrictions

No fresh 2026 performance inspection, threshold retuning, new weekday/session search, Pine port, sizing recommendation, leverage increase or deployment is authorized.
