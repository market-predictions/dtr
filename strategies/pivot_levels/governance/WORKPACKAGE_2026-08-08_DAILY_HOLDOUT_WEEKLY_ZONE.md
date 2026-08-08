# Work Package — Daily H1 Holdout + Weekly H4 Zone Geometry

Date: 2026-08-08
Work package: `PIV-WP-20260808-04`
Role: `implementation_operations`
State: `RELEASE_CANDIDATE_READY_ASSURANCE_PENDING`

## Objective

1. Perform one unchanged protected-holdout confirmation of the internally promoted Daily-pivot × H1 wick-rejection interaction.
2. Separately test whether the internally positive but non-promoted Weekly-pivot × H4 wick interaction is sensitive to a principled pivot-zone geometry that accounts for adjacent pivot spacing and/or contemporaneous H4 volatility.

The two objectives are intentionally separated so weekly zone research cannot tune on the Daily/H1 holdout.

## Implementation outcome

- Daily/H1 protected 2022–2025 confirmation: **PASS under the preregistered implementation gate**, interaction +1.084 pp, 95% CI [+0.654,+1.543] pp, 10/10 pairs positive, all years/halves and all leave-one-pair-out pools positive. Decision `CONFIRM_DAILY_H1_PIVOT_WICK_INTERACTION_ON_PROTECTED_HOLDOUT`.
- Weekly/H4 seven-geometry 2015–2021 robustness family: only `SP10` passes the full joint structural + wick gates and material-strength rule. SP10 structural +1.002 pp; wick interaction +1.616 pp, 95% CI [+0.523,+2.686] pp, Holm p=0.0308. Decision `WEEKLY_H4_ZONE_GEOMETRY_MATERIALLY_STRENGTHENS_PIVOT_WICK_INTERACTION`.
- ATR-capped weekly hybrids do not pass the wick gate.
- Daily/H1 2022–2025 holdout is consumed for the exact authorized question. Weekly/H4 2022–2025 outcomes remain uninspected.
- Independent implementation-side arithmetic validation passed. Independent governance assurance remains pending.

## Scientific units

- `DFXC-20260808-003-pivot-daily-wick-holdout` — protected 2022–2025 confirmation.
- `DFXC-20260808-004-pivot-weekly-h4-zone-geometry` — 2015–2021 internal robustness/falsification study.

## Data authority

Canonical source: **Dukascopy FX Cash**, dataset ID `dukascopy_fx_cash_m1_bid_ask_v1`.

Ten pairs: EURUSD, GBPUSD, USDCHF, AUDUSD, NZDUSD, USDCAD, USDJPY, EURJPY, GBPJPY, EURGBP.

The permanent private cache must be reused and archive identity verified before analysis. Raw market data remains private.

## Holdout authorization boundary

The principal explicitly authorized the proposed unchanged Daily→H1 pivot-zone + wick-interaction test on the protected 2022–2025 window on 2026-08-08. This authority applies only to `DFXC-20260808-003-pivot-daily-wick-holdout` and does not authorize weekly zone tuning on 2022–2025.

Authorization record: `strategies/pivot_levels/governance/HOLDOUT_AUTHORIZATION_2026-08-08_DAILY_H1_WICK.md`.

## Scope A — Daily/H1 exact holdout confirmation

Frozen from `DFXC-20260808-002-pivot-wick-rejection`:

- classic daily floor pivots S3/S2/S1/PP/R1/R2/R3 from the prior completed NY17 FX trading day;
- H1 midpoint OHLC;
- nearest-pivot local spacing in the direction of the H1 high/low observation;
- normalized pivot distance `d = abs(extreme - pivot) / local_spacing`;
- pivot core `0 <= d < 0.20`;
- outer matched region `0.30 <= d <= 0.50`;
- directional wick fraction: high-side `(H-max(O,C))/(H-L)` and low-side `(min(O,C)-L)/(H-L)`;
- strong wick `>= 0.30`; weak wick `< 0.10`;
- pivot-blind, wick-blind terminal label from ATR24 simple mean lagged one H1 bar and a 0.75×ATR directional change;
- candidate extreme can be confirmed only on a strictly later H1 candle;
- primary interaction `(core strong - core weak) - (outer strong - outer weak)`;
- structural core-minus-outer terminal effect and wick gradients are secondary diagnostics.

Outcome window: 2022-01-01 through 2025-12-31 by NY17 FX trading date. 2021 may be read only for warm-up and prior-day pivot construction; no 2021 observation contributes to holdout outcomes. No 2026 member may be read.

## Scope B — Weekly/H4 zone-geometry robustness

Only 2015–2021 outcomes are eligible. 2022–2025 weekly/H4 outcomes remain unopened for this hypothesis.

The prior weekly reference zone is purely spacing-relative: core 0–20% of local adjacent weekly-pivot spacing and outer 30–50%. It contains no ATR term.

The frozen seven-geometry family is:

1. `SP10`: half-width `w = 0.10 * spacing`; outer matched band `[0.50*spacing-w, 0.50*spacing]`.
2. `SP15`: `w = 0.15 * spacing`; same matched-control construction.
3. `SP20_REF`: `w = 0.20 * spacing`; exactly reproduces the inherited 0–20% core / 30–50% outer reference.
4. `SP25`: `w = 0.25 * spacing`; matched outer 25–50% band.
5. `HYB_ATR050`: `w = min(0.20*spacing, 0.50*H4_ATR24_lag1)`.
6. `HYB_ATR075`: `w = min(0.20*spacing, 0.75*H4_ATR24_lag1)`.
7. `HYB_ATR100`: `w = min(0.20*spacing, 1.00*H4_ATR24_lag1)`.

For hybrid variants, the matched outer band is `[0.50*spacing-w, 0.50*spacing]`. This keeps core and control widths equal on each observation and prevents ATR widening from crossing the nearest-pivot midpoint. ATR is lagged and pivot-blind.

Both structural terminal effect and pivot-specific wick interaction are evaluated for every geometry. The wick threshold itself is not changed.

## Inference and gates

- 5,000 pair-year clustered bootstrap draws.
- Separate Holm correction across seven structural effects and seven wick-interaction effects.
- Development 2015–2019 and internal validation 2020–2021 must have the same positive sign for a promoted weekly geometry.
- 95% CI lower bound must exceed zero and Holm-adjusted p must be <0.05.
- At least 6/10 pair effects positive and every leave-one-pair-out pooled effect positive.
- For wick promotion, the frozen five-bin core wick gradient must remain non-decreasing.
- A weekly geometry is called **materially stronger than reference** only if its combined wick interaction is at least +1.00 percentage point and at least +0.25 pp above `SP20_REF`.
- If more than one weekly geometry passes all gates, results are reported side-by-side; no pair, pivot level, wick threshold or session is selected post hoc. Any future confirmatory candidate must be frozen before new/fresh data.

## Daily holdout pass contract

The Daily/H1 holdout interaction confirms only if:

- combined 2022–2025 interaction > 0;
- 95% pair-year clustered-bootstrap CI lower bound > 0 and p < 0.05;
- 2022–2023 and 2024–2025 interaction estimates are both > 0;
- at least 6/10 pair interactions are positive;
- every leave-one-pair-out pooled interaction is positive;
- the five frozen core wick bins remain non-decreasing.

The original +0.92 pp internal estimate is not used as a minimum holdout effect threshold.

## Non-scope

- No entry, stop, target, P&L, spread/slippage or execution strategy.
- No Pine/alerts/sizing/deployment.
- No volume or tick-activity filter.
- No pair removal, named-pivot selection, session selection or wick-threshold optimization.
- No weekly/H4 use of 2022–2025 for zone selection.

## Acceptance criteria

- [x] Preregistrations and holdout authorization record committed before outcome computation.
- [x] Exact cache/archive identities verified.
- [x] Daily holdout reads only 2021 warm-up plus 2022–2025 outcome members and no 2026 member.
- [x] Weekly geometry outcomes are only 2015–2021.
- [x] Reference weekly geometry reproduces prior `SP20_REF` results exactly after documented invalidated preliminary runs.
- [x] All seven weekly variants reported, including failures.
- [x] Study/result records, evidence, limitations, authorized next steps and prohibited rescue paths stored in the Dukascopy FX Cash Research Registry.
- [ ] Independent `governance_release_assurance` of the exact candidate before merge.
