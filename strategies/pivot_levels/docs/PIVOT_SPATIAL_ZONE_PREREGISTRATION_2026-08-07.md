# Pivot Spatial Zone Follow-up — Preregistration

Date: 2026-08-07
Programme: `PIVOT-SPATIAL-ZONE-V1`
Work package: `PIV-WP-20260807-02`
Status at creation: `FROZEN_PRE_OUTCOME`
Parent programme: `PIVOT-TARGET-REVERSAL-V1` / PR #72

## Why this is a new test

The parent study found no exact-coordinate pivot advantage against nearby controls, but those controls were centered at ±25% of local pivot spacing. If the true market object is a broad pivot **zone** rather than an exact line, those controls may have been inside the same influence region. This follow-up tests the spatial extent of pivot influence directly. It may not retrospectively promote or rewrite the parent result.

## Data and sample contract

- Source: registered `Dukascopy FX Cache`; no historical reacquisition.
- Pairs: EURUSD, GBPUSD, USDCHF, AUDUSD, NZDUSD, USDCAD, USDJPY, EURJPY, GBPJPY, EURGBP.
- Source construction: M1 separate BID/ASK UTC; midpoint price for structural analysis.
- H1 causal trend layer and M15 first-passage/reaction layer derived from the same M1 source.
- Development: 2015–2019.
- Internal validation: 2020–2021.
- Holdout: 2022–2025 remains unopened.
- Same New York 17:00 DST-safe FX period boundaries and classic floor-pivot formulas as the parent study.
- Daily/weekly: S3/S2/S1/PP/R1/R2/R3.
- Monthly/quarterly/yearly: principal pivots plus all six adjacent arithmetic midlevels.

## Spatial geometry

For every pivot level, let the left/right spacing be the actual distance to the adjacent tested level on that side. For an outermost level, extrapolate the sole adjacent spacing outward.

### Real pivot zones

Symmetric zone half-widths are preregistered as fractions of the applicable adjacent spacing:

`5%, 10%, 15%, 20%, 25%`.

The **20% half-width** is the primary broad-zone specification. The complete five-width curve is a secondary coherence test. No width may be selected post-outcome as a rescue winner.

### Far midpoint controls

For every side of every real pivot, the far-control center is the midpoint to the adjacent tested pivot, i.e. `50%` of that side's spacing from the real pivot. For an outermost pivot, the control is extrapolated outward by 50% of the sole adjacent spacing.

The far control uses the **same percentage half-width** as the real zone on that side. At the primary 20% width, the real zone and midpoint-control zone are separated by a 10%-of-spacing gap. At 25% they may touch at one boundary but do not overlap.

The purpose is to compare a broad pivot-centered region with an equally wide region clearly outside that pivot core.

## Independent trend state

Retain the parent study's pivot-blind qualified trend definition unchanged:

- five contiguous valid H1 closes spanning four hours;
- absolute four-hour displacement >= `0.75 * ATR24_H1`;
- directional efficiency >= `0.60`;
- close in the outer 20% of the recent four-hour range;
- candidate zone lies in the trend direction;
- candidate zone was not entered in the preceding four hours;
- distance to the near edge of the candidate zone from `0.10` to `0.75 * ATR24_H1`.

## Primary tests — 20% zone

### S1 — Broad-zone trend-endpoint clustering

Use the already independent ATR-ZigZag H1 trend-leg endpoints. For each timeframe, compare endpoint-zone incidence at real 20% pivot zones with equal-width midpoint-control zones.

Primary effect: real incidence minus control incidence, exposure-balanced by parent level and period.

### S2 — Broad-zone target completion

From matched qualified trend states, compare the probability of reaching a real 20% pivot zone before an adverse `0.50 * ATR24_H1` move with the probability of reaching an equal-width midpoint-control zone under the same event-state contract.

### S3 — Broad-zone containment / stall

After first entry into a real or control 20% zone, time inside the zone is neutral. A containment success occurs when the trend-side continuation boundary (zone edge plus `0.25 * ATR24_H1`) is not breached during the same frozen dwell windows as the parent study:

- daily 60m;
- weekly 120m;
- monthly 240m;
- quarterly 360m;
- yearly 480m.

### S4 — Broad-zone reversal before extension

After first zone entry, use symmetric barriers outside the zone:

- reversal: opposite-side zone edge plus `0.25 * ATR24_H1` against incoming trend;
- extension: trend-side zone edge plus `0.25 * ATR24_H1` with incoming trend.

Time inside the zone remains neutral. Observation ends at 24h or active-period expiry.

## Secondary tests — spatial response curve

Repeat S1–S4 descriptively at 5%, 10%, 15%, 20% and 25% half-widths. A genuine broad pivot-zone mechanism should show coherent persistence or strengthening toward 20–25%, not a single isolated favorable width.

No individual secondary-width p-value can promote the hypothesis if the primary 20% specification fails.

## S5 — Continuous distance / occupancy enrichment

This test removes the arbitrary zone boundary.

For every active timeframe/period:

1. assign each valid H1 close to its nearest tested pivot level;
2. normalize absolute distance to that pivot by the spacing to the adjacent level on the side containing price;
3. retain observations from 0% to 50% of spacing (pivot center to midpoint between pivots);
4. bin normalized distance into `0–10, 10–20, 20–30, 30–40, 40–50%`;
5. compute the same normalized-distance distribution for independent H1 trend-leg endpoints.

For each bin, calculate endpoint incidence per H1 occupancy exposure. The primary gradient contrast is endpoint enrichment in `0–20%` versus `30–50%`.

A broad pivot terminal-zone mechanism predicts positive development and validation contrasts and a declining enrichment profile with increasing distance from the pivot.

## Matching and inference

S2–S4 use the parent's matched strata where sample permits:

- pair;
- year;
- timeframe;
- parent level;
- direction;
- four-hour UTC session;
- approach-distance band;
- ATR tercile;
- efficiency band.

Uncertainty uses pair-year-week clustered bootstrap resampling.

- primary S1–S5: 5,000 draws;
- Holm familywise correction across 25 primary hypotheses (`S1–S5` × five timeframes).
- Secondary width curves are descriptive/coherence evidence only and are not separately promoted.

## Promotion gate

A timeframe/mechanism can qualify only if:

1. development and validation primary effects are both positive;
2. combined 95% interval is strictly above zero;
3. Holm-adjusted two-sided p < 0.05;
4. at least 6/10 eligible pairs are positive where pair-level estimation is possible;
5. leave-one-pair-out pooled effects remain positive;
6. the result is not dominated by one level/pair;
7. the secondary width curve is directionally coherent with the primary broad-zone interpretation.

## Restrictions

- No change to pivot formula, period boundary, trend definition, ATR threshold, barrier or dwell definitions after outcomes.
- No pair/session/year/level shopping.
- No opening 2022–2025.
- No execution P&L, Pine, alerts, sizing, paper trading or deployment.
- Null results are preserved. A favorable secondary width cannot rescue a failed 20% primary specification.
