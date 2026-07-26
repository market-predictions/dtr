# Wayne Pivots Daily Geometry — Independent Artifact Audit

Date: 2026-07-27  
Evidence: authoritative run `30223457477`

## Audit scope

The downloaded decision artifact was inspected independently outside the GitHub Actions workflow. The audit covered:

- pooled event identity and duplicate keys;
- instrument and year boundaries;
- fresh-event census;
- Wayne source-faithful event counts and absolute outcomes;
- all 60 paired Wayne-versus-placebo comparisons;
- comparison-gate reconstruction;
- candidate-level authorization logic;
- core prior-close and range-midpoint comparisons;
- pair/year breadth;
- artifact file hashes;
- bias and execution boundaries.

## Reconciled invariants

- 596,277 pooled event-target rows;
- 547,764 fresh event-target rows;
- zero duplicate instrument/day/structure/side/target keys;
- exactly six instruments: AUDUSD, EURUSD, GBPUSD, USDCAD, USDCHF and USDJPY;
- exactly years 2015 through 2021;
- zero rows after 2021;
- exactly 11 structures and 60 paired comparisons;
- exactly 20 comparisons passed all individual gates;
- zero of six candidates passed the geometry gate;
- bias authorization correctly remained closed.

## Source-faithful outcome reconstruction

The pooled Wayne rows reproduced:

- bull: 9,241 fresh events;
- bear: 9,382 fresh events;
- bull M4: 17.4548% success, -0.413527R;
- bull R1: 29.9102% success, -0.205167R;
- bull R2: 10.5616% success, -0.571057R;
- bear M1: 18.3543% success, -0.381572R;
- bear S1: 29.7485% success, -0.208654R;
- bear S2: 11.2449% success, -0.543028R.

All six pair-level means were negative for all six source-faithful targets. Annual means were negative in every year from 2015 through 2021.

## Core-anchor reconstruction

The independent paired merge reproduced the published Wayne-minus-control effects.

Wayne versus prior close:

- negative payoff effect in five comparisons;
- essentially zero positive effect only for bull R2 at +0.000505R;
- no comparison passed.

Wayne versus prior-range midpoint:

- effects ranged from approximately 0R to +0.040R;
- maximum hit-rate lift was +2.60 percentage points;
- no comparison reached the frozen +5-point lift gate;
- no comparison passed the complete individual gate.

The family-level result is therefore not caused by sample insufficiency. Every Wayne candidate had more than 9,000 fresh events and all six pairs exceeded the minimum breadth requirement.

## Gate reconstruction

The individual comparison predicate was independently recomputed from the CSV columns:

- minimum event count;
- pair event breadth;
- +5-point hit lift;
- positive payoff effect;
- pair and year positive breadth;
- pair/year concentration limits;
- block-bootstrap probability;
- adjusted q-value.

The recomputed predicate agreed with all 60 published `passes_all_gates` values and reproduced exactly 20 passes.

The candidate predicate also reconciled:

- no candidate was positive versus at least eight of ten placebos;
- no candidate produced five full comparison passes;
- no candidate achieved a complete prior-close or range-midpoint anchor pass.

## Metadata audit note

The original pair-day ledger wrote the non-authoritative `previous_wayne_p` metadata value after assigning the current pivot. The actual `pivot_slope_state` was computed before that assignment and was correct. Neither field entered the geometry comparison or authorization decision.

The public package output has been corrected to reconstruct `previous_wayne_p` by a causal one-day shift, and a regression test was added. No scientific rerun is required because the geometry artifact did not consume this metadata.

## Artifact hashes

- `wayne_pivots_geometry_decision.json`: `099641b1fafab1129ca1503e03e58be1e44bbd9d921cf2901f8e88cfe1390d72`;
- `wayne_pivots_candidate_summary.csv`: `3ca3112cef5b13249009dcdc431a9e1a23d434c08e866178eb24ab940f9308b5`;
- `wayne_pivots_comparison_summary.csv`: `8b39841bfaae5df8e1d5ce498cf54ab6900cc4dcbd3fecefba080011068309b2`;
- `wayne_pivots_subgroup_summary.csv`: `1d7d5fe06908ca5a2b34b09ebebde83d045208f58a9a7476cd889aa0c31cc8eb`;
- `wayne_pivots_pooled_anatomy_ledger.csv`: `edad235505bce7ed652bd0dc145358c989464d9c588a242a348d63997e13e9e2`;
- generated Markdown decision: `d84268a9016996107fede130461a81cc9e101a1ec04d0f19f50aa78d9a8c7764`.

## Verdict

`APPROVE_FAIL_DAILY_PIVOT_GEOMETRY_STOP_BEFORE_BIAS`

The negative uniqueness decision is supported by the complete evidence. Wayne geometry is responsive to prior-range location, but it did not establish sufficient incremental value over the prior close or range midpoint. No arithmetic, census or authorization inconsistency was found.
