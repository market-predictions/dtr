# Stacey Burke Multi-Asset FX Research

This namespace contains a separate research programme for mechanically testable Stacey Burke liquidity concepts. It does not alter DTR, Asian Sweep or Stoic results.

## Final state

Status: **complete — rejected at controlled-study Gate B**

The first research object tested a conditional previous-FX-day high/low sweep-and-reclaim event across a fixed, factor-diverse FX basket.

The event was frequent—2,423 retained events in 2015–2021—but it did not produce a positive control-adjusted 60-minute reversal effect:

- 2,393 matched observable events;
- pooled mean effect `-0.001709 ATR20`;
- 95% date-block interval `[-0.010309, +0.006900]`;
- date-clustered permutation p-value `0.670733`;
- four positive pairs and one positive factor block.

The frozen decision is `FAIL_GATE_B_STOP_STACEY_BURKE_REVERSAL_PROGRAMME`. No SB-1 strategy, validation run, parameter rescue, Pine implementation or deployment is authorized.

## Frozen initial universe

- EURUSD, GBPUSD, USDCHF
- AUDUSD, NZDUSD, USDCAD
- USDJPY, EURJPY, GBPJPY
- EURGBP

All instruments use Dukascopy one-minute BID and ASK data. Source acquisition preserves inactive records and annual immutable hashes.

## Evidence map

- `EVENT_CENSUS_PREREGISTRATION.md` — frozen event and census contract.
- `CONTROLLED_STUDY_PREREGISTRATION.md` — frozen endpoint, matching, inference and gates.
- `FINAL_DECISION.md` — complete results, independent reconstruction and final authorization state.
- `STATUS.md` — concise current status.
- `ROADMAP.md` — completed and cancelled phases.
- `CHANGELOG.md` — version history.