# DTR Optimization Lab Status

## Current work package

`DTR-NQ-WP-20260721-02 — Independent continuation engine`

Status: **complete; awaiting final CI and PR merge**

Branch: `agent/nq-continuation-engine`

Draft PR: `#2 — Build independent NQ continuation engine`

Decision: `HOLD_FOR_FRESH_DATA`

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

Both remain frozen.

## Continuation result

The four unfiltered structural variants are negative. Immediate entry is decisively poor. Two-bar pullback is the least adverse unfiltered route.

Held research lead:

`CONT_A2_PULLBACK_LATE60`

- trades: `147`
- expectancy: `0.108895R`
- net R: `16.007565R`
- profit factor: `1.242960`
- maximum drawdown: `8.003633R`

The lead remains held because bootstrap intervals include zero, four-tick slippage produces a negative aggregate result, and no fresh post-December-2025 sample exists.

## Validation status

- standalone continuation module: **complete**
- strict continuation manifests: **complete**
- structural fixtures: **passed**
- full existing regression suite: **passed locally**
- canonical baseline rerun: **byte-identical**
- canonical late-60 stress rerun: **byte-identical**
- independent adversarial review: **complete**
- reviewed package publication: **complete**
- temporary publication material: **removed**
- normal read-only CI workflow: **restored**
- GitHub CI on connector-authored published head: **running**

## Promotion restriction

Continuation may not be combined with reversal. No further continuation timing, session, or exit tuning is authorized on the current dataset.

## Next planned work package

`DTR-NQ-WP-20260721-03 — IFVG entry-confirmation ablation`

It will test IFVG as an independently measurable confirmation layer against the frozen gap-safe reversal baseline. The held continuation lead may appear only as a secondary diagnostic and may not be retuned.

## Open project limitations

- continuous-contract rollover and back-adjustment methodology;
- exact timestamp and daylight-saving semantics;
- session-boundary and supplied VWAP reset verification;
- absence of post-December-2025 paper-forward data.
