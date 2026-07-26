# Asian Sweep Triage Failure and Independent Feasibility Amendment v6.1

Date frozen: 2026-07-26  
Applies to: `TRIAGE_STAGED_EXTENDED_PROGRAMME_PREREGISTRATION_V6_0.md`

## 1. Phase-A development status

The hierarchical triage frontier was completed on 2015–2019 only. No protected year was opened.

No T0–T3 candidate passed `PASS_FULL_TRIAGE` or `PASS_CONTINUATION_VETO_ONLY`.

The strongest HGB findings were:

- T0: continuation precision `73.30%`, coverage `22.87%`, false-veto rate `16.37%`;
- T1: continuation precision `76.11%`, coverage `19.77%`, false-veto rate `14.08%`;
- T2: continuation precision `77.89%`, coverage `17.66%`, false-veto rate `9.12%`;
- T3: continuation precision `80.25%`, coverage `22.02%`, false-veto rate `12.17%`.

The models produced no reversal actions under the frozen selective threshold procedure. Therefore:

`FAIL_TRIAGE_STOP_BEFORE_PROTECTED_VALIDATION`

A direct continuation-versus-rest challenger was also explored on development only. It could reach approximately `88.6%` continuation precision at T3, but at only `7.7%` coverage. At approximately `25%` coverage, precision remained below `80%`. This is retained as a rare warning signal, not a broad triage pass.

No Phase-A gate is relaxed and 2020–2025 remains sealed.

## 2. Independent development-only studies

The user requested research into all three next paths. Because Phase A failed, the following are authorized only as **new development hypotheses**. They may not open protected data or claim validation without a new frozen pass decision.

### 2.1 Staged-entry feasibility

Purpose: determine whether the information-payoff frontier can be improved mechanically by risking little early and adding only when the existing out-of-fold reversal ranking strengthens.

This is not authorized by the failed triage gate and therefore remains development-only.

The staged policies use the previously generated HGB leave-one-year-out probabilities. No model is refit on protected data.

Frozen probability conditions:

- T0 provisional eligibility: `p_continuation < 0.72` and `p_unresolved < 0.30`;
- T1 reversal add: `p_reversal >= 0.19`, `p_continuation < 0.72`, `p_unresolved < 0.35`;
- T2 reversal add: `p_reversal >= 0.21`, same continuation/unresolved limits;
- T3 reversal add: `p_reversal >= 0.23`, same continuation/unresolved limits;
- T1/T2 continuation cancel: `p_continuation >= 0.75` and `p_continuation - p_reversal >= 0.40`;
- T3 continuation cancel: `p_continuation >= 0.80` and the same margin.

The add thresholds approximate the development score-distribution 80th percentiles and were chosen without target-outcome optimization.

Frozen policy family:

1. `T0_QUARTERS`: `0.25R` at T0; add `0.25R` at each qualifying T1/T2/T3;
2. `T1_QUARTERS`: `0.25R` at T1; add `0.25R` at qualifying T2/T3; maximum `0.75R`;
3. `T0_CONCENTRATED`: `0.25R` at T0; add `0.50R` at the first qualifying T2/T3 and a final `0.25R` at T3 if still qualified;
4. `T0_LATE_WEIGHTED`: `0.25R` at T0; add `0.375R` at qualifying T2 and `0.375R` at qualifying T3;
5. `T0_STATIC_025`: reference with `0.25R` at T0 and no add/cancel;
6. `T0_STATIC_100`: reference with `1.00R` at T0 and no add/cancel.

All staged variants:

- use the frozen adverse stop and Asian midpoint target;
- exit at 10:00 Amsterdam if neither is reached;
- use actual next-active BID/ASK quotes;
- apply `0.10` pip adverse slippage to every entry and market exit;
- use stop-first treatment for same-minute stop/target ambiguity;
- never widen the stop or exceed `1.00R` total allocated risk;
- liquidate all open tranches at the next active quote when a continuation-cancel condition occurs.

Development feasibility gate remains the original Phase-B gate. Failure closes staged entry without protected validation.

### 2.2 Independent extended-target discovery

Purpose: determine whether early causal features predict large reversal moves more directly than midpoint success.

This study may proceed even though staged entry is not authorized, because it performs target discovery only. It may not compare TP1 fractions, break-even rules or realized management policies unless a target passes.

Entry landmarks:

- T0 next-active BID/ASK entry;
- T1 next-active BID/ASK entry.

Frozen labels:

- `EXTENDED_1_5R_1300`: reaches `1.5R` before stop by 13:00 Amsterdam;
- `EXTENDED_2R_1300`: reaches `2.0R` before stop by 13:00;
- `EXTENDED_3R_1600`: reaches `3.0R` before stop by 16:00;
- `OPPOSITE_ASIAN_BOUNDARY_1300`: reaches the opposite Asian boundary before stop by 13:00;
- `LATE_TREND_HOLD_1600`: reaches at least `2R` MFE and closes at or beyond `1R` at 16:00 before a prior stop.

Target labels use actual executable BID/ASK paths and stop-first ambiguity handling. Events with invalid geometry or insufficient active path are excluded and counted.

Model families, grouped nested evaluation and predictive gates remain those in v6.0.

Possible decisions:

- `PASS_EXTENDED_TARGET_DISCOVERY_FREEZE_TARGET`;
- `FAIL_EXTENDED_TARGET_DISCOVERY_STOP_BEFORE_TP1_PNL`.

Only a predictive pass can open the frozen position structures:

- `TP1_50_RUNNER_50`;
- `TP1_25_RUNNER_75`;
- `NO_TP1_FULL_RUNNER`.

## 3. Integrity boundary

- all work in this amendment remains 2015–2019 development;
- no threshold or policy may be altered after source-backed outcomes are generated;
- no result from this amendment may be described as validated;
- 2020–2025 remains unopened;
- no Pine, alerts, paper trading or deployment is authorized.
