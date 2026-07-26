# Wayne Direction-First Framework — Changelog

## v0.1.0 — 2026-07-27

### Changed

- replaced the daily-pivot-first hierarchy with direction first, reach second and execution last;
- defined macro, regime, seasonality and D1 structural trend as independent direction layers;
- froze the double-bottom/top → BOS → retest → HL/LH → continuation structure sequence;
- assigned H4 EMA21/55/200 ordering and divergence to trend-health grading;
- assigned monthly M2–P and P–M3 zones to location;
- assigned monthly M4/R2 and M1/S2 to conservative/stretch reach;
- archived daily-pivot PR #63 as a bounded negative result rather than an active dependency;
- opened work package `WP-WD-20260727-01`.

### Reason

Direction must exist before monthly pivot levels can be interpreted as opportunity and reach. Testing levels without the methodology's directional framework answers a narrower and less important question.

### Known limitations

- macro and policy-regime point-in-time sources are not yet qualified;
- the structural thresholds are frozen but not yet evaluated on real data;
- H4 divergence and monthly reach are not yet implemented;
- the first stage is attribution, not executable P&L;
- 2022–2025 remain unopened.

### Next

- implement the D1 structural state machine;
- add synthetic causal tests;
- construct DST-safe D1/H4/monthly bars;
- build the first six-pair structural event census;
- then attach H4 health and monthly reach.
