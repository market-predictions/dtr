# Asian Sweep Triage, Staged Entry and Extended Reversal Programme — Preregistration v6.0

Date frozen: 2026-07-26  
Branch: `agent/asia-sweep-triage-staged-extended`  
Parent evidence: `EARLY_ENTRY_INFORMATION_FRONTIER_DECISION.md`

## 1. Strategic question

The rejected one-shot T0–T3 architecture showed a structural frontier: early prices preserve payoff but reversal information is weak; later confirmation improves classification after much of the midpoint move has already occurred.

This programme tests three distinct hypotheses in sequence:

1. **Selective triage** — can the sweep be classified as reversal, continuation or no-action early enough to improve decisions?
2. **Staged entry** — can small provisional risk plus causal add/cancel decisions combine early price with later information?
3. **Extended reversal** — can target-specific models identify runners beyond the midpoint strongly enough to justify 50%, 25% or 0% TP1?

A later phase may not open unless the preceding phase passes its frozen gate.

## 2. Data partitions

- `2015–2019`: development only; prior work has already inspected these years.
- `2020–2021`: first protected validation.
- `2022–2023`: second protected validation.
- `2024–2025`: final untouched holdout.
- `2026`: monitoring only; never used for model or policy selection.

No protected partition may be opened before the complete code, thresholds, metrics and stop rules for that phase are committed.

## 3. Shared event geometry

The programme inherits without modification:

- Europe/Amsterdam session definitions;
- first qualifying sweep per side/day;
- Asian range and liquidity-topology features;
- T0, T1, T2, T3 and exact `LEGACY_T5` landmark semantics;
- actual next-active BID/ASK executable entry prices;
- original midpoint and adverse-barrier first-passage rules;
- exclusion and reporting of same-minute/two-sided ambiguity;
- no future or T5 information in T0–T3 features.

## 4. Phase A — selective reversal/continuation/abstention triage

### 4.1 Outcome taxonomy

Outcomes reuse the frozen fingerprint labels:

- `REVERSAL`: `MIDPOINT_SUCCESS_09_10`;
- `CONTINUATION`: `IMMEDIATE_CONTINUATION` or `FALSE_REVERSAL`;
- `UNRESOLVED`: `STALLED_REACTION` or `LATE_MIDPOINT`;
- `AMBIGUOUS`: excluded from fitting and primary scoring, but counted and reported.

`ABSTAIN` is a decision action, not a hindsight outcome.

### 4.2 Hierarchical model

At each landmark T0–T3, fit two separate models:

1. resolvability: `RESOLVED` versus `UNRESOLVED`;
2. direction conditional on resolved: `REVERSAL` versus `CONTINUATION`.

Final probabilities are:

- `P(reversal) = P(resolved) × P(reversal | resolved)`;
- `P(continuation) = P(resolved) × P(continuation | resolved)`;
- `P(unresolved) = 1 − P(resolved)`.

Model families:

- elastic-net logistic classification;
- histogram gradient boosting.

Evaluation remains leave-one-year-out with Amsterdam-week grouped inner folds, fold-local preprocessing and fold-local calibration.

### 4.3 Selective action thresholds

Thresholds are selected only inside each outer training fold from the frozen finite grid:

- reversal threshold: `{0.55, 0.60, 0.65, 0.70}`;
- continuation threshold: `{0.70, 0.75, 0.80, 0.85}`;
- maximum unresolved probability: `{0.20, 0.30, 0.40}`;
- minimum reversal/continuation probability margin: `{0.15, 0.25, 0.35}`.

Lexicographic inner-fold selection:

1. continuation precision at least `0.80`;
2. reversal precision at least `0.50`;
3. total action coverage at least `0.20`;
4. maximize utility per eligible event where correct = `+1`, wrong = `−1.5`, abstain = `0`;
5. maximize coverage;
6. choose stricter thresholds on ties.

If no threshold set satisfies all three minimums, retain the set with highest utility subject to continuation precision >=0.80; otherwise retain the globally highest-utility set and mark the fold deficient.

### 4.4 Phase-A decisions

Possible decisions:

- `PASS_FULL_TRIAGE`: both reversal and continuation satisfy the full gate;
- `PASS_CONTINUATION_VETO_ONLY`: continuation satisfies its gate but reversal does not;
- `FAIL_TRIAGE_STOP`: continuation also fails.

Full development gate:

- at least `1,500` resolved events pooled and `600` per pair;
- continuation precision >=`0.80` with continuation coverage >=`0.25`;
- reversal precision >=`0.50` with at least `100` reversal calls;
- selective accuracy >=`0.75`;
- utility per eligible event >`0.05`;
- positive utility for both pairs and at least four of five years;
- multiclass log loss and Brier score improve over fold-local class-frequency baselines;
- no single pair, side or weekday contributes >`70%` of correct reversal calls.

Continuation-veto-only gate:

- continuation precision >=`0.85`;
- continuation coverage >=`0.25`;
- positive utility for both pairs and at least four of five years;
- continuation false-veto rate against true reversals <=`0.12`;
- model calibration beats the constant baseline.

Only a frozen development pass may open 2020–2021.

## 5. Phase B — true staged provisional entry

Phase B is authorized by either `PASS_FULL_TRIAGE` or `PASS_CONTINUATION_VETO_ONLY`.

### 5.1 Architecture

- total trade risk is capped at `1.00R` relative to the frozen adverse stop;
- no averaging down and no widening the stop;
- every tranche uses the contemporaneous next-active BID/ASK price;
- high-confidence continuation always vetoes a new reversal tranche and liquidates any open provisional reversal exposure at the next active quote;
- unresolved/abstain never adds risk.

Frozen policy family:

1. `S0_T0_025`: enter `0.25R` risk at T0 if not continuation-vetoed;
2. `S1_T1_025`: first provisional `0.25R` at T1 if not continuation-vetoed;
3. add `0.25R` at T1/T2/T3 when reversal action is active;
4. concentrated add variant: `0.25R` provisional then one `0.50R` add at the first T2/T3 reversal action;
5. maximum total risk before T3 is `0.75R`; final `0.25R` is permitted only on a T3 reversal action;
6. no trade may be opened after T3.

Phase-B exit is deliberately fixed:

- 100% at the Asian midpoint;
- frozen adverse stop;
- forced close at 10:00 Amsterdam;
- no break-even rule, runner, trailing stop or later close.

This isolates whether staged information entry itself adds value.

### 5.2 Policy selection and gate

Policy selection uses grouped nested evaluation. A staged policy passes only if:

- at least `300` trades and `120` per pair;
- positive pooled expectancy after spread and `0.10` pip adverse slippage per entry and exit;
- positive expectancy in both pairs and at least four of five development years;
- return/max-drawdown >=`1.50`;
- max drawdown <=`20R`;
- no pair, year, side or weekday supplies >`65%` of net R;
- staged policy improves expectancy by at least `0.05R` and return/drawdown by at least `25%` versus the same first-entry timing without later add/cancel logic.

If Phase B fails, Phase C may still perform target discovery as a non-execution research study, but no management P&L or deployment is authorized.

## 6. Phase C — target-specific extended-reversal models

### 6.1 Target labels

Labels are computed from actual BID/ASK paths after the selected staged decision snapshot:

- `EXTENDED_1_5R`: reaches `1.5R` before stop by 13:00 Amsterdam;
- `EXTENDED_2R`: reaches `2.0R` before stop by 13:00;
- `EXTENDED_3R`: reaches `3.0R` before stop by 16:00;
- `OPPOSITE_ASIAN_BOUNDARY`: reaches the opposite Asian boundary before stop by 13:00;
- `LATE_TREND_HOLD`: reaches at least `2R` MFE and closes at or beyond `1R` at 16:00.

Each target gets an independent calibrated model. Midpoint success may be a feature only when it is causally known before the runner decision; it may not be used at initial entry.

### 6.2 Position structures

Only after at least one extended target passes its predictive gate, compare:

- `TP1_50_RUNNER_50`;
- `TP1_25_RUNNER_75`;
- `NO_TP1_FULL_RUNNER`.

For TP1 variants, TP1 is the Asian midpoint. Runner stop variants are limited to:

- original stop retained;
- stop to break-even only after TP1 is filled.

Runner objectives are limited to the target whose model passed. No broad target/time grid is permitted.

### 6.3 Predictive gate

For an extended target:

- at least `150` positives pooled and `50` per pair;
- PR-AUC relative lift >=`0.50`;
- top-quintile lift >=`1.75×`;
- bottom/base ratio <`0.60`;
- both pairs and at least four of five years show positive top-quintile lift;
- Brier score beats the constant baseline;
- top-quintile stressed expected-value proxy is positive for that target.

### 6.4 Management gate

A payoff structure passes only if:

- positive nested out-of-fold expectancy after spread and `0.10` pip slippage;
- positive both-pair expectancy and at least four positive development years;
- return/max-drawdown >=`2.00`;
- no material deterioration under `0.25` pip slippage stress;
- superiority over the 50% TP1 reference is at least `0.05R` expectancy or `25%` return/drawdown;
- familywise uncertainty control covers all authorized position structures and BE variants.

## 7. Protected validation sequence

After development selection is completely frozen:

1. run 2020–2021 once;
2. proceed to 2022–2023 only if the relevant phase retains positive expectancy/utility, both-pair direction and no catastrophic calibration failure;
3. proceed to 2024–2025 only after a formal second-validation pass;
4. no post-validation threshold, model, policy or target changes are allowed.

## 8. Stop rules

Stop the relevant path immediately when:

- causal or future-append tests fail;
- protected data is accessed before a frozen contract;
- continuation triage fails its veto-only gate;
- staged entry fails development or first validation;
- no extended target passes prediction before management P&L;
- results depend on a pair/day/side rescue not preregistered here;
- any proposed change would reuse protected outcomes for tuning.

## 9. Operational requirements

- deterministic seeds and stable sorting;
- visible artifact digests and source-run identifiers;
- synthetic tests for T0–T3 causality, action thresholds, tranche accounting, quote side, stop handling, same-minute ambiguity and future-append invariance;
- independent metric and ledger reconciliation before a decision is recorded;
- no Pine, alerts, paper trading or deployment until final holdout passes.
