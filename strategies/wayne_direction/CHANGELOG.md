# Wayne Direction-First Framework — Changelog

## v0.8.0 — 2026-07-27

### Changed

- froze the independent FX replication candidate universe before outcomes;
- defined binding annual file, timestamp, BID/ASK alignment, quote-validity, temporal-coverage, spread and activity gates;
- required a committed admitted/excluded panel manifest with source checksums before sequence generation;
- froze independent sample, effect, breadth, concentration and leave-one-pair-out criteria;
- separated the independent-panel estimate from the six-pair development estimate;
- simplified the conditional-layer roadmap to two-year nominal yield differential followed by a VIX-only risk regime;
- explicitly deferred seasonality, full macro-release vintages, real yields, curve models and multi-index stress composites.

### Reason

The day-10 result is too under-sampled to justify a large conditional-data programme. The next decision must establish whether the unchanged technical sequence replicates cross-sectionally. Pair selection and data inclusion therefore need to be frozen before any new Wayne outcomes are visible.

### Known limitations

- the frozen 22-pair candidate inventory has not yet been source-qualified;
- the existing qualified-source workflow is confirmed only for the six development pairs;
- no independent-pair Wayne outcomes are authorized or available;
- 2022–2025 remain locked;
- external yield and VIX outcome testing remains blocked by technical replication.

### Next

- locate or acquire 2015–2021 Dukascopy BID/ASK M1 files for the frozen candidate universe;
- implement and run the source-only qualification manifest;
- freeze the admitted panel before generating sequence outcomes;
- run the exact day-10 replication and independent audit.

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
