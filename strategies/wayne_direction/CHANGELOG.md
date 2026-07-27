# Wayne Direction-First Framework — Changelog

## v0.4.0 — 2026-07-27

### Changed

- corrected continuation confirmation to exceed the full pre-retest impulse extreme;
- reran the six-pair D1 census under the corrected definition;
- implemented the same frozen structural sequence on completed H4 bars;
- implemented causal month-open sampling of D1 state, H4 state and H4 EMA health;
- added separate H4 transition and monthly-alignment sample gates;
- completed the authoritative D1 correction and H4 sensitivity workflows;
- recorded the staged interpretation of monthly location, H4 turn and later MA expansion.

### Results

- corrected D1 census: 79 transitions; sample gate failed; 69 of 79 had healthy aligned H4 averages at confirmation;
- H4 census: 475 transitions; transition-count gate passed across all six pairs;
- healthy aligned H4 averages at H4 confirmation: 176 of 475;
- monthly-zone months: 486;
- simultaneous aligned structure plus healthy MAs at month open: zero;
- simultaneous month-open conjunction rejected.

### Reason

Monthly pivot location and healthy H4 trend conditions represent different stages of a pullback-and-resumption process. Requiring them at the same timestamp removes the entire intended opportunity population.

### Known limitations

- the staged zone → H4 structure → MA expansion sequence is not yet frozen or tested;
- macro and policy-regime point-in-time sources remain unqualified;
- seasonality remains unimplemented;
- monthly reach results are descriptive and not executable P&L;
- 2022–2025 remain unopened.

### Next

- freeze and test the staged technical sequence;
- require target reach after, not before, completed confirmation;
- build expanding-window seasonality;
- qualify point-in-time macro and regime data;
- combine only after each layer has independent sample and attribution.

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

- macro and policy-regime point-in-time sources were not qualified;
- structural thresholds had not yet been evaluated on real data;
- H4 divergence and monthly reach were not yet implemented;
- the first stage was attribution, not executable P&L;
- 2022–2025 remained unopened.
