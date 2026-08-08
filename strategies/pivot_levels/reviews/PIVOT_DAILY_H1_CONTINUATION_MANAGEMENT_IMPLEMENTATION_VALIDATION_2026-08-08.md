# Implementation Validation — Daily S1/R1 Continuation Management

Study: `DFXC-20260808-009-pivot-daily-continuation-management`

## Scope

Validate that the continuation-position management study implements the frozen decision problem without changing the signal, quote-side semantics, horizon, holdout boundary or overlap rules.

## Checks

### Preregistration ordering

- Dedicated branch created from exact parent execution-study head `8dc0e390287f57943fb62cba74c023cc8d7f21b3`.
- Preregistration committed at `39f5bfe5f59fabe42418ee4eeb3da896ff75df3e` before management-outcome inspection.
- 2026 YTD was not opened.

### Signal population

The inherited 2015-2025 strong-wick event ledger was reused without retuning:

- S1/R1 core: 68,118 observations;
- S1/R1 matched outer: 93,309;
- S2/R2 core: 18,583.

No session, weekday, pair or named-level selection was applied.

### Executable quote-side semantics

At the post-H1 decision time:

- R1 incoming long liquidation uses BID;
- S1 incoming short liquidation uses ASK;
- future HOLD exits use the same executable liquidation side;
- no synthetic entry spread is charged because the tested position pre-exists the management event.

The management decision price matches the already-audited parent executable countertrend-entry price exactly on all 64,733 jointly valid S1/R1-core HOLD4 observations; maximum absolute error 0.0.

### Direct-source audit

Twenty randomly sampled 2024 observations from S1/R1 core/outer cohorts were rebuilt directly from the original private Dukascopy BID and ASK archive members.

- maximum decision-price absolute error: 0.0;
- maximum HOLD4 return absolute error: 0.0.

### Time/gap semantics

- decision occurs only after the completed signal H1;
- each requested horizon requires active quotes in every constituent clock-hour segment;
- endpoint requires an active quote within the final ten minutes;
- no weekend or year-boundary gap is bridged;
- 2025 observations requiring 2026 data are missing rather than extended into the reserved partition.

### Inference

- primary horizon: 4H, unchanged after outcome inspection;
- 5,000 deterministic pair-year clustered-bootstrap draws;
- development 2015-2019, validation 2020-2021, exposed stability 2022-2025;
- 4H same-pair/same-direction cooldown used only as preregistered robustness.

## Validation conclusion

`PASS_IMPLEMENTATION / SCIENTIFIC_GATE_FAIL`

The implementation is fit to support the recorded negative scientific decision. It does not authorize a management rule, 2026 holdout exposure, optimization, Pine, alerts, sizing or live trading. Independent `governance_release_assurance` remains separate and pending.
