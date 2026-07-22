# DTR Optimization Lab Status

## Current stacked work package

`DTR-NQ-WP-20260722-14 — E6 fixed-fraction equity and execution-cost stress`

Status: **research complete; independent review and deterministic repeat passed**

Decision state: `EQUITY_COST_STRESS_COMPLETE_NO_SIZING_AUTHORIZATION`

Base dependency: `DTR-NQ-WP-20260722-13 — E6 event, holiday and rollover attribution` remains a stacked draft on PR #13.

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

### Working advanced-test baseline

`E6_EXCLUDE_NEAR_PRIOR_DAY_DIRECTIONAL_EXTREME`

- 304 trades;
- 48.937550R net;
- 0.160979R expectancy;
- 8.632571R maximum drawdown;
- 5.668942 return/DD.

E6 remains research-only and unchanged.

## Completed E6 advanced programme

- Blocks 0–3: mechanism supported; no additional path or reward-space filter advanced.
- Block 4: retain current one-open-position global sequencing.
- Block 5: preserve FOMC-pre and expiration/roll overlap only as future risk-watch cohorts; no event exclusion.
- Block 6: fixed-fraction equity and cost stress complete.

## Block 6 findings

Observed $100,000 account under normal costs:

- 0.50% risk: $126,940 final equity; 4.3% maximum drawdown.
- 1.00% risk: $159,185 final equity; 8.4% maximum drawdown.
- 1.50% risk: $197,231 final equity; 12.4% maximum drawdown.

Observed account under severe four-tick-per-side costs:

- 0.50% risk: $117,082 final equity; 5.3% maximum drawdown.
- 1.00% risk: $135,430 final equity; 10.3% maximum drawdown.
- 1.50% risk: $154,787 final equity; 15.2% maximum drawdown.

Resampled conclusion:

- 0.50% is the most drawdown-resilient tested envelope.
- 1.00% is a middle research envelope but can produce 20% drawdowns when execution is poor.
- 1.50% is aggressive; under severe costs approximately 45–55% of resamples reached 20% drawdown and approximately 9–14% reached 30% drawdown.
- Independent reconstruction and deterministic repeat passed.

Decision: preserve 0.50% and 1.00% only as paper-research envelopes. Do not treat 1.50% as a balanced default. No live sizing recommendation follows.

## Next evidence gate

The bounded E6 historical programme is complete. Highest-value next evidence:

- qualified fresh post-2025 NQ data;
- materially longer contract-audited NQ history; or
- unchanged ES replication.

## Existing unresolved gates

- authoritative timestamp metadata or qualified replacement dataset: `UNRESOLVED`;
- continuous-contract methodology: `UNRESOLVED`;
- original 904-search familywise adjustment: `UNRESOLVED_EXACT_RECONSTRUCTION_BLOCKED`;
- qualified fresh OOS Arms 0/A/B: `NOT_RUN_PREREGISTERED`;
- Python/Pine parity: `NOT_RUN`.

## Scope restrictions

No E6 threshold change, event-window search, event exclusion, weekday/session search, sequencing retune, additional interaction, risk-fraction optimization, dynamic sizing, Pine port, live sizing recommendation, leverage increase or deployment is authorized.
