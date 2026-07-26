# Asian Sweep Staged Reference Correction Amendment v6.5

Date frozen: 2026-07-26  
Applies to v6.0–v6.4.

## 1. Withdrawn staged result

The first source-backed staged feasibility artifact from Actions run `30201189610` is withdrawn before any protected validation.

Independent audit confirmed that the four staged policies were simulated with the intended causal continuation-cancel behavior. However, the implementation also applied continuation cancellation to the static comparator policies:

- `T0_STATIC_025`;
- `T1_STATIC_025`;
- `T0_STATIC_100`;
- unconditional static diagnostics.

The frozen contracts define these as static **no add/no cancel** references. Consequently, the staged-versus-static improvement predicates were not evaluated against the required baseline.

The withdrawn artifact produced a failure, but it is not authoritative.

## 2. Correction

- continuation cancellation applies only to `T0_QUARTERS`, `T1_QUARTERS`, `T0_CONCENTRATED` and `T0_LATE_WEIGHTED`;
- all static references hold their initial tranche until stop, midpoint target or 10:00 Amsterdam;
- initial eligibility, quote sides, slippage, stop, target, event selection, tranche sizing and all staged-policy actions remain unchanged;
- no thresholds, gates or policy alternatives are modified.

## 3. Reproduction

The corrected staged gate will reuse:

- immutable early-entry ledger from run `30197859712`;
- corrected triage predictions from run `30201189610`;
- qualified 2015–2019 BID/ASK source from run `30111481052`.

Only the staged simulation and its independent reconciliation are rerun.

## 4. Extended aggregate recovery

The same recovery workflow may aggregate the twenty already-completed extended-target candidate artifacts from run `30201189610`. The original aggregate job failed operationally because it installed the base environment while importing the scikit-learn model module. No candidate fit failed and no candidate is rerun.

## 5. Boundaries

- 2020–2025 remains unopened;
- withdrawn staged metrics may not be cited as programme evidence;
- no staged or extended gate is relaxed;
- no TP1 management P&L opens unless the recovered extended decision passes;
- no Pine, alerts, paper trading or deployment is authorized.
