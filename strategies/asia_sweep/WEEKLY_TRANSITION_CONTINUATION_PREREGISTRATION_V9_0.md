# Asian Sweep Weekly-Transition Continuation — Preregistration v9.0

Date frozen: 2026-07-26  
Branch: `agent/asia-sweep-weekly-transition-validation`

Discovery used only for hypothesis formation: EURUSD and GBPUSD, 2015–2019  
First untouched confirmation: EURUSD and GBPUSD, 2020–2022  
Final holdout: EURUSD and GBPUSD, 2023–2025

## 1. Why this is a new programme

The preregistered weekly-profile H1/H2 study failed:

- trend resumption after an early-week countertrend retracement underperformed its broader HTF-aligned reference on every target;
- Monday/Tuesday retracement continuation was sparse and negative-EV.

A post-decision descriptive audit exposed a materially different state. From Wednesday onward, after the current week had displaced at least 0.75 ATR against the old structural trend and remained directionally displaced, Asian Sweep trades continuing that developing transition showed positive discovery economics.

This lead had no promotion authority in the H1/H2 programme. It is frozen here before any 2020–2025 outcome is read.

## 2. Discovery evidence — descriptive only

Exact 2015–2019 discovery population:

- `weekly_phase == MIDWEEK_REVERSAL_OR_TRANSITION`;
- proposed T0 trade opposes the old structural trend and therefore continues the developing weekly transition;
- 85 events: 45 EURUSD and 40 GBPUSD.

Descriptive outcomes:

- opposing liquidity by 14:00: 27.06% hit rate, +0.309R mean stressed EV proxy, positive in both pairs and 4 of 5 years;
- fixed 4R by 14:00: 27.06% hit rate, +0.311R, positive in both pairs and 3 of 5 years;
- fixed 3R by 12:00: 28.24% hit rate, +0.094R, positive in both pairs and 4 of 5 years.

For the primary opposing-liquidity target, the broader Wednesday–Friday countertrend-continuation reference contained 139 events, a 20.14% hit rate and -0.032R mean stressed EV. The frozen transition population therefore had +6.91 percentage points hit-rate lift and +0.341R EV lift in discovery.

These figures justify validation only. They are not evidence of an authorized strategy.

## 3. Exact causal population

At the T0 next-active BID/ASK entry:

1. structural trend is `UP` or `DOWN` under the unchanged v8.0 completed-day definition;
2. event weekday is Wednesday, Thursday or Friday (`event_weekday >= 2`);
3. current-week direction remains opposite the structural trend;
4. countertrend excursion from the weekly open is at least `0.75 ATR20`;
5. the unchanged weekly-phase classifier returns `MIDWEEK_REVERSAL_OR_TRANSITION`;
6. proposed sweep trade direction opposes the old structural trend, and therefore aligns with the current weekly displacement;
7. target geometry is valid at T0 under the unchanged adverse stop: `0.20 × Asian range` beyond the sweep extreme.

No threshold, weekday, pair, side, target, stop or phase component may change after validation starts.

## 4. Causal context and warm-up

- daily trend uses completed Amsterdam trading days only;
- current-week context ends strictly before entry;
- the entry/sweep bar and future weekly information are excluded;
- 2019 source may be used only as causal warm-up for 2020;
- 2022 source may be used only as causal warm-up for 2023 after stage one passes;
- warm-up-year outcomes are excluded from the relevant stage.

## 5. Primary target and diagnostics

### Primary promotion target

`EXT_OPPOSING_LIQUIDITY_1400`

- nearest causally confirmed opposing external-liquidity level beyond entry;
- horizon: 14:00 Europe/Amsterdam;
- conservative stop-first same-minute ordering;
- actual BID/ASK next-active T0 entry;
- 0.10-pip adverse entry/stop stress, unchanged from the extended-target programme.

### Frozen corroboration targets

- `EXT_FIXED_4R_1400` — required pooled robustness target;
- `EXT_FIXED_3R_1200` — descriptive corroboration;
- `EXT_OPPOSITE_BOUNDARY_1100` — descriptive corroboration;
- `EXT_FIXED_2R_1100` — descriptive corroboration.

No diagnostic target can rescue failure of the primary target.

## 6. Frozen reference population

For the same target and stage:

- structural trend is directional;
- weekday is Wednesday through Friday;
- current-week direction opposes the structural trend;
- proposed trade opposes the structural trend;
- no 0.75-ATR or weekly-phase requirement.

The transition population is a strict subset of this reference.

## 7. Outcome and inference

Per-row observed stressed EV proxy:

`hit × stressed_reward_risk - (1 - hit)`

A non-hit is treated as -1R. This is conservative and identical to the preceding mechanism contract.

Report:

- event count and positives;
- target hit rate;
- mean stressed EV proxy;
- median stressed reward/risk and breadth at or above 1.25R;
- absolute hit-rate lift versus reference;
- mean-EV lift versus reference;
- pair and year attribution;
- pair/year concentration;
- deterministic calendar-date block bootstrap with 10,000 iterations and seed `20260726`;
- bootstrap probability mean EV is positive and the 10th percentile.

## 8. Stage-one gate — 2020–2022

All predicates must pass for the primary opposing-liquidity target:

- at least 40 events and 10 positives;
- at least 15 events per pair;
- pooled mean stressed EV proxy > 0;
- positive mean stressed EV in both pairs;
- positive mean stressed EV in at least 2 of 3 years;
- target-rate lift versus reference >= +3 percentage points;
- mean-EV lift versus reference >= +0.15R;
- median stressed reward/risk >= 2.50R;
- at least 90% of events retain stressed reward/risk >= 1.25R;
- pair concentration <= 70%;
- year concentration <= 50%;
- bootstrap probability mean EV positive >= 80%;
- 10th bootstrap percentile > -0.10R;
- fixed-4R pooled mean stressed EV proxy > 0.

Decision:

- pass: `PASS_WEEKLY_TRANSITION_CONFIRMATION_OPEN_FINAL_HOLDOUT`;
- fail: `FAIL_WEEKLY_TRANSITION_CONFIRMATION_STOP`.

If any predicate fails, 2023–2025 remains unopened and the programme stops.

## 9. Final-holdout gate — 2023–2025

The exact unchanged rule and targets are applied only after stage one passes.

All predicates must pass:

- at least 40 events and 10 positives;
- at least 15 events per pair;
- pooled mean stressed EV proxy > 0;
- positive mean stressed EV in both pairs;
- positive mean stressed EV in at least 2 of 3 years;
- target-rate lift versus reference >= +3 percentage points;
- mean-EV lift versus reference >= +0.15R;
- median stressed reward/risk >= 2.50R;
- at least 90% retain at least 1.25R;
- pair concentration <= 70%;
- year concentration <= 50%;
- bootstrap probability mean EV positive >= 90%;
- 10th bootstrap percentile > -0.05R;
- fixed-4R pooled mean stressed EV proxy > 0.

Combined 2020–2025 must also have:

- at least 80 events;
- pooled mean stressed EV proxy >= +0.10R;
- positive EV in both pairs;
- positive EV in at least 4 of 6 years;
- bootstrap probability mean EV positive >= 95%;
- fixed-4R pooled mean stressed EV proxy > 0.

Decision:

- pass: `PASS_WEEKLY_TRANSITION_FINAL_HOLDOUT_OPEN_EXECUTION_PNL`;
- fail: `FAIL_WEEKLY_TRANSITION_FINAL_HOLDOUT_STOP`.

## 10. Authorization boundary

A complete final pass authorizes only a separately frozen execution-P&L reconstruction using the primary opposing-liquidity target and 14:00 time exit. It does not authorize Pine, alerts, paper trading, sizing, portfolio use or deployment.

No model fitting, probability threshold, target selection or subgroup search occurs in this programme.