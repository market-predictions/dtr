# Wayne Direction-First Research Roadmap

Updated: 2026-07-27

## Current state

`PHASE_D_STAGED_TECHNICAL_SEQUENCE_REQUIRES_FREEZE`

## Phase A — Direction contract

Status: `COMPLETE`

- macro, regime, seasonality and structure are separate direction layers;
- daily pivots cannot create direction;
- D1 structure is strategic context;
- H4 structure is current technical transition;
- H4 EMA21/55/200 grades health;
- monthly pivots define location and reach.

## Phase B — D1 strategic structure

Status: `COMPLETE_REFERENCE_FAILED_SAMPLE_GATE`

- causal double-bottom/top → BOS → retest → HL/LH → continuation engine;
- full pre-retest impulse reference;
- six pairs, 2015–2021;
- corrected result: 79 complete transitions;
- 69 of 79 had aligned healthy H4 averages at confirmation;
- D1 state is broad but slow and persistent;
- retain unchanged as strategic regime context;
- do not loosen thresholds to manufacture sample.

Primary record: `D1_STRUCTURE_CENSUS_CORRECTION_V0_2_1.md`.

## Phase C — H4 current structure and health

Status: `COMPLETE_TRANSITION_GATE_PASS_MONTH_OPEN_GATE_FAIL`

- 475 complete H4 transitions;
- all six pairs exceed 40 events;
- transition-count gate passed;
- only 176 of 475 had aligned healthy H4 averages at confirmation;
- zero of 486 monthly-zone months were simultaneously aligned structure plus healthy MAs at the exact month open;
- simultaneous conjunction is rejected;
- H4 thresholds remain frozen.

Primary record: `H4_STRUCTURE_SENSITIVITY_DECISION_V0_4.md`.

## Phase D — Staged technical sequence

Status: `NEXT_VALID_PHASE`

Test an ordered setup rather than simultaneous filters:

1. month opens in zone or first touches the zone during the first five pivot days;
2. H4 structure confirms in the zone direction;
3. H4 EMA21/55/200 subsequently becomes stable or expanding;
4. monthly reach is measured from the completed confirmation timestamp.

Rules:

- first five pivot days are primary;
- ten pivot days may be a labeled development sensitivity only;
- no H4 threshold tuning;
- no target-grid search;
- compare against no-direction and opposite-direction month controls;
- report pair/year breadth and concentration;
- treat pre-confirmation target touches as ineligible, not successes.

## Phase E — Seasonality

Status: `BLOCKED_BY_STAGED_TECHNICAL_SAMPLE`

- expanding-window month-of-year prior;
- week-of-month and turn-of-month states;
- prior years only;
- supportive, neutral or opposing relationship;
- no override of missing technical confirmation.

## Phase F — Macro and regime data qualification

Status: `DATA_CONTRACT_REQUIRED`

- point-in-time rate and policy expectations;
- inflation and growth-surprise differentials;
- real-yield or rate-market differential;
- volatility, efficiency and risk regime;
- explicit release timestamps and revision treatment;
- reject any series that cannot be reconstructed as known contemporaneously.

## Phase G — Direction triage atlas

Status: `BLOCKED`

Candidate permission stack:

- D1 strategic context aligned or explicitly neutral;
- macro must not oppose;
- regime must permit trend-following;
- seasonality supportive or neutral;
- staged H4 structural and MA confirmation complete;
- otherwise abstain.

No weighted-score optimization in the first atlas.

## Phase H — Conditional reach validation

Status: `BLOCKED`

- M4/R2 bullish and M1/S2 bearish reach;
- start clock at completed staged confirmation;
- matched controls;
- pair/year breadth, concentration, block bootstrap and FDR;
- preserve 2022–2025 for locked confirmation.

## Phase I — Bounded execution

Status: `NOT_AUTHORIZED`

Only after direction and reach pass:

- freeze a small entry set;
- BID/ASK fills and transaction costs;
- identical execution across monthly-zone and generic-anchor controls;
- no partial exits, runners or continuous threshold search.

## Phase J — Historical confirmation and deployment

Status: `FUTURE`

- 2022–2023 locked validation;
- 2024–2025 final historical confirmation;
- prospective or cross-asset replication;
- Pine parity only after Python evidence;
- no sizing or deployment before prospective confirmation.

## Archived work

PR #63 remains the bounded negative daily-pivot geometry study. It is not an active dependency and cannot block or authorize the direction-first programme.
