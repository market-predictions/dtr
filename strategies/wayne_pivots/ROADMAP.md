# Wayne Pivots Research Roadmap

Updated: 2026-07-27

## Phase A — Source and causal contract

Status: `IMPLEMENTED_PENDING_CI`

- traditional P/R1/S1/R2/S2 and M1–M4 formulas;
- New York 17:00 DST-safe pivot day;
- prior-period-only construction;
- BID/ASK ingestion and midpoint anatomy path;
- same-minute stop-first ambiguity policy;
- deterministic tests.

## Phase B — Daily pivot anatomy

Status: `IMPLEMENTED_PENDING_AUTHORITATIVE_RUN`

- six USD majors;
- 2015–2021 source isolation;
- bullish M2–P and bearish P–M3 first-touch events;
- target-before-invalidation outcomes;
- MFE, MAE and strict payoff proxy;
- fresh versus consumed structure classification.

## Phase C — Placebo geometry

Status: `IMPLEMENTED_PENDING_AUTHORITATIVE_RUN`

- prior close, range midpoint, quartiles;
- translated structures;
- four frozen synthetic H/L/C anchors;
- matched pair-day comparisons;
- pair/year breadth, block bootstrap, permutation and FDR;
- hard geometry authorization gate.

## Phase D — Direction attribution

Status: `BLOCKED_BY_GEOMETRY`

- book pivot-slope bias;
- opening-location diagnostics;
- frozen H4 21/55/200 and M15 5/8 technical state;
- macro-market proxy only after technical attribution;
- point-in-time fundamental bias last.

## Phase E — Bounded execution

Status: `BLOCKED_BY_BIAS`

Exactly six initial arms:

- E1 central-zone entry with T1/T2;
- E2 deep-zone entry with T1/T2;
- E3 M15 5/8 confirmation with T1/T2.

No partial exits, runners, breakeven or continuous threshold search.

## Phase F — Locked historical confirmation

Status: `BLOCKED`

- 2022–2023 locked strategy validation;
- 2024–2025 final historical confirmation;
- leave-one-pair and leave-one-year diagnostics;
- cost stress and familywise correction.

## Phase G — Replication and deployment

Status: `FUTURE_DATA_REQUIRED`

- unchanged cross-asset or prospective replication;
- future-pivot snapshot calibration as a separate study;
- Pine parity only after Python evidence;
- no deployment before prospective confirmation.
