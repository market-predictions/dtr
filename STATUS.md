# DTR Optimization Lab Status

## Current work package

`DTR-NQ-WP-20260722-06 — Baseline validity reset`

Status: **complete; source and compact evidence published; final GitHub CI and merge pending**

Decision: `CONTINUE_RESEARCH_DO_NOT_DEPLOY`

## Corrected benchmark

`DTR_PY_NQ_CANDIDATE_0_1_CAUSAL_GAP`

- 495 trades;
- 0.173746993R expectancy;
- 86.004761R net;
- PF 1.366383;
- maximum drawdown 14.107858R;
- return/DD 6.096231;
- four causal gap liquidations.

## Historical references

- Observe-only: 504 trades and 84.164359R.
- Suspended retrospective rejection: 491 trades and 88.495783R.
- Historical rolling walk-forward: 289 trades and 0.151217R expectancy.

## Validity gates

- timestamp semantics: `UNRESOLVED`;
- continuous-contract methodology: `UNRESOLVED`;
- 904-search familywise adjustment: `UNRESOLVED`;
- fresh qualified OOS: `NOT_RUN_PREREGISTERED`;
- Python/Pine parity: `NOT_RUN`.

## No-retune module decisions

- continuation: `HOLD_FOR_FRESH_DATA`;
- IFVG: `REJECT_NO_INCREMENTAL_VALUE`;
- CISD: `REJECT_NO_INCREMENTAL_VALUE`;
- entry routing: `REJECT_NO_INCREMENTAL_VALUE`, PR #5 draft pending supersession decision.

## Reproducibility

- local suite: 75 tests passed;
- baseline validity: 15/15 artifacts identical;
- IFVG: 52/52;
- CISD: 52/52;
- continuation structural: 30/30;
- continuation late-60: 30/30;
- entry routing: 33/33;
- source publication archive: checksum verified and self-cleaned;
- evidence publication archive: checksum verified and self-cleaned.

## Remaining closure gates

- pinned Ruff on the exact connector-authored final head;
- pytest on Python 3.11 and 3.12;
- final adversarial PR review;
- squash merge of PR #6;
- retire or rebuild PR #5 against the accepted causal benchmark.

## Deployment restriction

No deployment, Pine strategy release, sizing recommendation, current-sample retuning, or rescue combination is authorized.
