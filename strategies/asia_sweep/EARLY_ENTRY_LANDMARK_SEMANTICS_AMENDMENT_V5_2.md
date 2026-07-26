# Asian Sweep Early-Entry Landmark Semantics Amendment v5.2

Date: 2026-07-26  
Branch: `agent/asia-sweep-early-entry-research`

## Status

`FROZEN_BEFORE_LANDMARK_LEDGER_OR_MODEL_OUTCOME_INSPECTION`

## Reason

The validated fingerprint programme calls its confirmation snapshot `T5`, but the implementation constructs a five-bar inclusive path beginning with the sweep bar. For a sweep at minute `m`, the frozen validated snapshot ends at minute `m+4`.

The early-entry preregistration used the phrase “k completed M1 bars after the sweep bar,” which would otherwise imply a different clock convention. This amendment removes that ambiguity before landmark data is generated.

## Binding landmark definitions

- `T0`: close of the sweep bar at minute `m`;
- `T1`: close of the first complete active M1 bar after the sweep, normally `m+1`;
- `T2`: close of the second complete active M1 bar after the sweep, normally `m+2`;
- `T3`: close of the third complete active M1 bar after the sweep, normally `m+3`;
- `LEGACY_T5`: the exact validated five-bar inclusive snapshot over `[m, m+5 minutes)`, normally ending at `m+4`.

The programme will not silently redefine or refit the validated benchmark.

## Entry timing

For every landmark, the executable geometry snapshot uses the first active BID/ASK minute open strictly after that landmark bar closes.

Thus, under continuous quotes:

- T0 enters at `m+1` open;
- T1 enters at `m+2` open;
- T2 enters at `m+3` open;
- T3 enters at `m+4` open;
- `LEGACY_T5` enters at `m+5` open, matching the audited market-next-open execution programme.

If the immediately following minute is inactive, the first later active minute is used and the delay is recorded. No inactive quote is forward-filled.

## Feature windows

- T0 features include the sweep bar and all previously frozen context available by its close.
- T1–T3 incremental features include the sweep bar plus the completed post-sweep bars through the named landmark.
- `LEGACY_T5` features and score are copied/reproduced from the validated pipeline without alteration.
- No feature may use the bar on which the next-open entry occurs.

## Population and label timing

An event is excluded at a landmark when the midpoint or adverse barrier was reached on or before that landmark close. The landmark label begins strictly with the next active bar after the landmark.

Same-bar target/barrier ambiguity after the landmark remains conservatively ambiguous and is excluded from the primary supervised target, while being reported separately.

## Reporting

All outputs must include:

- landmark close timestamp;
- first executable entry timestamp;
- count of included bars;
- elapsed minutes from sweep;
- active-minute delay to entry;
- explicit `LEGACY_T5` naming in reports and code.

The user-facing report may explain that `LEGACY_T5` is the previously validated five-bar confirmation snapshot; it must not describe it as five full minutes after the sweep bar.
