# DTR Optimization Lab Status

## Current work package

`DTR-NQ-WP-20260722-07 — Selection robustness and explicit execution contract`

Status: **claimed; design complete; candidate-universe audit starting**

Decision state: `HISTORICAL_SELECTION_EVIDENCE_UNDER_REVIEW`

## Accepted causal benchmark

`DTR_PY_NQ_CANDIDATE_0_1_CAUSAL_GAP`

- 495 trades;
- 0.173746993R expectancy;
- 86.004761R net;
- PF 1.366383;
- maximum drawdown 14.107858R;
- return/DD 6.096231.

This benchmark is an exact regression gate and may not be retuned.

## Work package objectives

- reconstruct the original staged 904-candidate universe and selection chronology where evidence permits;
- build aligned candidate return streams on `session_date × session` and calendar-date units;
- apply joint multiple-testing-aware inference with fixed seeds;
- measure bootstrap reselection, winner stability, duplicates, and parameter plateaus;
- remove canonical import-time monkey-patching and require explicit causal execution policy;
- preserve all prior signal and trade outcomes.

## Existing unresolved gates

- timestamp semantics: `UNRESOLVED`;
- continuous-contract methodology: `UNRESOLVED`;
- 904-search familywise adjustment: active work package;
- fresh qualified OOS: `NOT_RUN_PREREGISTERED`;
- Python/Pine parity: `NOT_RUN`.

## Closed or superseded work

- PR #6 merged the causal baseline reset as commit `18e48b9f15d68541da8c1bcea970a7894bf99dbf`;
- PR #5 was closed without merge as superseded;
- continuation remains `HOLD_FOR_FRESH_DATA`;
- IFVG, CISD, and entry-routing decisions remain `REJECT_NO_INCREMENTAL_VALUE`.

## Scope restrictions

No fresh 2026 performance inspection, strategy retuning, new candidate family, module combination, Pine port, sizing recommendation, or deployment is authorized.
