# Wayne Direction-First Framework — Changelog

## v1.0.0 — 2026-07-27

### Changed

- opened a separate stacked work package for independent day-10 replication;
- froze EURGBP, EURJPY, GBPJPY and NZDUSD before outcome access;
- added source-only qualification for exact calendar coverage, BID/ASK agreement, OHLC validity, spreads and New York D1/H4 coverage;
- qualified all four pairs without using Wayne outcomes;
- ran the exact unchanged monthly-location → H4 structure → H4 MA-health sequence;
- added a four-pair replication decision gate with cluster-preserving inference;
- independently audited treatment availability, pair/year breadth, permutation and bootstrap results;
- kept yield, VIX, seasonality, full macro and execution closed.

### Results

- independent primary opportunities: 514;
- active day-10 sequences: 26;
- clean conservative treatments: 14;
- controls: 447;
- conservative reach: 35.71% versus 12.53%;
- conservative lift: +23.19 pp;
- cluster p=0.0948;
- bootstrap 90% interval: +1.48 to +43.70 pp;
- stretch supportive lift: +32.11 pp, p=0.0002;
- binding decision: `FAIL_REPLICATION_SAMPLE_INSUFFICIENT`.

### Reason

The positive effect direction reproduced outside the original six-pair panel, but the exact setup remained too sparse after causal target availability. The conservative treatment sample missed its frozen minimum by one, EURJPY exceeded the concentration ceiling, and pair/year breadth did not pass.

### Known limitations

- only 14 clean conservative treatment observations remained;
- twelve active sequences had conservative targets consumed before or on the observation boundary;
- only EURJPY was eligible for a pair-level conservative effect;
- only three years were eligible and one was negative;
- the strong stretch endpoint was supportive only and cannot rescue the primary endpoint;
- 2022–2025 remain unopened;
- no P&L or execution evidence exists.

### Next

- choose between stopping the sparse technical line or authorizing one final preregistered independent pair panel;
- do not change the sequence, window, target or target-availability rules;
- open two-year yield and VIX attribution only after a technical replication pass;
- keep seasonality, full macro and deployment postponed.

## v0.7.0 — 2026-07-27

### Changed

- froze the staged monthly-location → H4 structure → H4 MA-health sequence;
- separated close-in-zone primary location from range-touch sensitivity;
- added day-5 primary and day-10 sensitivity landmarks;
- excluded targets consumed before or on confirmation/landmark bars;
- added instrument-month clustered bootstrap and bundle-preserving permutation inference;
- completed six-pair 2015–2021 pair construction and corrected pooled aggregation;
- added independent audit, decision record and replication roadmap.

### Results

- primary close-in-zone opportunities: 764;
- active sequences by day 5: 15;
- active sequences by day 10: 36;
- day-5 conservative: 45.45% versus 18.08%, +27.37 pp, p=0.1192, q=0.1589;
- day-10 conservative: 48.00% versus 12.31%, +35.69 pp, p=0.0002, q=0.0008;
- primary and sensitivity sample gates both failed;
- binding decision: `FAIL_STAGED_SEQUENCE_PRIMARY_SAMPLE`.

### Reason

The ordered sequence appears economically discriminating when it completes, especially by day 10, but occurs too rarely on the frozen six-pair development population to support promotion. Sample scarcity must be resolved through independent replication, not weaker definitions or additional in-sample window search.

### Known limitations

- only 25 day-10 conservative treatment cases remained available at the fixed landmark;
- EURUSD was negative in the day-10 conservative pair breakdown;
- most active opportunities lacked aligned D1 structure, so D1 interaction remains unresolved;
- macro, regime and seasonality outcomes remain untested;
- 2022–2025 remain unopened;
- no executable P&L has been calculated.

### Next

- freeze and qualify a broader independent liquid-FX panel;
- replicate the exact day-10 sequence without threshold changes;
- allow point-in-time macro/regime data engineering in parallel;
- keep direction integration, execution and deployment blocked.

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

- the staged sequence had not yet been tested;
- macro and policy-regime point-in-time sources remained unqualified;
- seasonality remained unimplemented;
- monthly reach results were descriptive and not executable P&L;
- 2022–2025 remained unopened.

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
