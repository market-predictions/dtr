# Wayne Direction-First Research Roadmap

Updated: 2026-07-27

## Current state

`PHASE_E_PANEL_PREREGISTERED_DATA_QUALIFICATION_NEXT`

## Phase A — Direction contract

Status: `COMPLETE`

- macro, regime, seasonality and structure are separate direction layers;
- daily pivots cannot create direction;
- D1 structure is slow strategic context;
- H4 structure is the current technical transition;
- H4 EMA21/55/200 grades health;
- monthly pivots define location and reach.

## Phase B — D1 strategic structure

Status: `COMPLETE_REFERENCE_FAILED_SAMPLE_GATE`

- causal double-bottom/top → BOS → retest → HL/LH → continuation engine;
- continuation exceeds the complete pre-retest impulse;
- six pairs, 2015–2021;
- 79 complete transitions;
- 69 of 79 had aligned healthy H4 averages at confirmation;
- retain unchanged as strategic regime context;
- do not loosen thresholds to manufacture sample.

Primary record: `D1_STRUCTURE_CENSUS_CORRECTION_V0_2_1.md`.

## Phase C — H4 structure and health

Status: `COMPLETE_TRANSITION_GATE_PASS_SIMULTANEOUS_GATE_FAIL`

- 475 complete H4 transitions;
- all six pairs exceeded 40 events;
- 176 of 475 had healthy aligned H4 averages at confirmation;
- zero of 486 monthly-zone months were simultaneously aligned and healthy at the exact month open;
- simultaneous conjunction rejected;
- H4 thresholds remain frozen.

Primary record: `H4_STRUCTURE_SENSITIVITY_DECISION_V0_4.md`.

## Phase D — Staged monthly sequence

Status: `COMPLETE_PRIMARY_AND_SENSITIVITY_SAMPLE_FAIL`

Frozen sequence:

1. month opens or H4 closes in the directional monthly zone within five pivot days;
2. a new H4 structural turn follows;
3. EMA21/55/200 becomes aligned stable or expanding;
4. reach begins only after completed confirmation or a fixed landmark.

Results:

- primary close-in-zone opportunities: 764;
- active day-5 sequences: 15;
- active day-10 sequences: 36;
- day-5 conservative lift: +27.37 pp, p=0.1192, q=0.1589;
- day-10 conservative lift: +35.69 pp, p=0.0002, q=0.0008;
- both frozen sample gates failed;
- binding decision: `FAIL_STAGED_SEQUENCE_PRIMARY_SAMPLE`.

Consequences:

- reject day 5 as a promotable technical gate on the current population;
- retain the exact day-10 sequence as an unchanged replication candidate;
- do not weaken structure, MA health or target-availability rules;
- do not extend the in-sample window again;
- do not open direction-layer integration or execution.

Primary record: `STAGED_MONTHLY_SEQUENCE_DECISION_V0_7.md`.

## Phase E — Independent day-10 replication

Status: `PANEL_PREREGISTERED_DATA_QUALIFICATION_NEXT`

Primary record: `INDEPENDENT_FX_REPLICATION_PREREGISTRATION_V0_8.md`.

Frozen scope:

- qualify an independent broader panel of liquid FX pairs before opening outcomes;
- use the preregistered 22-pair candidate inventory;
- admit pairs only through annual file completeness, timestamp integrity, BID/ASK alignment, quote validity, temporal coverage, spread plausibility and activity gates;
- freeze the admitted-panel manifest and source checksums before generating Wayne outcomes;
- reuse the exact close-in-zone, H4 structure, EMA health and day-10 definitions;
- retain conservative and stretch targets unchanged;
- preserve instrument-month clustering and complete bull/bear treatment bundles;
- treat current six-pair results as development evidence only;
- preserve 2022–2025 as locked chronological confirmation, not sample rescue.

No new pair outcome may be viewed until the expanded-panel manifest and data-quality gate are frozen.

The next operational steps are:

1. identify or acquire 2015–2021 Dukascopy BID/ASK M1 files for the frozen candidate inventory;
2. build a source-only qualification runner and manifest;
3. freeze admitted and excluded pairs with reasons and checksums;
4. run the unchanged replication only on the frozen admitted panel;
5. apply the preregistered sample, effect, breadth and leave-one-pair-out gates;
6. commission an independent no-panel-shopping audit.

## Phase F — Minimal external context

Status: `BLOCKED_BY_TECHNICAL_REPLICATION`

Only if Phase E passes, introduce two simple external variables in sequence.

### F1 — Two-year nominal yield differential

- base-currency two-year yield minus quote-currency two-year yield;
- current differential plus frozen 20-day change;
- optionally retain a predeclared 60-day stability diagnostic without optimization;
- classify as supports base, supports quote, neutral or conflicted;
- test independently before combining with another context layer.

### F2 — Simple VIX risk regime

- use VIX only in the first risk-regime version;
- use expanding historical percentiles and recent change;
- classify as risk-on, neutral, risk-off or volatility shock;
- test independently from yields;
- do not build a broad stress-index or cross-asset model in this phase.

No full macro-release database, economic-surprise model, real-yield model or term-structure model is authorized here.

## Phase G — Simple permission triage

Status: `BLOCKED`

Only if at least one Phase F layer adds stable information without collapsing sample:

- technical sequence complete;
- yield state supportive or neutral;
- risk state compatible or neutral;
- otherwise classify as conflicted or abstain.

Initial outputs:

- `PERMITTED`;
- `CONFLICTED`;
- `ABSTAIN`.

No weighted-score optimization in the first triage model.

## Phase H — Deferred research

Status: `DEFERRED_NOT_ON_CRITICAL_PATH`

Explicitly postponed:

- expanding-window seasonality;
- week-of-month and turn-of-month models;
- CPI, employment, GDP and retail-release vintages;
- historical consensus-surprise databases;
- central-bank language models;
- real-yield differentials;
- 10-year yield and curve-slope models;
- OFR, NFCI, credit, funding and multi-index risk composites.

Seasonality may be revisited only after the dataset materially expands and the technical sequence passes independent replication. A cheap descriptive month-of-year table is not an authorized decision layer.

## Phase I — Conditional reach and execution

Status: `NOT_AUTHORIZED`

Only after independent technical replication and minimal direction-layer attribution:

- locked historical confirmation;
- bounded entry triggers;
- BID/ASK fills and costs;
- no partial exits, runners or continuous threshold search;
- no Pine, alerts, sizing, paper trading or deployment.

## Stop rules

Stop this direction-context programme when:

- the independent technical replication fails effect or breadth;
- the sequence remains below the frozen sample gates on the qualified panel;
- fewer than four independent pairs pass source qualification;
- simple yield and VIX layers add no stable information or destroy sample;
- results depend on one pair or one exceptional crisis period.

Do not rescue a failed phase through looser technical definitions, post-outcome panel changes, seasonality, extra indicators or consumption of the 2022–2025 holdout.

## Archived work

PR #63 remains the bounded negative daily-pivot geometry study. It is not an active dependency and cannot block or authorize this direction-first programme.
