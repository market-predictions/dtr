# Asian Sweep Ten-Pair FX Status

Date: 2026-07-25  
Work package: `AS-WP-20260725-10`  
State: `COMPLETE_DISCOVERY_FAILED_VALIDATION_BLOCKED`

## Final decision

`FAIL_DISCOVERY_STOP_BEFORE_MECHANISM_VALIDATION`

A causally confirmed London rejection of the completed Asian range did not add positive 60-minute reversal value relative to matched non-rejection boundary breaches across the fixed ten-pair FX universe.

## Primary evidence

- 2,498 matched rejection events;
- 12,490 distinct-date matched controls;
- mean event return: `+0.005890` Asian-range fractions;
- mean control return: `+0.024507`;
- mean event-minus-control effect: `-0.018617`;
- 95% date-block interval: `[-0.046224, +0.008483]`;
- one-sided clustered permutation p-value: `0.910809`;
- positive pairs: `4 / 10`;
- positive factor blocks: `1 / 4`.

Five sample/breadth/concentration predicates passed. All five effect, inference and directional-breadth predicates failed.

## Integrity status

Complete and independently reconstructed:

- exact five-control cardinality;
- distinct control dates;
- zero same-date leakage;
- pair and factor attribution;
- event-minus-control arithmetic;
- clustered bootstrap and permutation;
- all frozen gates.

No implementation or source defect explains the negative result.

## Current authorization

Authorized:

- retain the study as negative research evidence;
- manually reproduce the frozen 2015–2019 run;
- reuse the generic source and matched-control infrastructure for genuinely new preregistered hypotheses.

Blocked:

- 2020–2021 mechanism validation;
- executable entries, stops, targets, costs and strategy P&L;
- 2022–2025 outcome inspection;
- pair, direction, weekday or regime selection;
- NZDUSD or positive-pair rescue;
- PDH/PDL-cluster rescue within this trial;
- Pine, alerts, sizing, paper trading and deployment.

See `FINAL_DECISION_FX_TEN_PAIR.md` for the complete audit record.
