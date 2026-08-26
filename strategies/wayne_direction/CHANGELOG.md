# Wayne Direction-First Framework — Changelog

## v1.0.0 — 2026-07-27

### Changed

- operationalized and reproduced annual Q1-Q6 source gates for the independent FX panel;
- froze EURGBP, EURJPY, GBPJPY and NZDUSD before outcomes;
- reproduced all 28 annual source-quality records in CI against the committed manifest;
- ran the exact unchanged day-10 sequence on the independent panel;
- applied bundle-preserving instrument-month inference, pair concentration and leave-one-pair-out diagnostics;
- independently recomputed every reported count, effect, confidence bound and p-value;
- closed the Wayne direction-first roadmap after the binding independent sample failure.

### Results

- independent active day-10 sequences: 26 versus 80 required;
- available conservative treatments: 14 versus 40 required;
- controls: 447 versus 120 required;
- pairs with at least eight active sequences: 2 versus 4 required;
- pairs with at least five available treatments: 1 versus 4 required;
- conservative: 35.71% versus 12.53%, +23.19 pp, p=0.0990, q=0.0990;
- stretch: 40.00% versus 7.89%, +32.11 pp, p=0.0004, q=0.0008;
- treatment concentration: 57.14% in EURJPY;
- binding decision: `FAIL_INDEPENDENT_REPLICATION_SAMPLE`.

### Reason

The exact technical sequence remained too rare on an independently qualified panel. Four of five frozen sample gates failed. Favorable descriptive reach differences, including the secondary stretch endpoint, cannot replace the preregistered primary endpoint or repair inadequate pair and year breadth.

### Known limitations

- only four independent pairs were available in the frozen qualified-source run;
- only 14 conservative treatment observations remained after causal target-availability rules;
- EURJPY contributed 8 of 14 conservative treatments;
- pair effects outside EURJPY were based on only two treatments each;
- 2022-2025 remain unopened;
- no executable P&L was calculated.

### Next

- keep yields, VIX, macro, seasonality, execution and Pine closed for this research line;
- do not loosen thresholds, substitute the stretch endpoint or consume the chronological holdout;
- redirect research resources to strategies with materially higher event frequency and a clearer executable path;
- treat any future cohort or asset-family study as a new preregistered programme, not sample rescue.

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

The day-10 result was too under-sampled to justify a large conditional-data programme. The next decision had to establish whether the unchanged technical sequence replicated cross-sectionally. Pair selection and data inclusion were therefore frozen before any new Wayne outcomes became visible.

### Known limitations

- the frozen 22-pair candidate inventory had not yet been source-qualified;
- the existing qualified-source workflow was confirmed only for the six development pairs;
- no independent-pair Wayne outcomes were authorized or available;
- 2022-2025 remained locked;
- external yield and VIX outcome testing remained blocked by technical replication.

### Next

- locate or acquire 2015-2021 Dukascopy BID/ASK M1 files for the frozen candidate universe;
- implement and run the source-only qualification manifest;
- freeze the admitted panel before generating sequence outcomes;
- run the exact day-10 replication and independent audit.

## v0.7.0 — 2026-07-27

### Changed

- froze the staged monthly-location -> H4 structure -> H4 MA-health sequence;
- separated close-in-zone primary location from range-touch sensitivity;
- added day-5 primary and day-10 sensitivity landmarks;
- excluded targets consumed before or on confirmation/landmark bars;
- added instrument-month clustered bootstrap and bundle-preserving permutation inference;
- completed six-pair 2015-2021 pair construction and corrected pooled aggregation;
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

The ordered sequence appeared economically discriminating when it completed, especially by day 10, but occurred too rarely on the frozen six-pair development population to support promotion. Sample scarcity had to be resolved through independent replication, not weaker definitions or additional in-sample window search.

### Known limitations

- only 25 day-10 conservative treatment cases remained available at the fixed landmark;
- EURUSD was negative in the day-10 conservative pair breakdown;
- most active opportunities lacked aligned D1 structure, so D1 interaction remained unresolved;
- macro, regime and seasonality outcomes remained untested;
- 2022-2025 remained unopened;
- no executable P&L was calculated.

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
- 2022-2025 remained unopened.

## v0.1.0 — 2026-07-27

### Changed

- replaced the daily-pivot-first hierarchy with direction first, reach second and execution last;
- defined macro, regime, seasonality and D1 structural trend as independent direction layers;
- froze the double-bottom/top -> BOS -> retest -> HL/LH -> continuation structure sequence;
- assigned H4 EMA21/55/200 ordering and divergence to trend-health grading;
- assigned monthly M2-P and P-M3 zones to location;
- assigned monthly M4/R2 and M1/S2 to conservative/stretch reach;
- archived daily-pivot PR #63 as a bounded negative result rather than an active dependency;
- opened work package `WP-WD-20260727-01`.
