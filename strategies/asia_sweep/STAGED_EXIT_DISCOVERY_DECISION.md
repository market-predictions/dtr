# Asian Sweep Staged-Exit Research — Discovery Decision

Date: `2026-07-26`  
Actions run: `30194156719`  
Evaluated head: `f84e755c64fefefb86baad55292c7c1e98871d79`  
Decision artifact: `sha256:b8963564a6f5dd2ab7ead40f87d0ef93a8914556a00b9d839d2aca1cafaf9ad0`

## Decision

`FAIL_STAGED_EXIT_DISCOVERY_STOP_BEFORE_VALIDATION`

The user's correction was valid: the Asian midpoint should be tested as TP1 rather than assumed to be the only exit. The frozen 50/50 staged-exit study was therefore completed.

Neither runner-management variant converted the validated post-T5 reversal signal into positive and stable executable expectancy during 2015–2019.

The 2020–2021 staged-exit validation and both later holdouts remain unopened.

## Frozen structure

- unchanged T5 model and probability threshold;
- unchanged audited `MKT_NEXT_OPEN` entries;
- 50% exit at the Asian midpoint before 10:00 Amsterdam;
- 50% runner to the opposite Asian boundary;
- runner time exit before 11:00 Amsterdam;
- original adverse-barrier stop or break-even after TP1;
- actual Dukascopy BID/ASK execution;
- no pair, weekday, year, side, score bucket or split-ratio selection.

## Results

| Variant | Trades | Net R | Expectancy | 0.10-pip stress | Max DD | Bootstrap P(E>0) |
|---|---:|---:|---:|---:|---:|---:|
| Original runner stop | `630` | `-4.6709R` | `-0.00741R` | `-0.02798R` | `43.7361R` | `42.11%` |
| Runner to break-even | `630` | `-5.3902R` | `-0.00856R` | `-0.02936R` | `44.8902R` | `40.72%` |

Both variants passed only the sample-size gates. Every absolute edge, breadth, annual stability, drawdown, bootstrap and cost-stress gate failed.

## Position-leg attribution

### Original-stop runner

- TP1 hit rate: `37.14%`;
- opposite-boundary TP2 rate: `18.73%`;
- TP1-leg expectancy: `-0.00736R`;
- runner-leg expectancy: `-0.00746R`;
- weighted total expectancy: `-0.00741R`.

The TP1 leg exactly reproduced the previous 100%-at-midpoint baseline logic. The runner leg was independently near-flat but negative, so combining them did not improve the pooled result.

### Break-even runner

- TP1 hit rate: `37.14%`;
- opposite-boundary TP2 rate: `13.65%`;
- break-even exits after TP1: `126`;
- TP1-leg expectancy: `-0.00736R`;
- runner-leg expectancy: `-0.00975R`;
- weighted total expectancy: `-0.00856R`.

Break-even increased the percentage of non-losing-looking outcomes and raised the raw trade win rate from `42.22%` to `47.30%`, but it reduced runner expectancy and did not improve net R or drawdown. This is a concrete example of win-rate improvement without expectancy improvement.

## Pair attribution

### Original-stop runner

| Pair | Trades | Net R | Expectancy | TP1 leg | Runner leg |
|---|---:|---:|---:|---:|---:|
| EURUSD | `323` | `+12.9844R` | `+0.04020R` | `+0.02528R` | `+0.05512R` |
| GBPUSD | `307` | `-17.6554R` | `-0.05751R` | `-0.04171R` | `-0.07331R` |

The runner helped EURUSD but harmed GBPUSD. Selecting EURUSD after observing this split is prohibited and would require a new independent pair-specific hypothesis and new evidence.

### Break-even runner

| Pair | Trades | Net R | Expectancy |
|---|---:|---:|---:|
| EURUSD | `323` | `+8.5928R` | `+0.02660R` |
| GBPUSD | `307` | `-13.9829R` | `-0.04555R` |

Break-even compressed both the positive EURUSD contribution and the negative GBPUSD contribution without producing pooled edge.

## Annual breadth

Original-stop runner expectancy:

- 2015: `-0.00400R`;
- 2016: `+0.00698R`;
- 2017: `-0.07387R`;
- 2018: `-0.07241R`;
- 2019: `+0.10969R`.

Break-even runner expectancy:

- 2015: `+0.02342R`;
- 2016: `-0.04175R`;
- 2017: `-0.06248R`;
- 2018: `-0.05478R`;
- 2019: `+0.10214R`.

Only two of five years were positive in either variant.

## Runner exit anatomy

Original-stop runner:

- full stop before TP1: `285`;
- full time exit at 10:00 without TP1: `111`;
- TP2: `118` including one same-bar TP1/TP2;
- original stop after TP1: `61`;
- runner time exit at 11:00: `55`.

Break-even runner:

- full stop before TP1: `285`;
- full time exit at 10:00 without TP1: `111`;
- TP2: `86` including one same-bar TP1/TP2;
- break-even stop after TP1: `126`;
- runner time exit at 11:00: `22`.

Moving to break-even prevented many runners from reaching either the opposite boundary or the later time exit. It reduced exposure, but also truncated favorable continuation often enough to worsen expectancy.

## Independent verification

A separate reconstruction reproduced:

- all `1,260` staged rows and `630` trades per variant;
- every event/variant identity;
- every entry, stop, TP1, TP2 and time-exit state;
- all base and stressed R values within floating-point tolerance;
- pair, year, leg-contribution, drawdown and bootstrap metrics;
- exact runner-exit counts.

No source, entry, fill-order, leg-weighting, slippage or aggregation defect was found.

## Interpretation boundary

This result rejects only the frozen staged-exit formulation:

> 50% at the midpoint, 50% to the opposite Asian boundary, runner closed by 11:00, with either the original stop or break-even.

It does not prove that every possible runner horizon, scale-out fraction or liquidity target is ineffective. Those are separate hypotheses. They cannot be introduced as post-hoc rescue parameters inside this programme.

The predictive fingerprint remains valid, but waiting until complete T5 confirmation still leaves insufficient and unstable post-entry payoff under both the single-target and tested staged-exit geometries.

## Final disposition

- stop before 2020–2025 staged-exit P&L;
- no EURUSD-only rescue;
- no alternate partial fraction, later time exit, TP2 or BE buffer in this branch;
- preserve the continuation/fake-rejection programme as a separate direct model;
- preserve earlier staged T0–T5 entry/cancel logic as a genuinely different future reversal hypothesis;
- no Pine, alerts, paper trading or deployment.
