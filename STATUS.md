# DTR Optimization Lab Status

## Current stacked work package

`DTR-NQ-WP-20260722-08 — Advanced Context Robustness`

Status: **research complete; deterministic evidence and independent review ready for stacked publication**

Decision state: `NO_HISTORICAL_PROMOTION_CONTINUE_FRESH_OOS_RESEARCH`

Base dependency: `DTR-NQ-WP-20260722-07 — Selection robustness and explicit execution contract` remains open and draft.

## Active timing-corrected exploratory baseline

`DTR_CAUSAL_BAR_CLOSE_RANGE_SHIFT_MINUS1`

- 477 trades;
- 0.089261R expectancy;
- 42.577515R net;
- PF 1.178993;
- maximum drawdown 16.426493R;
- return/DD 2.592003.

This baseline treats vendor minute labels as bar-close, shifts timestamps back one minute before five-minute resampling, and restores the one-minute-earlier London/New York range rows. It was selected after timing sensitivity was inspected and is therefore exploratory only.

## Advanced context result

Completed:

- 12 causal context families and 37 univariate categories;
- six frozen broad exclusions;
- six capped two-factor interactions;
- fixed threshold sensitivity surface;
- one-, two- and four-tick cost stress;
- calendar-year and half-year attribution;
- familywise edge and paired incremental inference;
- independent metric reconstruction and causality review;
- byte-identical deterministic repeats.

No historical filter passed the complete promotion gate.

## Frozen fresh-OOS challengers

- Arm 0: unfiltered timing-corrected baseline.
- Arm A: exclude initial ranges below the 33.3rd trailing same-session range/D1-ATR percentile.
- Arm B: exclude setups within 0.25 previous-day ATR of the prior-day directional extreme.
- Arm C: apply A and B together; shadow-only because the frozen historical interaction retained 220 trades.

Arm A and B materially improved historical expectancy and drawdown and remained positive in every year and under two-tick costs. Their paired incremental advantage versus Arm 0 remains statistically unresolved.

## Selection work package status

- original staged 904 chronology: `EXACT_RECONSTRUCTION_BLOCKED`;
- explicit causal execution contract: implemented on PR #7;
- current-code causal 904 universe: paused pending final timestamp-alignment decision;
- no claim that advanced context testing repairs the missing original selection chronology.

## Existing unresolved gates

- authoritative bar-open/bar-close metadata or qualified replacement dataset: `UNRESOLVED`; internal boundary census strongly supports bar-close;
- continuous-contract methodology: `UNRESOLVED`;
- original 904-search familywise adjustment: `UNRESOLVED_EXACT_RECONSTRUCTION_BLOCKED`;
- qualified fresh OOS Arms 0/A/B: `NOT_RUN_PREREGISTERED`;
- Python/Pine parity: `NOT_RUN`.

## Scope restrictions

No fresh 2026 performance inspection, threshold retuning, new context family, third-factor interaction, session/weekday filtering, Pine port, sizing recommendation, leverage increase, or deployment is authorized.
