# Directional Extension × Strong H1 Rejection — Reversal Preregistration

**Study ID:** `DFXC-20260808-010-extension-conditioned-reversal`  
**Date frozen:** 2026-08-08  
**Parent branch/head:** `agent/pivot-daily-h1-continuation-management` @ `044c30b6961ed8ed05f22609d59c9e9e8e46b45b`  
**Dataset:** Dukascopy FX Cash, ten-pair M1 BID/ASK  
**Internal outcome window:** 2015-2025 only  
**Conditional fresh confirmation:** 2026 YTD ending exclusive 2026-07-24; remains unopened unless the internal promotion gate below passes unchanged.

## Decision problem

Prior Daily-pivot studies established a structural terminal/exhaustion association around first-order pivots, but neither immediate nor confirmation-based countertrend entry and neither a universal continuation exit rule produced executable edge after real BID/ASK execution.

This study tests a materially different mechanism suggested by the principal:

> Does a strong H1 rejection become more reversal-prone as the market has already travelled farther in the incoming direction, independent of whether the rejection occurs at a named pivot?

The causal variable is **pre-rejection directional extension**, not pivot number. Daily pivot location is evaluated only after the extension effect itself is tested.

## Frozen generic strong-rejection universe

For every completed H1 bar on the ten canonical FX pairs, using midpoint H1 bars derived from synchronized Dukascopy BID/ASK M1 quotes:

- H1 range must be positive;
- lagged H1 ATR24 must be finite and positive;
- lagged Daily ATR20 must be finite and positive;
- upper-wick fraction = `(high - max(open, close)) / (high - low)`;
- lower-wick fraction = `(min(open, close) - low) / (high - low)`;
- a strong rejection requires wick fraction `>= 0.30`;
- an upper rejection is eligible only when `high > NY17 FX-day open`, representing an incoming upward extension and a countertrend-short response;
- a lower rejection is eligible only when `low < NY17 FX-day open`, representing an incoming downward extension and a countertrend-long response;
- bars on which both upper and lower wicks simultaneously meet the `>=0.30` threshold are excluded as directionally ambiguous;
- the signal is observable only after the H1 bar closes;
- no weekday, session, pivot, trend, MA or other contextual filter is applied to the primary universe.

## Frozen extension metric

The NY17 FX trading day is the same day convention used in the parent pivot programme.

For each FX day:

- `day_open` = open of the first H1 bar belonging to that NY17 FX date;
- completed-day true range = `max(day_high, previous_day_close) - min(day_low, previous_day_close)`;
- `Daily_ATR20_lag1` = simple mean of the previous 20 completed NY17 FX-day true ranges, shifted by one FX day so the signal day is never included.

Directional extension at the rejection event:

- upper rejection: `EXT = (signal_high - day_open) / Daily_ATR20_lag1`;
- lower rejection: `EXT = (day_open - signal_low) / Daily_ATR20_lag1`.

`EXT` must be non-negative by construction.

## Frozen extension bins

For interpretability, events are assigned before outcome inspection to:

- `E0`: `0.00 <= EXT < 0.75`;
- `E1`: `0.75 <= EXT < 1.25`;
- `E2`: `1.25 <= EXT < 1.75`;
- `E3`: `EXT >= 1.75`.

The continuous `EXT` value remains the primary dose variable; bins are not tuned after seeing outcomes.

## Executable reversal response

At the first active M1 quote after the completed H1 signal:

- lower rejection / countertrend long enters at ASK;
- upper rejection / countertrend short enters at BID.

Primary exit is fixed 240 contiguous minutes after executable entry:

- long exits at BID;
- short exits at ASK.

Primary endpoint:

`REV4_ATR` = executable four-hour countertrend return divided by the signal's lagged H1 ATR24.

No commission beyond observed spread and no ordinary slippage are added. No weekend or missing-hour bridge is permitted. The same first-active-quote, contiguous-hour and endpoint-tolerance rules used in the executable parent studies apply. If the horizon cannot be completed safely, the endpoint is missing.

## Primary hypotheses

### H1 — extension dose effect

Null: greater pre-rejection directional extension does not improve subsequent executable four-hour countertrend return.

Alternative: greater `EXT` improves `REV4_ATR`.

Primary continuous statistic: pair-year-clustered bootstrap slope of `REV4_ATR` on continuous `EXT`.

### H2 — extreme-extension reversal edge

Null: `E3` strong rejections do not have positive executable four-hour reversal expectancy and/or do not outperform low-extension `E0` rejections.

Alternative: `E3` has positive executable expectancy and materially outperforms `E0`.

Primary discrete statistics:

- mean `REV4_ATR` in `E3`;
- `E3 minus E0` mean `REV4_ATR` contrast.

The ordered E0→E1→E2→E3 means are reported as a monotonicity diagnostic but exact monotone ordering is not itself a promotion requirement.

## Primary inference

- pair-year clustered bootstrap;
- 5,000 deterministic draws;
- development: 2015-2019;
- internal validation: 2020-2021;
- 2022-2025: exposed stability only, never relabelled as protected holdout;
- two-sided confidence intervals are reported; promotion uses the preregistered positive-direction lower-bound conditions below.

## Internal promotion gate for extension mechanism

The extension-conditioned reversal mechanism may proceed to fresh 2026 confirmation only if **all** are true:

1. continuous `EXT` slope on `REV4_ATR` is `> 0`;
2. the 95% clustered-bootstrap lower bound of that slope is `> 0`;
3. `E3 minus E0` mean `REV4_ATR` is `> 0`;
4. the 95% clustered-bootstrap lower bound of `E3 minus E0` is `> 0`;
5. mean executable `REV4_ATR` within `E3` is `> 0`;
6. the 95% clustered-bootstrap lower bound of the E3 mean is `> 0`;
7. `E3 minus E0` is positive in both 2015-2019 development and 2020-2021 validation;
8. at least 7/10 pair-level `E3 minus E0` contrasts are positive;
9. a deterministic 4H same-pair/same-reversal-direction cooldown does not reverse the continuous-slope, E3-mean or E3-minus-E0 conclusions.

If any condition fails, 2026 remains sealed and no threshold/bin/session/weekday/indicator rescue is authorized.

## Secondary horizons and path diagnostics

Reported without selection authority:

- executable countertrend return at 1H, 2H and 8H using the same quote-side semantics;
- reversal-direction MFE and MAE over 4H;
- first passage to `+0.5 H1 ATR` countertrend versus `-0.5 H1 ATR` continuation from executable entry;
- median time to first passage;
- descriptive pair, year, session and weekday breadth only.

The 4H horizon remains primary regardless of secondary outcomes.

## Pivot-increment analysis after extension

Pivot location is not allowed to rescue a failed extension mechanism. It is evaluated as an incremental explanatory layer.

For each rejection extreme, reconstruct the unchanged classic Daily pivot geometry used in the parent programme:

- nearest level among S3/S2/S1/PP/R1/R2/R3;
- normalized distance `d` based on spacing to the adjacent pivot in the direction away from the nearest level;
- `S1R1_CORE`: nearest S1/R1 with `d < 0.20`;
- `S2R2_CORE`: nearest S2/R2 with `d < 0.20`;
- `NON_CORE`: all remaining generic strong-rejection events not in either S1/R1 or S2/R2 core.

The specific principal hypothesis is evaluated as:

> After controlling for pre-rejection extension, does S2/R2 proximity add reversal expectancy beyond generic strong rejection at comparable extension?

Frozen extension adjustment:

- create 0.25-Daily-ATR extension strata: `[0,.25), [.25,.50), ... [2.25,2.50), >=2.50`;
- within each pair × calendar year × rejection direction × extension stratum, compare S2/R2-core `REV4_ATR` with NON_CORE `REV4_ATR` where both cohorts exist;
- aggregate the matched stratum differences with observation-count weighting;
- use pair-year clustered bootstrap over the matched-stratum estimator.

Secondary matched contrast: S1/R1 core versus NON_CORE under the identical procedure.

A pivot-specific S2/R2 increment is considered internally supported only if:

1. matched S2/R2 minus NON_CORE effect is `>0`;
2. its 95% clustered-bootstrap lower bound is `>0`;
3. the matched effect is positive in both development and validation.

This pivot-specific result cannot authorize live use if the primary extension promotion gate fails.

## Conditional 2026 confirmation

Only if the full primary extension promotion gate passes may 2026 YTD be opened once for the unchanged extension hypothesis.

The frozen confirmation rule will test:

- the continuous extension slope remains positive;
- `E3 minus E0` remains positive;
- E3 executable reversal expectancy remains positive;
- effect sizes are directionally compatible with historical uncertainty.

The shorter 2026 partition is not required to achieve standalone statistical significance. No parameter may be changed after 2026 is opened.

If the S2/R2 matched incremental gate also passed internally, its sign will be reported on 2026 as a secondary fresh check without changing the primary extension rule.

## Prohibited rescue paths

After outcome inspection, do not:

- alter the 0.75 / 1.25 / 1.75 extension thresholds;
- replace Daily ATR20 with another normalization because it looks better;
- redefine extension from close, swing point, previous close, weekly open or another anchor;
- include dual-strong ambiguous bars;
- select only upper or lower rejections;
- select only S2 or only R2;
- mine session, weekday or pair subsets;
- switch the primary horizon away from 4H;
- add moving averages, trend filters, RSI, COT, range filters or divergence;
- optimize stops or targets;
- expose 2026 after any primary internal gate failure.

## Interpretation boundary

A pass would support a general `far-travelled + strong H1 rejection` reversal mechanism after spread. It would not by itself prove pivots matter.

Only a separately positive extension-matched S2/R2 increment would support the narrower statement that second-order Daily pivots add information beyond extension itself.

A fail means the intuitive `price travelled far, therefore a strong rejection should mean-revert` mechanism does not survive the frozen executable test under this architecture.
