# Work Package — Daily H1 Executable Entry Architecture

ID: `PIV-WP-20260808-08`  
Study: `DFXC-20260808-008-pivot-daily-execution-entry`  
Role: `implementation_operations`  
State: `IMPLEMENTATION_COMPLETE_ASSURANCE_PENDING`

## Objective

Determine whether the established Daily S1/R1 + strong H1 rejection state can be converted into a positive-expectancy executable countertrend entry after real Dukascopy BID/ASK spread by requiring a frozen rejection-candle confirmation.

## Scope

- reuse permanent Dukascopy FX Cash cache only;
- preserve S1/R1, d<0.20 and wick>=30% definitions;
- compare immediate executable entry with four-hour rejection-candle confirmation;
- fixed 240-minute exit solely to isolate entry quality;
- pair-year clustered inference;
- matched outer and S2/R2 falsification controls;
- keep 2026 YTD unopened.

## Acceptance criteria

- pre-outcome preregistration committed;
- executable BID/ASK semantics deterministic;
- 2015-2025 run complete across ten pairs;
- primary gate evaluated without rescue tuning;
- source audit and parent-midpoint reconciliation recorded;
- negative findings and prohibited next actions durable;
- registry/index/changelog updated;
- exact-head CI green;
- independent assurance required before closeout/merge.

## Outcome

Frozen promotion gate **FAILED** because confirmation expectancy is negative (-0.0822 ATR, 95% CI [-0.0978,-0.0659]) despite a statistically significant +0.0174 ATR improvement versus immediate entry. Matched outer-zone confirmation improves more than pivot core, rejecting a pivot-specific executable confirmation mechanism.

Decision: `REJECT_CONFIRMATION_AS_STANDALONE_EXECUTABLE_EDGE_DO_NOT_OPTIMIZE_EXITS`.

## Holdout

2026 YTD ending exclusive 2026-07-24 remains unopened.

## Next authorized direction

A new, separately preregistered study may test S1/R1 strong rejection as continuation-risk / position-management information. Stop/target rescue optimization of the failed reversal-entry architecture is prohibited.