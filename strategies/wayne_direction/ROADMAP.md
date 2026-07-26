# Wayne Direction-First Research Roadmap

Updated: 2026-07-27

## Current state

`PHASE_A_CONTRACT_FROZEN_IMPLEMENTATION_ACTIVE`

## Phase A — Direction contract

Status: `ACTIVE`

- freeze D1 structural sequence;
- freeze H4 moving-average health;
- freeze macro, regime and seasonality roles;
- prohibit daily pivots from creating direction;
- define categorical long/short/abstain routing.

## Phase B — Structural trend engine

Status: `NEXT`

- build New York 17:00 D1 bars from qualified M1 BID/ASK data;
- confirm swings causally with right-side delay;
- implement double-bottom/top, BOS, retest, HL/LH and continuation confirmation;
- implement structural invalidation;
- test synthetic bull, bear, failed-break, ambiguous-shock and missing-data paths;
- publish a six-pair structural event ledger for 2015–2021.

## Phase C — H4 health engine

Status: `BLOCKED_BY_PHASE_B`

- build DST-safe H4 bars nested in each pivot day;
- calculate EMA21/55/200 and ATR20;
- classify expanding, stable, compressed and conflicted states;
- attach the last completed H4 state to each D1 structural event;
- quantify whether healthy divergence improves continuation and monthly reach.

## Phase D — Monthly location and reach

Status: `BLOCKED_BY_PHASE_B`

- calculate prior-month traditional levels and M1–M4;
- classify month-open location and first-five-day zone touch;
- evaluate M4/R2 reach for bullish direction and M1/S2 for bearish direction;
- use month-end and structural invalidation as causal stopping conditions;
- record R1/S1 as path checkpoints, not optimized targets.

## Phase E — Seasonality

Status: `PLANNED`

- expanding-window month-of-year prior;
- week-of-month and turn-of-month states;
- no full-sample seasonality lookup;
- minimum-history and stability gates;
- seasonality supports or blocks but does not override structure.

## Phase F — Macro and regime data qualification

Status: `DATA_CONTRACT_REQUIRED`

- identify point-in-time rate, inflation, growth and real-yield sources;
- freeze release timestamps and revision treatment;
- define pairwise currency differential;
- freeze volatility, efficiency, risk and policy-regime states;
- reject any series that cannot be reconstructed as known at the decision timestamp.

## Phase G — Direction triage atlas

Status: `BLOCKED`

- structural direction mandatory;
- macro must not oppose;
- regime must permit trend-following;
- seasonality must be supportive or neutral;
- H4 health must be expanding or stable;
- otherwise abstain;
- no weighted-score optimization in the first atlas.

## Phase H — Conditional reach validation

Status: `BLOCKED`

- test monthly M4/R2 and M1/S2 reach conditional on frozen direction states;
- report absolute reach rates, timing, MFE/MAE, pair/year breadth and concentration;
- use block bootstrap, permutation and FDR where families are compared;
- preserve 2022–2025 for later confirmation.

## Phase I — Bounded execution

Status: `NOT_AUTHORIZED`

Only after direction and reach pass:

- freeze a small number of entry triggers;
- apply identical triggers to Wayne monthly zones and generic monthly anchors;
- model BID/ASK fills, costs and same-bar ambiguity;
- no partial exits, runners or continuous search in the first execution study.

## Phase J — Historical confirmation and deployment

Status: `FUTURE`

- 2022–2023 locked validation;
- 2024–2025 final historical confirmation;
- prospective or cross-asset replication;
- Pine parity only after Python evidence;
- no sizing or deployment before prospective confirmation.

## Archived branch

PR #63 is retained as a negative daily-pivot geometry study. It is not an active roadmap dependency and cannot block or authorize this direction-first programme.
