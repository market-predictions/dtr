# DTR Optimization Lab Status

## Current stacked work package

`DTR-NQ-WP-20260722-15 — Promote E6 no-FOMC working baseline`

Status: **completed and documented**

Decision state: `PROMOTE_E6_NO_FOMC_DAY_AS_WORKING_BASELINE`

Base dependency: `DTR-NQ-WP-20260722-14 — E6 fixed-fraction equity and execution-cost stress` remains a stacked draft on PR #14.

## Baseline hierarchy

### Execution regression benchmark

`DTR_PY_NQ_CANDIDATE_0_1_CAUSAL_GAP`

- 495 trades;
- 86.004761R net;
- 0.173747R expectancy.

### Mandatory non-selectable control

`DTR_CAUSAL_BAR_CLOSE_RANGE_SHIFT_MINUS1`

- 477 trades;
- 42.577515R net;
- 0.089261R expectancy;
- 16.426493R maximum drawdown.

### Frozen E6 comparator

`E6_EXCLUDE_NEAR_PRIOR_DAY_DIRECTIONAL_EXTREME`

- 304 trades;
- 48.937550R net;
- 0.160979R expectancy;
- 8.632571R maximum drawdown;
- 5.668942 return/DD.

### Current working research baseline

`E6_NO_FOMC_DAY`

Rule: reject entries whose Eastern Time calendar date equals an official FOMC statement date, then rerun the one-global-position sequencing.

- 291 trades;
- 53.483342R net;
- 0.183792R expectancy;
- 9.151061R maximum drawdown;
- 5.844496 return/DD.

At 1% current-equity risk, the historical account path grew $100,000 to approximately $166,725 with an 8.87% maximum drawdown.

This is a user-mandated risk-policy baseline change. Original E6 remains the frozen comparator because the FOMC sample is limited and the rule was not statistically promoted.

## Completed E6 advanced programme

- Blocks 0–3: mechanism supported; no additional path or reward-space filter advanced.
- Block 4: retain current one-open-position global sequencing.
- Block 5: FOMC risk identified; CPI/NFP did not justify exclusions; expiration/roll weakness came from one shared cohort.
- Block 6: fixed-fraction equity and cost stress complete.
- Baseline policy override: no entries on official FOMC statement dates.

## Next evidence gate

Use `E6_NO_FOMC_DAY` as the working baseline for subsequent research, while retaining original E6 as a control. Highest-value next evidence:

- qualified fresh post-2025 NQ data;
- materially longer contract-audited NQ history; or
- unchanged ES replication.

## Existing unresolved gates

- authoritative timestamp metadata or qualified replacement dataset: `UNRESOLVED`;
- continuous-contract methodology: `UNRESOLVED`;
- original 904-search familywise adjustment: `UNRESOLVED_EXACT_RECONSTRUCTION_BLOCKED`;
- qualified fresh OOS comparison of original E6 versus E6 no-FOMC: `NOT_RUN`;
- Python/Pine parity: `NOT_RUN`.

## Scope restrictions

No additional FOMC buffer search, alternate event-day definition, E6 threshold change, weekday/session search, sequencing retune, risk-fraction optimization, dynamic sizing, Pine port, live sizing recommendation, leverage increase or deployment is authorized.
