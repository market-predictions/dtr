# Daily S1/R1 × H1 Rejection — Executable Entry Architecture Study

**Study:** `DFXC-20260808-008-pivot-daily-execution-entry`  
**Date:** 2026-08-08  
**Dataset:** Dukascopy FX Cash — ten pairs, M1 BID/ASK  
**Outcome window inspected:** 2015–2025 only  
**Reserved fresh data:** 2026 YTD ending exclusive 2026-07-24 — **not opened**

## Executive conclusion

The confirmation-entry hypothesis fails the frozen promotion gate.

Waiting for a break of the completed H1 rejection candle in the reversal direction produces a statistically real improvement versus immediate next-H1 execution, but **does not produce positive executable expectancy**. More importantly, the improvement is not special to the S1/R1 pivot core: matched S1/R1 outer-zone strong-wick controls improve even more.

Decision:

`REJECT_CONFIRMATION_AS_STANDALONE_EXECUTABLE_EDGE_DO_NOT_OPTIMIZE_EXITS`

Scientific disposition: `REJECT_MECHANISM`.

This study therefore does **not** authorize the planned stop/target optimization phase. The correct interpretation is that candle-break confirmation acts mainly as a generic abstention/delay filter, while the observed Daily S1/R1 structural terminal association does not currently translate into a positive-expectancy countertrend entry after real quoted spread.

## Frozen test

Signal definitions were inherited unchanged from the accepted structural programme:

- Daily classic S1/R1;
- normalized pivot-core proximity `d < 0.20`;
- directional H1 rejection wick fraction `>= 0.30`;
- signal observable only after H1 close;
- NY17 FX trading-day pivots;
- no weekday or session filter.

Two entry architectures were compared:

1. **Immediate:** first active M1 quote in the next H1 period; long at ASK, short at BID.
2. **Confirmation:** within four contiguous hours, long only when ASK reaches the rejection H1 high or short only when BID reaches the rejection H1 low; unconfirmed valid signals receive zero strategy return.

Both architectures use a fixed 240-minute post-entry exit solely to isolate entry quality. Long exits sell BID; short exits buy ASK. No stop/target family was inspected.

## Primary population

- frozen S1/R1 core signals: **68,118**;
- jointly evaluable immediate + confirmation signals: **64,267** (**94.35%**);
- confirmation trigger rate on jointly valid signals: **78.99%**;
- confirmed trades: **50,765**.

Confirmation timing is fast:

- 25th percentile: **1 minute**;
- median: **12 minutes**;
- 75th percentile: **50 minutes**;
- 90th percentile: **117 minutes**.

So the confirmation rule is not mainly waiting several hours; most triggers occur early after the rejection candle closes.

## Primary executable result

All returns are normalized by the signal H1 lagged ATR24.

| Architecture / contrast | Mean per signal | 95% pair-year bootstrap CI |
|---|---:|---:|
| Immediate executable entry | **-0.0996 ATR** | **[-0.1150, -0.0826]** |
| Confirmation, including zero for valid non-trigger | **-0.0822 ATR** | **[-0.0978, -0.0659]** |
| Confirmation minus immediate | **+0.0174 ATR** | **[+0.0084, +0.0262]** |

The confirmation-minus-immediate improvement is statistically robust, but the confirmation strategy remains decisively below zero.

Among trades that actually confirm, mean return is **-0.1041 ATR** and only **45.0%** finish positive after the fixed four-hour hold.

This means the better per-signal result comes primarily from **not trading roughly 21% of signals**, not from turning confirmed entries into profitable trades.

## Promotion gate

The preregistered rule required every gate to pass before any stop/target optimization.

| Gate | Result |
|---|---|
| Full-sample confirmation-minus-immediate > 0 | PASS |
| 95% CI lower bound for architecture difference > 0 | PASS |
| Confirmation expectancy > 0 with CI lower bound > 0 | **FAIL** |
| Difference positive in development and validation | PASS |
| Pair-concentration gate | Not applicable because aggregate confirmation return is negative |

**Overall promotion gate: FAIL.**

Per the preregistration, stop/target optimization is therefore prohibited for this exact confirmation architecture.

## Stability

| Partition | Immediate | Confirmation per signal | Difference | Confirmation rate |
|---|---:|---:|---:|---:|
| 2015–2019 development | -0.0867 | -0.0716 | +0.0150 | 78.41% |
| 2020–2021 validation | -0.1190 | -0.0842 | +0.0347 | 78.80% |
| 2022–2025 exposed stability | -0.1059 | -0.0945 | +0.0113 | 79.82% |

The improvement is positive in all three broad partitions, 8/10 pairs and 10/11 individual years. This is why the loss-reduction effect should be regarded as real rather than noise. But its level remains economically negative in every broad partition.

S1 and R1 separately also remain negative:

- **S1:** immediate -0.0872 ATR; confirmation -0.0689 ATR; +0.0183 ATR improvement; confirmed trades -0.0873 ATR.
- **R1:** immediate -0.1113 ATR; confirmation -0.0947 ATR; +0.0166 ATR improvement; confirmed trades -0.1198 ATR.

Neither side supplies a hidden positive-expectancy rescue.

## Falsification controls: is the confirmation uplift pivot-specific?

No.

Using the same executable confirmation logic on the preregistered controls:

| Cohort | Immediate | Confirmation per signal | Improvement | Confirmed-trade mean |
|---|---:|---:|---:|---:|
| **S1/R1 core** | -0.0996 | -0.0822 | **+0.0174** | -0.1041 |
| S1/R1 matched outer zone | -0.1050 | -0.0743 | **+0.0307** | -0.0931 |
| S2/R2 core | -0.1149 | -0.0959 | **+0.0190** | -0.1250 |

The matched S1/R1 outer-zone improvement is positive in 10/10 pairs and is **larger** than the S1/R1 pivot-core improvement.

Clustered core-minus-outer confirmation-uplift contrast:

- estimate: **-0.0134 ATR**;
- 95% CI: **[-0.0252, -0.0014]**;
- two-sided bootstrap sign-mass p ≈ **0.027**.

Core minus S2/R2 uplift is approximately **-0.0016 ATR**, CI spanning zero.

Therefore the architecture improvement is best interpreted as a **generic strong-wick candle-break abstention effect**, not evidence that first-order daily pivots uniquely improve executable reversal entry.

## Spread / parent-study reconciliation

A critical validation check reconciles the earlier midpoint study with the new executable result on the exact jointly valid signal population:

- parent midpoint FWD4 mean: **-0.0123 ATR**;
- executable immediate mean: **-0.0996 ATR**;
- execution-minus-midpoint: **-0.0873 ATR**;
- mean observed entry spread: **0.0842 ATR**;
- correlation of midpoint and executable signal returns: **0.9981**.

The sharp deterioration is therefore not a contradictory signal-engine result. It is overwhelmingly consistent with the cost of crossing the real BID/ASK spread at entry and exit. The structural signal's small raw directional tendency is simply far too small to overcome execution friction.

## Path diagnostics

Average four-hour excursion after executable entry:

- immediate: MFE **1.023 ATR**, MAE **1.226 ATR**;
- confirmed trades: MFE **1.038 ATR**, MAE **1.268 ATR**.

Confirmation does not create a favorable excursion asymmetry; adverse excursion remains larger on average.

A frozen 4H same-pair/same-direction cooldown robustness check reduces the sample to **42,608** signals and leaves the conclusion intact:

- immediate: **-0.0969 ATR**;
- confirmation: **-0.0789 ATR**;
- improvement: **+0.01795 ATR**, 95% CI **[+0.00730, +0.02806]**;
- confirmed-trade mean: **-0.1017 ATR**.

Repeated/overlapping signals are therefore not hiding a positive edge.

## Implementation validation

A separate direct-source audit rebuilt 20 randomly selected 2024 observations from the original private Dukascopy BID/ASK CSV members rather than the generated execution ledger.

- immediate-return maximum absolute error: **0.0**;
- confirmation-return maximum absolute error: **0.0**;
- confirmation-trigger matches: **20/20**.

The parent midpoint/executable reconciliation provides an additional population-wide validity check.

## Strategic interpretation

The research programme has now separated three facts that should not be conflated:

1. **Structural:** strong rejection near Daily S1/R1 carries terminal/exhaustion information.
2. **Directional:** this does not imply a reliable immediate four-hour countertrend return.
3. **Executable:** after real BID/ASK spread, neither immediate entry nor rejection-candle confirmation has positive expectancy.

The current evidence therefore argues against treating `Daily S1/R1 + strong H1 rejection` as a standalone reversal-entry strategy.

A more coherent possible use is as **position-management / continuation-risk information**: a trader already riding the move into S1/R1 may have evidence to reduce continuation expectations or manage an existing position, even though opening a fresh countertrend trade is not supported. That is a genuinely different decision problem and would require a new preregistered study rather than rescuing this failed entry rule.

## Holdout state

**2026 YTD was not opened.**

It remains available for a future completely frozen hypothesis. Because the reversal-entry architecture failed internally, spending that fresh partition on stop/target optimization would be scientifically wasteful.

## Prohibited interpretation

Do not:

- optimize stops/targets for this confirmation architecture;
- mine session or weekday subsets;
- alter the four-hour confirmation window or wick threshold;
- select S1 or R1 alone as a rescue;
- claim pivot-specific executable confirmation edge;
- build Pine alerts or live rules from this study.

## Recommended next research direction

If the pivot programme continues, the next clean question should change the **decision role**, not retune the failed reversal entry:

> Does a strong H1 rejection at Daily S1/R1 provide actionable information for **exiting, reducing, or avoiding continuation exposure** in the direction of the incoming move?

That hypothesis directly matches the proven structural terminal-hazard effect and does not require assuming that terminal behavior must immediately become a countertrend reversal.
