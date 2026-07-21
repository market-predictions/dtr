# DTR Optimization Lab Status

## Current work package

`DTR-NQ-WP-20260721-04 — CISD entry-confirmation ablation`

Status: **claimed; causal design complete; implementation starting**

Branch: `agent/nq-cisd-ablation`

Predecessor: `DTR-NQ-WP-20260721-03` — complete and merged in PR #3

## Locked primary dataset

Dataset SHA-256:

`8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc`

NQ remains the sole optimization base for the current phase.

## Frozen reversal baseline

`DTR_PY_NQ_CANDIDATE_0_1_GAP_SAFE`

- trades: `491`
- expectancy: `0.180235811449135R`
- net R: `88.49578342152539R`
- profit factor: `1.3819983049452256`
- maximum drawdown: `14.107857513807524R`

No reversal parameter may change.

## Closed module decisions

- continuation: `HOLD_FOR_FRESH_DATA`;
- IFVG confirmation: `REJECT_NO_INCREMENTAL_VALUE`.

Neither result may be retuned or combined in the CISD work package.

## Current research question

Does a causal close through the first-sequence or last-candle open of an opposite-delivery run add independent value to the frozen reversal decisions after coverage loss and portfolio sequencing are considered?

## Predeclared CISD variants

- `CISD_OBSERVE`;
- `CISD_SEQUENCE_CONFIRM`;
- `CISD_LAST_CANDLE_CONFIRM`;
- `CISD_SEQUENCE_RECENT_3`;
- `CISD_SEQUENCE_RECENT_6`;
- `CISD_SEQUENCE_RETEST`.

## Immediate implementation gate

- implement bullish and bearish opposite-delivery sequences;
- implement causal sequence and last-candle anchor confirmations;
- expire stale sequences when newer opposite delivery begins;
- isolate all state by reset epoch;
- annotate frozen reversal signals;
- separate cohort and implementable portfolio results;
- reconcile every removed and newly enabled trade;
- pass pinned Ruff and pytest on Python 3.11 and 3.12.

## Promotion restriction

No CISD variant may be promoted from aggregate performance alone. Promotion requires chronological, coverage, anchor-neighbourhood, cost, portfolio-attribution, and independent-review support.

## Open project limitations

- continuous-contract rollover and back-adjustment methodology;
- exact timestamp and daylight-saving semantics;
- session-boundary and supplied VWAP reset verification;
- absence of post-December-2025 paper-forward data.
