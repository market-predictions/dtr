# DTR Optimization Lab Status

## Current work package

`DTR-NQ-WP-20260721-02 — Independent continuation engine`

Status: **claimed; design and baseline implementation starting**

Branch: `agent/nq-continuation-engine`

Predecessor: `DTR-NQ-WP-20260721-01` — complete and merged in PR #1

## Locked data and reversal baselines

Dataset SHA-256:

`8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc`

### Observe-only reference

- candidate: `DTR_PY_NQ_CANDIDATE_0_1`
- trades: `504`
- net R: `84.16435914242919`
- maximum drawdown: `14.107857513807524R`

### Gap-safe reversal baseline

- candidate: `DTR_PY_NQ_CANDIDATE_0_1_GAP_SAFE`
- trades: `491`
- net R: `88.49578342152539`
- maximum drawdown: `14.107857513807524R`

Both are frozen. The continuation branch must not retune or modify them.

## Current research question

Does an accepted session-range breakout provide an independent, robust continuation edge after realistic costs, and is immediate or first-pullback entry the better decision route?

## Immediate implementation gate

- create a separate continuation event-state module;
- define upside/downside accepted breaks and failed-breakout invalidation;
- implement one-bar and two-bar acceptance fixtures;
- implement immediate and first-pullback entry fixtures;
- preserve the locked `reject_unsafe` data contract;
- instrument the unfiltered continuation funnel before optimization;
- pass pinned Ruff and pytest on Python 3.11 and 3.12.

## Promotion restriction

No continuation candidate may be combined with reversal until it demonstrates independently positive chronological validation and walk-forward evidence with acceptable opportunity coverage and an independent review decision.

## Open project limitations

- continuous-contract rollover and back-adjustment methodology;
- exact timestamp and daylight-saving semantics;
- session-boundary and supplied VWAP reset verification;
- absence of post-December-2025 paper-forward data.
