# Daily S1/R1 × H1 Rejection — Continuation-Position Management Preregistration

**Study ID:** `DFXC-20260808-009-pivot-daily-continuation-management`  
**Date frozen:** 2026-08-08  
**Parent evidence:** executable-entry study head `8dc0e390287f57943fb62cba74c023cc8d7f21b3`  
**Dataset:** Dukascopy FX Cash, ten-pair M1 BID/ASK  
**Internal outcome window:** 2015-2025 only  
**Conditional fresh confirmation:** 2026 YTD ending exclusive 2026-07-24; remains unopened unless the internal promotion gate below passes unchanged.

## Decision problem

The prior programme established that strong H1 rejection near Daily S1/R1 carries structural terminal/exhaustion information, but neither immediate nor rejection-candle-break countertrend entry has positive executable expectancy after quoted spread.

This study changes the decision role rather than retuning the failed reversal entry:

> For an existing continuation position already travelling into Daily R1 (long) or S1 (short), does a strong completed H1 rejection provide actionable evidence to exit/reduce continuation exposure rather than continue holding?

This is a position-management event study. It does not assume any particular original entry price. All comparisons begin at the observable post-signal decision time, so prior trade P&L is intentionally treated as sunk.

## Frozen signal

Inherited without retuning:

- Daily classic S1/R1;
- normalized pivot-core proximity `d < 0.20`;
- directional H1 rejection wick fraction `>= 0.30`;
- signal observable only after H1 close;
- NY17 FX trading-day pivots;
- no weekday or session filter;
- R1 signal represents an incoming/upward continuation exposure (existing long);
- S1 signal represents an incoming/downward continuation exposure (existing short).

## Executable decision time

At the first active M1 quote after the completed signal H1:

- existing R1 long can `EXIT_NOW` by selling BID;
- existing S1 short can `EXIT_NOW` by buying ASK.

No synthetic entry cost is added because the position is assumed to pre-exist the management event. This study measures only the incremental value of continuing versus exiting from the decision point onward.

## Primary endpoint

`HOLD4_CONTINUATION_RETURN_ATR` = incremental executable return from choosing to continue the incoming-direction position for 240 contiguous minutes instead of exiting immediately.

- R1 / existing long: `(future_exit_bid - exit_now_bid) / lagged_H1_ATR24`.
- S1 / existing short: `(exit_now_ask - future_exit_ask) / lagged_H1_ATR24`.

Negative values mean `EXIT_NOW` preserves more value than holding continuation exposure.

No weekend/session gap may be bridged. If the horizon cannot be completed contiguously, that endpoint is missing.

## Primary hypotheses

H1 — absolute management value:

- Null: mean S1/R1-core `HOLD4_CONTINUATION_RETURN_ATR >= 0`.
- Alternative: mean `< 0`.

H2 — pivot-specific incremental management value:

- Compare S1/R1 core strong-wick observations with the previously frozen matched S1/R1 outer-zone strong-wick control.
- Null: `core HOLD4 - outer HOLD4 >= 0`.
- Alternative: `< 0`.

A negative core-minus-outer contrast means continuation deteriorates more after rejection near the actual pivot than after a generic strong wick at comparable outer geometry.

## Controls / falsification

1. S1/R1 matched outer-zone strong wick — primary placebo.
2. S2/R2 core strong wick — second-order pivot control.
3. S1/R1 core weak-wick observations, where reconstructible under the unchanged wick threshold — mechanistic control; descriptive unless population alignment is exact.
4. S1 and R1 reported separately; neither may be selected post hoc as a rescue if the pooled gate fails.

## Secondary endpoints

Reported without selection authority:

- HOLD1, HOLD2 and HOLD8 continuation returns;
- incoming-direction maximum favorable excursion after the signal;
- incoming-direction maximum adverse/reversal excursion after the signal;
- probability of +0.5 ATR continuation before -0.5 ATR reversal;
- probability of -0.5 ATR reversal before +0.5 ATR continuation;
- time to those first-passage events;
- session phase retained only as descriptive movement-management context, never as a rescue filter;
- Monday-Friday retained only as descriptive heterogeneity, never as a rescue filter.

## Inference

- Pair-year clustered bootstrap.
- 5,000 deterministic draws.
- Primary inference on HOLD4 absolute core mean and core-minus-outer contrast.
- Development: 2015-2019.
- Internal validation: 2020-2021.
- 2022-2025: exposed stability only; not relabelled as protected holdout.

## Internal promotion gate

A continuation-management rule may proceed to fresh 2026 confirmation only if **all** are true:

1. pooled S1/R1-core HOLD4 mean is negative;
2. its 95% clustered-bootstrap upper bound is `< 0`;
3. core-minus-outer HOLD4 contrast is negative;
4. its 95% clustered-bootstrap upper bound is `< 0`;
5. the pooled core HOLD4 effect is negative in both 2015-2019 development and 2020-2021 validation;
6. at least 7/10 pair-level core HOLD4 effects are negative;
7. a deterministic 4H same-pair/same-direction cooldown does not reverse the conclusion.

If any gate fails:

- do not open 2026 YTD;
- do not optimize management thresholds, sessions, weekdays, wick size, pivot distance, partial-exit percentages or trailing stops;
- record the negative result durably.

If all gates pass:

- freeze the exact `EXIT_NOW versus HOLD4` management rule with no retuning;
- then, and only then, open 2026 YTD once for unchanged fresh confirmation.

## Conditional 2026 confirmation gate

If authorized by the internal gate, 2026 confirms only if:

- S1/R1-core HOLD4 mean remains `< 0`;
- core-minus-outer HOLD4 remains `< 0`;
- no implementation or signal-definition change is made after seeing 2026 outcomes.

No minimum significance threshold is imposed on the shorter 2026 partition; sign consistency and effect-size compatibility with historical uncertainty are the confirmation criteria.

## Prohibited rescue paths

Do not, after outcome inspection:

- switch the primary horizon away from 4H;
- select only S1 or only R1;
- mine London/New York/Tokyo subsets;
- mine weekday combinations;
- change `d < 0.20` or wick `>= 0.30`;
- add trend, MA, range, COT, RSI or divergence filters;
- test partial exits/trailing stops unless the frozen internal promotion gate first passes;
- expose 2026 after an internal gate failure;
- convert this management study into a fresh reversal-entry rescue.

## Interpretation boundary

A pass would support `strong S1/R1 rejection as continuation-risk / exit-management information`, not a standalone reversal entry, not a complete trading strategy, and not live-trading authority.

A fail would mean the structural terminal association still has no demonstrated executable decision value under either fresh reversal entry or simple continuation-position exit management.
