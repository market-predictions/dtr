# DTR Python Research Run — 2026-07-21

## Decision context

TradingView is parked as the primary research environment. The Python Lab now starts from the known DTR market concept and tests its structural components directly on one-minute NQ data. TradingView will be used later only as a Pine implementation and execution-semantics validation target.

## Dataset and assumptions

- Source: `NQ_Futures_-_1min_Bar_2022_2025.zip`
- Usable rows after dropping the incomplete final date: 1,047,382 one-minute bars
- Research coverage: late December 2022 through 10 December 2025
- Timestamps are provisionally treated as Eastern-Time bar-open timestamps.
- Five-minute decision bars are reconstructed from the one-minute source.
- Stops and targets are evaluated on one-minute bars.
- A conservative stop-first assumption is used when a stop and target are both touched in the same minute.
- Commission: USD 2.25 per side per synthetic NQ contract.
- Baseline slippage: one NQ tick per side; stress tests extend to four ticks per side.

The continuous-contract rollover and adjustment method remains unresolved. Results are research evidence, not production claims.

## Scope implemented

The first engine implements the reversal branch of the DTR architecture:

1. Three New-York-clock session ranges.
2. First one-sided range sweep.
3. Sweep-depth and sweep-quality gates.
4. Reclaim after the sweep.
5. Protected pivot detection.
6. Configurable wick/close/buffered BOS definitions.
7. Displacement and acceptance requirements.
8. Break-close or retest entry modes.
9. Efficiency-ratio, ADX, VWAP and no-regime alternatives.
10. Session and weekday filters.
11. Structural/ATR stop, TP1, runner, breakeven, maximum hold and scheduled close.
12. One-position-at-a-time execution and full setup funnel counters.

Continuation, IFVG/CISD, footprint and the complete Pine scoring/dashboard model are not yet part of this research engine.

## Experiment volume

A total of **904 controlled configurations** were evaluated in staged packs:

| Pack | Configurations |
|---|---:|
| BOS/MSS | 96 |
| Sweep qualification | 120 |
| Regime/session/weekday | 200 |
| Exit architecture | 216 |
| Timing/pivot ageing | 192 |
| Stop and cost stress | 80 |
| **Total** | **904** |

Modules were optimized in sequence rather than as one undifferentiated global grid. This reduces interaction ambiguity and overfitting pressure.

## Current research candidate

`DTR_PY_NQ_CANDIDATE_0_1`

- Sessions: London 2AM, New York 9AM and Asia 7PM
- Days: Tuesday through Friday
- Sweep depth: at least 4% of the session range
- Pivot: 2-left/2-right protected pivot
- BOS: wick through the pivot
- Displacement: bar range greater than 0.90 times the 20-bar median range, directionally aligned
- Acceptance: 2 bars
- Reaction window: 10 bars
- Maximum setup age: 40 bars
- Regime: 20-bar efficiency ratio no higher than 0.35
- Stop: maximum of 8 ticks and 0.05 ATR beyond the sweep extreme
- TP1: 50% at 1.25R
- Runner: 4.0R
- Runner stop: breakeven after TP1
- Maximum holding time: 96 five-minute bars
- Scheduled close: every day at 16:00 New York

The machine-readable configuration is stored in `configs/nq_candidate_0_1.yaml`.

## Aggregate result

| Metric | Result |
|---|---:|
| Trades | 504 |
| Expectancy | 0.167R/trade |
| Net result | 84.16R |
| Profit factor | 1.35 |
| Win rate | 50.6% |
| Maximum drawdown | 14.11R |
| Return / drawdown | 5.97 |
| Average holding time | 210 minutes |

## Half-year stability

All six half-year periods were positive. Expectancy ranged from 0.073R to 0.344R per trade. The weakest period was 2024H2; the strongest was 2024H1.

This is materially stronger evidence than a single aggregate equity curve, but it is not a substitute for new unseen data.

## Attribution

### Session

- London 2AM: 172 trades, 0.302R expectancy, PF 1.64
- Asia 7PM: 155 trades, 0.100R expectancy, PF 1.20
- New York 9AM: 177 trades, 0.094R expectancy, PF 1.21

London is the dominant source of edge. Asia and New York remain positive but weaker.

### Weekday

Tuesday and Wednesday were modestly positive. Thursday and Friday produced the strongest expectancy. Monday was excluded by the selected calendar filter.

### Direction

Both directions were positive. Shorts were stronger than longs in the Python candidate, unlike the earlier contaminated TradingView run.

## Funnel

- Eligible session instances: 1,686
- Sweep-depth passes: 1,655
- Reclaims: 1,351
- Protected pivots ready: 1,282
- BOS passes: 936
- Two-bar acceptance passes: 601
- Regime-filter passes: 517
- Executed trades: 504

The largest meaningful contractions occur at BOS/acceptance and at the non-trending regime filter. The sweep-quality score itself is not yet highly discriminative because several quality settings produced identical outcomes.

## Cost stress

The selected wider stop construction remained positive at one, two and four ticks of slippage per side. Under four ticks per side, the 0.05 ATR / 8-tick stop retained positive expectancy in the development, validation and later-period samples.

This does not prove executable profitability; it shows that the candidate is not dependent on a zero-cost model.

## Monte Carlo trade-sequence bootstrap

10,000 bootstrap samples of the 504 realized trade outcomes produced:

- Probability of positive total R: 99.83%
- 5th percentile net result: 37.42R
- Median net result: 84.19R
- 95th percentile net result: 131.94R
- Median maximum drawdown: 14.34R
- 95th percentile maximum drawdown: 25.07R

The bootstrap resamples the observed trade distribution and does not model structural regime failure.

## Rolling walk-forward result

Four rolling six-month tests were run. A candidate was selected using only the preceding twelve months from a 37-member parameter neighbourhood.

- 2024H1: +0.197R/trade
- 2024H2: +0.006R/trade
- 2025H1: +0.339R/trade
- 2025H2: +0.052R/trade

All four forward folds were positive, but 2024H2 and 2025H2 were weak. The optimizer therefore does not have permission to claim a uniformly strong edge.

## Main conclusions

1. Two-bar acceptance is consistently more robust than one-bar acceptance on this NQ dataset.
2. A 2/2 protected pivot is more stable than the faster 1/1 alternative.
3. Break-close entries outperform retest-only entries in the candidates that remain positive across time segments.
4. A 4% minimum sweep-depth requirement improves stability without collapsing the sample.
5. Non-trending conditions, measured by efficiency ratio, improve the all-session result.
6. Tuesday-Friday is more robust than all weekdays, but Thursday and Friday carry a disproportionate share of the result.
7. The original 2.5R runner is not optimal in this research model; 4R performed better when paired with TP1 and breakeven.
8. Setup ageing beyond 40 bars adds trades without improving robustness.
9. London is the strongest session, but restricting to London alone creates a smaller and more overfit-looking sample.
10. A parameter neighbourhood is positive; the result is not dependent on one exact number, although some folds remain weak.

## Known limitations

- The engine is a Python research interpretation of the DTR concept, not an exact Pine clone.
- Continuation trades are not yet implemented.
- IFVG, CISD, higher-timeframe score, H1Vol, Weekly VWAP and footprint logic are not yet included.
- The session ranges use exact one-minute boundaries rather than TradingView five-minute session-bar semantics.
- Continuous-contract rollover handling is unresolved.
- The later 2025 sample was inspected during candidate research and is therefore robustness evidence, not a pristine final holdout.
- No live paper-forward period exists yet.

## Next work packages

1. Add continuation as a separate, independently measured engine.
2. Add IFVG/CISD entry refinements without mixing them into the current baseline prematurely.
3. Add anchored session and weekly VWAP context as score-only and hard-gate variants.
4. Implement rolling optimizer selection with locked experiment manifests.
5. Add true paper-forward ingestion when post-December-2025 NQ data becomes available.
6. Only after those gates, create a Pine candidate for TradingView validation.
