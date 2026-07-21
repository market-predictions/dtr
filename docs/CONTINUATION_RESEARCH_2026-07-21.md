# NQ Independent Continuation Research — 2026-07-21

## Decision

`HOLD_FOR_FRESH_DATA`

The continuation engine is complete and reproducible, but no continuation candidate is authorized for combination with the frozen reversal branch. The unfiltered structural variants are negative. A plausible late two-bar pullback pattern survives several robustness checks, but its uncertainty and cost sensitivity are too high for promotion on the current dataset.

## Research question

After NQ exits a DTR session range, does accepted price outside the range create an independently tradable continuation edge after realistic costs?

The engine deliberately separates:

1. first breakout attempt;
2. one-bar or two-bar acceptance;
3. immediate or first-pullback entry;
4. pre-entry failure and expiry;
5. structural risk and failed-breakout exit;
6. gap-safe one-minute execution.

Only the first breakout attempt per session is evaluated. No reversal condition, regime filter, weekday optimization, or adaptive routing is borrowed from the reversal candidate.

## Data and execution contract

- Dataset SHA-256: `8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc`
- Source: NQ one-minute archive, late December 2022 through 10 December 2025 after incomplete-date removal.
- Decision bars: five minutes.
- Execution bars: one minute.
- Gap policy: `reject_unsafe`.
- Collision policy: conservative stop first.
- Baseline slippage: one tick per side.
- Commission: USD 2.25 per side under the existing DTR cost convention.
- Structural stop: inside the broken boundary by the greater of four ticks or 0.10 ATR.
- Baseline exit: 50% at 1R, runner at 3R, runner to breakeven after TP1.
- Event expiry: session decision-window end or 72 five-minute bars, whichever occurs first.

## Structural baseline

| Variant | Trades | Expectancy | Net R | PF | Max DD | Development | Validation | Later research |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| One-bar, immediate | 2,055 | -0.207R | -425.67R | 0.66 | 425.67R | -0.240R | -0.178R | -0.167R |
| Two-bar, immediate | 1,456 | -0.081R | -117.70R | 0.86 | 126.13R | -0.128R | -0.004R | -0.050R |
| One-bar, pullback | 900 | -0.107R | -96.15R | 0.81 | 100.03R | -0.147R | -0.036R | -0.065R |
| Two-bar, pullback | 530 | -0.076R | -40.03R | 0.86 | 52.90R | -0.152R | +0.030R | +0.004R |

The baseline conclusion is adverse: raw accepted range breaks do not provide an independently positive continuation edge under this execution model. Two-close acceptance and pullback entry reduce the damage materially, but do not rescue the unfiltered branch.

## Funnel

Across 2,294 session records:

- 2,143 were eligible by session and weekday;
- 26 ranges were rejected for data contamination;
- 53 post-range paths were truncated at reset boundaries;
- 2,069 first breakout attempts occurred;
- 1,484 passed two-bar acceptance;
- 532 produced a valid two-bar pullback entry signal;
- two open-trade bridges were rejected by the unsafe-gap policy;
- 530 baseline two-bar pullback trades remained.

## Diagnostic lead: late two-bar pullback

Development-defined diagnostic screening found one economically plausible feature: a two-bar accepted breakout followed by a valid pullback at least approximately one hour after range completion.

`CONT_A2_PULLBACK_LATE60` produced:

- 147 trades, including two pre-2023 observations;
- 0.108895R expectancy;
- 16.007565R net;
- profit factor 1.242960;
- maximum drawdown 8.003633R.

Chronological periods:

| Period | Trades | Expectancy | Net R |
|---|---:|---:|---:|
| Development | 74 | 0.052261R | 3.867289R |
| Validation | 36 | 0.171057R | 6.158060R |
| Later research | 35 | 0.230726R | 8.075419R |

### Timing neighbourhood

The 60–70 minute region forms a positive plateau in all three main periods:

| Minimum delay | Trades | All expectancy | Development | Validation | Later |
|---:|---:|---:|---:|---:|---:|
| 50 min | 197 | 0.043807R | 0.052501R | 0.016310R | 0.103838R |
| 55 min | 175 | 0.022851R | 0.015938R | -0.017518R | 0.139193R |
| 60 min | 147 | 0.108895R | 0.052261R | 0.171057R | 0.230726R |
| 65 min | 125 | 0.119234R | 0.058464R | 0.151013R | 0.292794R |
| 70 min | 105 | 0.185164R | 0.044977R | 0.259975R | 0.386394R |

The concept is plausible: a later break follows a longer balance period and may represent genuine price acceptance rather than the first liquidity excursion. However, the pattern was discovered through diagnostic screening on this finite dataset and must therefore be treated as a research lead.

## Risk and exit stress

A predeclared 12-configuration stop/exit pack was applied to the late-60 signal population. All 12 configurations remained positive in development, validation, and later research. Aggregate expectancy ranged approximately from 0.077R to 0.166R.

The highest result used no breakeven move, but it is not promoted because it was observed after the structural lead was identified. The conservative 1R/3R-with-breakeven baseline remains the reference.

## Cost stress

| Slippage each side | Expectancy | Net R | Development | Validation | Later |
|---:|---:|---:|---:|---:|---:|
| 1 tick | 0.108895R | 16.007565R | 0.052261R | 0.171057R | 0.230726R |
| 2 ticks | 0.039879R | 5.862170R | -0.063290R | 0.192384R | 0.164531R |
| 4 ticks | -0.041928R | -6.163435R | -0.126104R | 0.113281R | 0.037537R |

The lead is therefore thin relative to execution friction. It cannot be treated as robust for poor fills or highly volatile execution conditions.

## Session concentration

- London: positive overall and in all three main periods, but development expectancy was only 0.004R.
- New York: strong development, approximately flat validation, negative later research.
- Asia: negative development and validation, positive later research.
- London plus New York: positive in all three periods and stronger than the all-session mix.

No single session delivers a decisive, high-sample, chronologically stable explanation. London is the strongest contributor, but a London-only rule would be another post-selection step and is not promoted.

## Walk-forward threshold stress

An expanding threshold-selection exercise selected 65 minutes for the first three folds and 90 minutes for the final fold. Combined test performance was:

- 71 trades;
- 8.380814R net;
- 0.118040R weighted expectancy.

Fold results were positive in 2024H1, 2024H2, and 2025H2, but negative in 2025H1. The final fold contained only nine trades. This supports continued observation, not deployment.

## Statistical uncertainty

For the 147-trade late-60 population:

- trade bootstrap 95% expectancy interval: `[-0.072828R, 0.292601R]`;
- month-block bootstrap 95% interval: `[-0.097124R, 0.323891R]`.

Both intervals cross zero. The sample cannot distinguish a modest positive edge from noise with sufficient confidence.

## Independent conclusion

The continuation branch has answered its strategic question:

1. **Unfiltered accepted range breakouts are not useful.**
2. **Two-bar acceptance is materially better than one-bar acceptance.**
3. **Pullback entry is materially better than immediate entry.**
4. **A late two-bar pullback is a credible structural lead.**
5. **The lead is not robust enough for combination or production.**

Decision: `HOLD_FOR_FRESH_DATA`.

The code, manifests, and compact evidence are retained. No further continuation tuning should be performed on the current NQ sample. The lead may be reassessed on genuinely new post-December-2025 data or a separately approved market dataset.
