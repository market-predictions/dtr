# DTR Advanced Context Research — 2026-07-22

## Decision

`NO_HISTORICAL_PROMOTION_CONTINUE_FRESH_OOS_RESEARCH`

The advanced context program found economically meaningful historical patterns, but none proved a statistically reliable incremental advantage over the unfiltered timing-corrected baseline. No context filter is approved for deployment, Pine implementation, or replacement of the baseline.

Two single-factor definitions are retained as frozen **fresh out-of-sample challengers**:

1. `E5_EXCLUDE_COMPRESSED_RANGE`
2. `E6_EXCLUDE_NEAR_PRIOR_DAY_DIRECTIONAL_EXTREME`

The interaction `I1_NOT_COMPRESSED_AND_NOT_NEAR_PRIOR_DAY` is retained only as an under-sampled shadow challenger.

## Frozen exploratory baseline

`DTR_CAUSAL_BAR_CLOSE_RANGE_SHIFT_MINUS1`

- vendor minute labels treated as bar-close and shifted back one minute before resampling;
- London range `[01:11, 02:12)` ET;
- New York range `[08:11, 09:12)` ET;
- Asia range `[19:00, 20:01)` ET;
- entry-search deadlines unchanged;
- all strategy parameters, costs and causal gap liquidation unchanged.

| Metric | Baseline |
|---|---:|
| Trades | 477 |
| Net R | 42.577515 |
| Expectancy | 0.089261R |
| Profit factor | 1.178993 |
| Max drawdown | 16.426493R |
| Return/DD | 2.592003 |

This baseline was selected after timing sensitivity was inspected. It is therefore exploratory and cannot authorize deployment.

## Causal feature architecture

All contextual features were constructed from information available before the applicable decision:

- previous completed ETH-day EMA, ATR, ADX and realized volatility;
- last completed four-hour EMA, ADX and efficiency ratio;
- previous completed CME-style week high and low;
- initial-range size, volume and VWAP known at range completion;
- entry-bar relative volume and VWAP known only after the entry signal bar closed.

Independent audit counts:

| Causality check | Violations |
|---|---:|
| D1 completion after range start | 0 |
| H4 completion after range start | 0 |
| Weekly completion after range start | 0 |
| Range completion after entry | 0 |

## Stage 1 — univariate families

Twelve families and 37 categories were tested:

- D1 direction;
- H4 direction;
- D1/H4 confluence;
- D1 volatility regime;
- higher-timeframe trend strength;
- initial-range volatility fit;
- volatility transition;
- prior-day location;
- prior-week location;
- overnight gap context;
- relative volume;
- VWAP/value location.

No category passed the complete promotion gate. Several narrow categories had high expectancy but retained too few trades. The most relevant negative regimes were:

- D1 countertrend;
- H4 countertrend;
- middle D1 volatility tercile;
- compressed initial ranges;
- proximity to the prior-day directional extreme;
- outside the prior-week range.

Directional findings were internally inconsistent: D1 alignment was favorable, H4 neutrality was favorable, but D1/H4 both-aligned was near flat. Direction filters are therefore not retained as operational candidates.

## Stage 2 — broad exclusion rules

Broad rules excluded one weak regime while passing feature-warm-up observations through.

| Rule | Trades | Net R | Exp. R | PF | DD R | Return/DD | 2-tick exp. | Edge p | Incremental p | State |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Exclude near prior-day directional extreme | 304 | 48.937550 | 0.160979 | 1.350938 | 8.632571 | 5.668942 | 0.143241 | 0.0366 | 0.7746 | Diagnostic |
| Exclude compressed range | 335 | 49.464423 | 0.147655 | 1.319303 | 9.470457 | 5.223024 | 0.131509 | 0.0449 | 0.7362 | Diagnostic |
| Keep mixed/neutral D1-H4 confluence | 261 | 47.496561 | 0.181979 | 1.407294 | 9.918449 | 4.788709 | 0.164618 | 0.0342 | 0.8157 | Diagnostic |
| Exclude D1 countertrend | 322 | 39.350391 | 0.122206 | 1.257623 | 9.764691 | 4.029865 | 0.104538 | 0.1075 | 1.0000 | Diagnostic |
| Exclude middle D1 volatility | 357 | 48.929854 | 0.137058 | 1.293464 | 16.601625 | 2.947293 | 0.119929 | 0.0535 | 0.7349 | Reject |
| Exclude H4 countertrend | 318 | 43.500392 | 0.136794 | 1.289441 | 16.590537 | 2.622000 | 0.118448 | 0.0796 | 0.8796 | Reject |

The edge p-value tests whether the selected rule remains positive after correcting across the six broad rules. The incremental p-value tests paired per-session improvement over the unfiltered baseline. The first three rules retained a familywise-positive edge, but none established incremental superiority.

## Stage 3 — capped two-factor interactions

Six interactions were frozen before inspection. No third factor or substitute interaction was allowed.

The strongest interaction was:

`I1_NOT_COMPRESSED_AND_NOT_NEAR_PRIOR_DAY`

| Metric | Result |
|---|---:|
| Trades | 220 |
| Net R | 56.774134 |
| Expectancy | 0.258064R |
| Profit factor | 1.605191 |
| Max drawdown | 8.554419R |
| Return/DD | 6.636819 |
| Two-tick expectancy | 0.240742R |
| Familywise edge p | 0.0041 |
| Familywise incremental p | 0.4919 |

It failed the frozen 250-trade requirement and its paired incremental advantage remained uncertain. The gate was not relaxed.

## Adversarial threshold sensitivity

The frozen definitions were challenged without selecting a replacement threshold.

### Exclude compressed range

Thresholds at the 25th, 33.3rd and 40th trailing same-session percentiles produced:

- 301–362 trades;
- 45.66–53.11R;
- 0.1467–0.1517R expectancy;
- positive results in 2023, 2024 and 2025;
- positive two-tick expectancy throughout.

### Exclude proximity to prior-day directional extreme

Thresholds at 0.20, 0.25 and 0.30 D1 ATR produced:

- 284–340 trades;
- 39.59–56.20R;
- 0.1394–0.1653R expectancy;
- positive results in every calendar year;
- positive two-tick expectancy throughout.

### Full 3×3 interaction surface

All nine cells were reported; none was selected.

- trades: 180–269;
- net R: 41.73–68.01R;
- expectancy: 0.2247–0.2745R;
- drawdown: 7.34–10.94R;
- return/DD: 4.88–8.04;
- every cell remained positive in every calendar year and under two-tick costs.

This supports a stable historical relationship, but does not resolve selection pressure.

## Independent adversarial review

A separate implementation reconstructed all 12 broad and interaction portfolios directly from signal-level independent trade outcomes. All metrics matched.

Paired date-block bootstrap of net-R improvement versus the baseline:

| Candidate | Observed delta R | 95% interval | Probability delta > 0 |
|---|---:|---:|---:|
| I1 combined challenger | +14.1966 | −23.1952 to +51.3714 | 0.776 |
| Exclude compressed range | +6.8869 | −20.1105 to +33.5717 | 0.697 |
| Exclude near prior-day extreme | +6.3600 | −25.0985 to +36.9706 | 0.662 |

All intervals include zero. The historical improvement is plausible, not established.

## Usable result

The current useful output is a three-arm frozen research comparison for qualified fresh data:

1. **Primary comparator:** unfiltered `DTR_CAUSAL_BAR_CLOSE_RANGE_SHIFT_MINUS1`.
2. **Challenger A:** skip signals when the initial range is below the 33.3rd percentile of trailing same-session range/D1-ATR observations.
3. **Challenger B:** skip signals when the relevant range edge is within 0.25 previous-day ATR of the prior-day directional extreme.
4. **Shadow only:** apply both challenger conditions together.

No parameters may be altered after fresh data inspection. Challenger A and B should be tested independently before considering their interaction.

## What not to implement

Do not implement or promote:

- D1/H4 direction filters;
- session or weekday selection;
- a best cell from the threshold sensitivity surface;
- the combined interaction as the primary strategy;
- higher leverage based on the improved historical drawdown;
- Pine code before the timestamp-corrected finalist survives fresh OOS.

## Final decision

`CONTINUE_RESEARCH_DO_NOT_DEPLOY`

The advanced tests produced two coherent, causal and reasonably robust challenger filters. They are suitable for preregistered fresh OOS comparison, not for historical promotion.
