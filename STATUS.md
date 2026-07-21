# DTR Optimization Lab Status

## Current work package

`DTR-NQ-WP-20260721-03 — IFVG entry-confirmation ablation`

Status: **claimed; causal implementation starting**

Branch: `agent/nq-ifvg-ablation`

Predecessor: `DTR-NQ-WP-20260721-02` — complete and merged in PR #2

## Locked primary dataset

Dataset SHA-256:

`8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc`

## Frozen reversal baseline

`DTR_PY_NQ_CANDIDATE_0_1_GAP_SAFE`

- trades: `491`
- net R: `88.49578342152539`
- expectancy: `0.180236R`
- maximum drawdown: `14.107857513807524R`

No reversal parameter may change in this work package.

## Held continuation result

`CONT_A2_PULLBACK_LATE60` remains `HOLD_FOR_FRESH_DATA` and may not be retuned or combined with reversal. It may appear only as a secondary diagnostic after the primary reversal IFVG analysis is complete.

## Current research question

Does a causally known, directionally aligned inversion fair value gap improve the frozen reversal decisions enough to compensate for lost opportunity coverage and portfolio-sequence effects?

## Immediate implementation gate

- implement causal bullish and bearish FVG recognition;
- implement later-close inversion without lookahead;
- partition FVG/IFVG state by reset epoch;
- annotate frozen reversal signals with IFVG state;
- separate frozen-cohort from implementable portfolio-filter analysis;
- test long/short symmetry, age windows and post-inversion zone touch;
- reconcile every added, removed and retained portfolio trade;
- pass pinned Ruff and pytest on Python 3.11 and 3.12.

## Predeclared variants

- `IFVG_OBSERVE`;
- `IFVG_CONFIRM_ANY`;
- `IFVG_CONFIRM_RECENT_3`;
- `IFVG_CONFIRM_RECENT_6`;
- `IFVG_CONFIRM_RECENT_12`;
- `IFVG_ZONE_TOUCH`.

## Promotion restriction

No IFVG rule may be promoted from a single attractive in-sample result. Promotion requires chronological, coverage, neighbourhood, cost and attribution stability plus independent review.

## Open project limitations

- continuous-contract rollover and back-adjustment methodology;
- exact timestamp and daylight-saving semantics;
- session-boundary and supplied VWAP reset verification;
- absence of post-December-2025 paper-forward data.
