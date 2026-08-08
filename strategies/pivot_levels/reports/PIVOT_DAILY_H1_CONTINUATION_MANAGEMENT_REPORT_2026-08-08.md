# Daily S1/R1 × H1 Rejection — Continuation-Position Management Study

**Study:** `DFXC-20260808-009-pivot-daily-continuation-management`  
**Dataset:** Dukascopy FX Cash, ten pairs, M1 BID/ASK  
**Internal sample:** 2015-2025  
**2026 YTD:** **not opened**

## Executive conclusion

The proposed `EXIT_NOW` management rule fails its preregistered gate.

For an existing continuation position already moving into Daily R1 (long) or S1 (short), a strong completed H1 rejection does **not** make the next four hours of continuation expectancy negative. The S1/R1-core mean HOLD4 continuation return is **+0.0050 ATR**, 95% pair-year clustered-bootstrap CI **[-0.0094,+0.0189]**.

Matched outer-zone strong-wick continuation is stronger at **+0.0156 ATR**, so the pivot core is directionally weaker by **-0.0106 ATR**. But that contrast is not statistically robust: 95% CI **[-0.0302,+0.0089]**.

Decision:

`REJECT_EXIT_NOW_MANAGEMENT_RULE_NO_ABSOLUTE_OR_PIVOT_SPECIFIC_4H_EDGE`

Because the internal promotion gate fails, 2026 remains sealed and no partial-exit, trailing-stop, session, weekday or threshold optimization is authorized.

## Frozen management decision

At the first active M1 quote after the signal H1 closes:

- R1 rejection represents an existing long continuation position; `EXIT_NOW` liquidates at BID.
- S1 rejection represents an existing short continuation position; `EXIT_NOW` liquidates at ASK.
- `HOLD4` keeps that incoming-direction position for 240 contiguous minutes and then liquidates on the same executable side.

This deliberately ignores the original trade entry and measures only the incremental value of holding versus exiting from the rejection event onward.

## Primary result

| Cohort | Valid HOLD4 observations | Mean continuation return | 95% CI |
|---|---:|---:|---:|
| S1/R1 core strong wick | 64,733 | **+0.0050 ATR** | **[-0.0094,+0.0189]** |
| S1/R1 matched outer strong wick | 89,956 | **+0.0156 ATR** | **[+0.0031,+0.0279]** |
| S2/R2 core strong wick | 17,341 | **+0.0128 ATR** | **[-0.0127,+0.0381]** |
| Core minus outer | — | **-0.0106 ATR** | **[-0.0302,+0.0089]** |

The strong rejection therefore does not justify a universal immediate exit. The relative slowdown near S1/R1 is suggestive but too weak and unstable to establish pivot-specific management value.

## Stability

S1/R1-core HOLD4 continuation return:

- 2015-2019 development: **+0.0029 ATR**;
- 2020-2021 validation: **+0.0220 ATR**;
- 2022-2025 exposed stability: **-0.0012 ATR**.

Only **3/10 pairs** have negative pooled core HOLD4 continuation return.

Named levels are inconsistent and are descriptive only:

- S1: **-0.0088 ATR**;
- R1: **+0.0180 ATR**.

The preregistration explicitly prohibited selecting one side as a rescue after pooled failure.

## Horizon shape

The S1/R1-core mean continuation return remains non-negative at every frozen horizon:

- 1H: **+0.0074 ATR**;
- 2H: **+0.0050 ATR**;
- 4H: **+0.0050 ATR**;
- 8H: **+0.0143 ATR**.

Core-minus-outer is negative at 1H, 2H and 4H, but reverses positive by 8H (**+0.0131 ATR**). This does not support a durable terminal/exit rule.

## Path evidence

Over the next four hours, S1/R1-core continuation-direction MFE averages **1.130 ATR** and adverse/reversal excursion averages **1.116 ATR**. A +0.5 ATR continuation threshold is reached first in **48.87%** of valid observations, while a -0.5 ATR reversal threshold is reached first in **47.85%**. The path is close to symmetric rather than showing a strong post-rejection collapse in continuation.

## Cooldown robustness

A deterministic 4H same-pair/same-direction cooldown reduces the core sample to **42,870** observations but leaves mean continuation positive at **+0.0051 ATR**, CI **[-0.0092,+0.0191]**. Core-minus-outer remains negative but borderline, CI ending just above zero.

Repeated/overlapping observations therefore do not conceal an exit edge.

## Implementation validation

- 20 randomly sampled 2024 observations were rebuilt directly from the original private Dukascopy BID/ASK archive members: maximum decision-price error **0.0**, maximum HOLD4-return error **0.0**.
- On all 64,733 jointly valid S1/R1-core observations, the management decision price exactly equals the already-audited executable countertrend-entry price from the parent study, as expected because exiting the existing continuation position uses the same quote side. Maximum error **0.0**.

## Strategic interpretation

The pivot programme now has a sharper boundary:

1. strong H1 rejection near Daily S1/R1 has structural terminal/exhaustion information;
2. it does not support a positive-expectancy fresh reversal entry after real spread;
3. it also does not support a simple universal `exit continuation now` rule over the next four hours.

The evidence may still justify treating the event as **reduced continuation confidence**, but not as a deterministic exit instruction. Any future work should change the market question materially rather than optimize this failed rule.

## Holdout state

2026 YTD ending exclusive 2026-07-24 was **not opened** because the internal gate failed. It remains available for a future genuinely frozen hypothesis.
