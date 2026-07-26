# Asian Sweep Sequential Triage and Staged Entry — Preregistration v6.0

Date: 2026-07-26
State: FROZEN_BEFORE_OUTCOMES
Development: EURUSD and GBPUSD, 2015–2019
Protected: 2020–2025

## Decision problem

The failed one-shot T0–T3 frontier showed that price quality is best before reversal certainty is available. This programme tests whether a sequential state/action architecture can preserve early price while limiting losses when continuation evidence appears.

## Programme sequence

### Phase A — state triage
At T0, T1, T2 and T3 estimate mutually exclusive states:
- REVERSAL: midpoint reached before the adverse barrier by 10:00 Amsterdam;
- CONTINUATION: adverse barrier reached before a 0.25-range reaction;
- ABSTAIN: all remaining valid events, including stalled, late, ambiguous or insufficiently resolved cases.

Primary implementation: multinomial elastic-net and histogram gradient boosting. Secondary diagnostic: one-vs-rest reversal and continuation models. All predictions are leave-one-year-out, with Amsterdam-week grouped inner tuning and fold-local calibration.

Primary triage gates:
- at least 400 eligible event-landmark rows and 150 per pair;
- macro one-vs-rest PR-AUC relative lift >= 35%;
- reversal top-quintile precision >= 40% and >= 1.60x base;
- continuation top-quintile precision >= 45% and >= 1.60x base;
- abstention coverage between 25% and 75% under the frozen decision thresholds;
- actionable decisions positive in both pairs and at least four of five years;
- no class/pair/day concentration above 70%;
- probability calibration better than class-frequency baselines.

Decision thresholds are selected inside each training fold to maximize balanced utility subject to minimum precision: reversal >= 0.40, continuation >= 0.45; otherwise ABSTAIN.

### Phase B — staged action policy
Opened only if Phase A passes.

Frozen action family:
- T0 provisional risk: 0%, 0.25R or 0.50R;
- T1/T2/T3 actions: ADD 0.25R, HOLD, REDUCE 50%, EXIT, or NO ACTION;
- maximum aggregate initial risk: 1.00R;
- no averaging beyond the frozen adverse stop;
- continuation decision forces EXIT and blocks further adds;
- abstention allows HOLD/REDUCE but no new add;
- reversal decision may authorize an add if total risk remains <=1R.

Only six predeclared policies will be evaluated: conservative, balanced and aggressive variants, each with and without T0 provisional risk. Selection uses nested weekly grouped out-of-fold simulation. No pair/day/direction rescue.

Staged-policy pass gates:
- stressed expectancy >0R;
- return/max-drawdown >=1.5;
- positive net R in both pairs and at least four of five years;
- no single pair/year contributes >45% of net R;
- maximum drawdown <=12R;
- at least 250 completed trades;
- survives +0.10 pip and +0.25 pip per execution-leg stress.

### Phase C — extended-reversal model
Independent of Phase B and may proceed after Phase A labels are stable.

Frozen targets from the first executable entry after each landmark:
- reaches 2R before stop by 11:00;
- reaches 3R before stop by 12:00;
- reaches 4R before stop by 14:00;
- reaches the opposite Asian boundary before stop by 11:00;
- reaches the nearest opposing external-liquidity level before stop by 14:00.

Each target receives separate out-of-fold models; midpoint success is not reused as the runner target.

Extended-model gates per target:
- at least 75 positive cases and 400 total rows;
- PR-AUC relative lift >=50%;
- top-decile precision >=2.0x base;
- positive lift in both pairs and at least four years;
- median executable expected-value proxy >0 after +0.10 pip stress;
- no concentration above70%.

### Phase D — position structures
Opened only for an extended target that passes Phase C and on identical frozen entries:
- TP1_50_RUNNER_50;
- TP1_25_RUNNER_75;
- NO_TP1_FULL_RUNNER.

TP1 is the Asian midpoint. Runner exit is the passed target's frozen horizon/structural objective. Selection requires nested out-of-fold P&L and familywise correction across the three structures.

## Causality and ambiguity

- Landmark features use only bars completed through that landmark.
- Entries use the next active BID/ASK open.
- Any event resolved before a landmark is excluded from that landmark.
- Same-minute target/stop ambiguity is stop-first in P&L and excluded from primary label metrics.
- Cross-pair features use only information timestamped at or before the current landmark.
- Append-future invariance is mandatory.

## Stop rules

- If Phase A fails, staged-entry P&L is not opened.
- If all Phase C targets fail, the 50%/25%/0% structures are not tested.
- No post-hoc threshold, pair, weekday, direction, range-width or session rescue.
- 2020–2025 remains unopened until a complete development programme passes.
