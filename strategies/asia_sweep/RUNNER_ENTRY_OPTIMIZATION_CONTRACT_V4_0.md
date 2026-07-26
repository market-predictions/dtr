# Asian Sweep Runner and Entry Optimisation Contract v4.0

Date: 2026-07-26  
Branch: `agent/asia-sweep-runner-entry-optimization`

## Objective

Determine whether the validated Asian Sweep reversal fingerprint can be converted into positive and stable executable expectancy by:

1. allowing a partial position to run materially beyond the Asian midpoint; and
2. only after a runner policy is frozen, testing earlier causal entry landmarks between T0 and T5.

The programme must not jointly optimise entry, partial fraction, target, horizon and stop policy in one unrestricted grid.

## Scientific boundary

The prior decisions remain valid for their exact formulations:

- 100% liquidation at the Asian midpoint after T5 failed;
- 50% at the midpoint plus a runner to the opposite Asian boundary closed by 11:00 failed.

This programme is a new hypothesis. It does not reinterpret or overwrite those decisions.

## Data partitions

- runner development: 2015–2019 only;
- runner validation: 2020–2021, unopened until development passes;
- runner holdout 1: 2022–2023, unopened until validation passes;
- runner holdout 2: 2024–2025, unopened until holdout 1 passes;
- earlier-entry development starts only after a runner policy passes runner development.

## Fixed signal and entry for runner development

Runner development uses the exact audited `MKT_NEXT_OPEN` entries from execution run `30192167763`:

- exact frozen T5 model and threshold;
- entry strictly after T5;
- one trade per pair per Amsterdam date;
- actual Dukascopy BID/ASK M1 execution;
- original adverse stop at `0.20 × Asian range` beyond the sweep extreme;
- no pair, weekday, side, range-width or score-bucket filtering.

## Position structure

The initial position is split:

- 50% exits at the Asian midpoint as TP1;
- 50% is the runner.

The 50/50 split is fixed for this programme. Alternative partial fractions are outside scope.

## Runner target family

The runner target is defined from initial executable risk at entry. Candidate targets are:

- `2R`;
- `3R`;
- `4R`;
- `5R`;
- opposite Asian boundary as a structural control.

A target must lie beyond TP1 in the reversal direction. Otherwise the event/target combination is invalid.

## Runner time-exit family

Candidate Amsterdam time exits are:

- 12:00;
- 14:00;
- 16:00;
- 18:00.

No position is held overnight.

## Runner stop family

Two runner stop policies are allowed:

1. `ORIGINAL_STOP`: retain the original adverse stop after TP1;
2. `BREAK_EVEN_AFTER_TP1`: move the runner stop to executable entry price from the first active minute after the TP1 bar.

No trailing stop, BE buffer, partial trailing or structure-based discretionary adjustment is allowed.

## Candidate manifest

The frozen runner grid contains:

- 5 target definitions;
- 4 time exits;
- 2 stop policies;
- 40 total candidate policies.

The fixed 100%-midpoint and prior 11:00 opposite-boundary staged variants are reported as controls but cannot be selected.

## Intrabar and cost rules

- BID/ASK sides follow the audited execution simulator;
- spread is embedded;
- stop-first ordering applies when stop and target are both touched in one M1 bar;
- TP1 and runner target may both fill in the TP1 bar only when the stop is not touched;
- BE activates only from the next active minute after TP1;
- additional slippage stresses: 0.10 and 0.25 pip per market/stop execution;
- inactive quotes are never forward-filled.

## Nested development selection

Runner policy selection uses leave-one-year-out outer folds across 2015–2019.

For each outer year:

1. evaluate all 40 policies only on the other four years;
2. rank policies by 0.10-pip-stressed expectancy;
3. require positive expectancy on both pairs within the inner sample;
4. require at least three of four inner years positive;
5. break ties by lower maximum drawdown, then simpler target/horizon/stop order;
6. apply the selected policy unchanged to the held-out year.

Simplicity order:

- lower R target before higher R target;
- earlier time exit before later time exit;
- original stop before break-even.

The deployable development policy is the modal outer-fold selection. Ties are resolved by the same simplicity hierarchy. No pooled best-in-sample selection is permitted.

## Runner development gates

The out-of-fold selected policy must satisfy all:

- at least 150 trades pooled;
- at least 50 trades per pair;
- base expectancy greater than `+0.03R`;
- 0.10-pip-stressed expectancy greater than zero;
- both pairs positive;
- at least four of five outer years positive;
- median annual expectancy positive;
- maximum drawdown below `25R`;
- return/max-drawdown at least `1.50`;
- calendar-week bootstrap probability expectancy positive at least 95%;
- selected policy appears in at least three of five outer folds;
- no single winning trade contributes more than 20% of net R.

Failure stops the runner programme before 2020–2025.

## Earlier-entry programme boundary

Only if a runner policy passes development may earlier-entry research begin.

Allowed landmarks:

- T0: sweep minute close;
- T1: one completed minute after sweep;
- T2;
- T3;
- T5.

The entry programme must build causal landmark-specific probability or confirmation states. It may not use the validated T5 score at T0–T3.

Primary architecture:

- provisional position before T5 when early evidence is sufficient;
- add, retain, reduce or cancel based on later causal confirmation;
- total initial risk capped at 1R;
- the frozen runner policy remains unchanged during entry research.

A separate preregistration amendment must freeze the early-entry model, sizing ladder and cancellation rules before any entry P&L is inspected.

## Explicit prohibitions

- no retrospective EURUSD-only rescue;
- no weekday/year/side/range-width filtering;
- no alternative partial fractions in this programme;
- no target beyond the frozen manifest;
- no horizon beyond 18:00;
- no trailing or structural stop grid;
- no threshold recalibration;
- no access to 2020–2025 unless the preceding gate passes;
- no Pine, alerts, paper trading or deployment before full execution validation.

## Required outputs

- complete 40-policy ledger;
- outer-fold policy selections;
- out-of-fold trade ledger;
- target, horizon and stop-policy attribution;
- TP1 and runner-leg attribution;
- pair/year/weekday/side tables;
- drawdown, stress and block-bootstrap evidence;
- deterministic tests and independent reconstruction;
- decision, roadmap, changelog and handover.
