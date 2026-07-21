# DTR Optimization Lab Status

## Current work package

`DTR-NQ-WP-20260722-05 — Reversal entry-routing ablation`

Status: **claimed; causal design complete; implementation starting**

Branch: `agent/nq-entry-routing-ablation`

Predecessor: `DTR-NQ-WP-20260721-04` — complete and merged in PR #4

## Locked primary dataset

Dataset SHA-256:

`8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc`

NQ remains the sole optimization base for the current phase.

## Frozen reversal baseline

`DTR_PY_NQ_CANDIDATE_0_1_GAP_SAFE`

- trades: `491`;
- expectancy: `0.180235811449135R`;
- net R: `88.49578342152539R`;
- profit factor: `1.3819983049452256`;
- maximum drawdown: `14.107857513807524R`.

Signal generation, stop construction, targets, and exits are frozen.

## Closed module decisions

- continuation: `HOLD_FOR_FRESH_DATA`;
- IFVG confirmation: `REJECT_NO_INCREMENTAL_VALUE`;
- CISD confirmation: `REJECT_NO_INCREMENTAL_VALUE`.

None may be retuned or combined in the entry-routing work package.

## Current research question

Does a causal first-pullback entry or a predeclared signal-time hybrid router improve the frozen break-close reversal entry after no-fills, latency, actual stop distance, costs, and changed portfolio sequencing are included?

## Predeclared routes

- `ENTRY_BREAK_CLOSE`;
- `ENTRY_FIRST_PULLBACK`;
- `ENTRY_HYBRID_PREDECLARED`.

## Baseline pullback contract

- structural reference: frozen broken pivot/BOS level;
- minimum band width: four ticks;
- ATR band width: 0.10 ATR;
- response: close back in the reversal direction after the first touch;
- expiry: 12 five-minute bars;
- maximum pre-touch extension: 1.50 times original signal risk;
- hybrid immediate-entry threshold: extension no greater than 0.35 ATR;
- no retrospective touch-price fills.

## Immediate implementation gate

- implement causal signal-to-entry route state;
- preserve the exact frozen break-close regression;
- calculate route-specific entry-to-stop risk;
- count touch, response, no-fill, expiry, invalidation, reset, and excessive-extension outcomes;
- separate signal-level opportunity from implementable portfolio results;
- attribute missed, delayed, replaced, retained, and newly enabled trades;
- pass pinned Ruff and pytest on Python 3.11 and 3.12.

## Promotion restriction

No route may be promoted from aggregate net R or entry-price improvement alone. Promotion requires chronological, coverage, cost, band/expiry neighbourhood, sequencing, and independent-review support.

## Open project limitations

- continuous-contract rollover and back-adjustment methodology;
- exact timestamp and daylight-saving semantics;
- session-boundary and supplied VWAP reset verification;
- absence of post-December-2025 paper-forward data.
