# DTR Optimization Lab Status

## Current work package

`DTR-NQ-WP-20260722-07 — Selection robustness and explicit execution contract`

Status: **exact historical reconstruction classified; architecture refactor and inference primitives implemented; CI validation active**

Decision state: `EXACT_RECONSTRUCTION_BLOCKED_CURRENT_CAUSAL_UNIVERSE_IN_PROGRESS`

## Accepted causal benchmark

`DTR_PY_NQ_CANDIDATE_0_1_CAUSAL_GAP`

- 495 trades;
- 0.173746993R expectancy;
- 86.004761R net;
- PF 1.366383;
- maximum drawdown 14.107858R;
- return/DD 6.096231.

This benchmark is an exact regression gate and may not be retuned.

## Original 904 audit

The six grid definitions, pack sizes, optimizer score, runner, final candidate and narrative pack order are preserved. The original pack leaderboards, selected winner per pack, stage-transition base configurations and candidate return streams are not preserved in Git history.

Decision: `EXACT_RECONSTRUCTION_BLOCKED`.

A newly frozen experiment is permitted only under the separate label `CURRENT_CODE_CAUSAL_904_UNIVERSE`; it may not be represented as reconstructing the original staged selection path.

## Architecture progress

- canonical package import no longer mutates `engine.py` symbols;
- optimizer imports the integrity-safe orchestration layer directly;
- optimizer gap policy is explicit and defaults to `liquidate_unsafe`;
- every new leaderboard row records the gap policy;
- import-order and direct-entry contract tests are committed;
- obsolete publisher workflow and staged archives were removed.

## Inference progress

Committed deterministic primitives for:

- session-date × session and calendar-date return alignment;
- zero return assignment when a candidate takes no trade;
- candidate return-stream SHA-256 hashes;
- exact duplicate stream detection;
- joint market-date block max-t testing;
- reality-check-style best-mean testing;
- bootstrap winner reselection frequencies and effective candidate count.

Synthetic fixtures are committed; clean-head CI is pending.

## Existing unresolved gates

- timestamp semantics: `UNRESOLVED`;
- continuous-contract methodology: `UNRESOLVED`;
- original 904-search familywise adjustment: `UNRESOLVED_EXACT_RECONSTRUCTION_BLOCKED`;
- current-code causal universe inference: `IN_PROGRESS`;
- fresh qualified OOS: `NOT_RUN_PREREGISTERED`;
- Python/Pine parity: `NOT_RUN`.

## Scope restrictions

No fresh 2026 performance inspection, strategy retuning, new candidate family, module combination, Pine port, sizing recommendation, or deployment is authorized.
