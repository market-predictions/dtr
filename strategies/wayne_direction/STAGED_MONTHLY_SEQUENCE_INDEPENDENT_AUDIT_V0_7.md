# Wayne Staged Monthly Sequence — Independent Audit v0.7

Date: 2026-07-27
Audited artifact run: `30254100112`
Artifact digest: `sha256:4c2a3a31f9e4e6588df0fbafbd6f5f8dec127135b3c23c4ec7a657379c45a38a`

## Scope

The audit independently inspected the corrected pooled ledger and recomputed the population, opportunity uniqueness, stage counts, treatment/control rates, effects, sample gates and binding decision.

## Population reconciliation

Recomputed results:

- target-level rows: 3,128;
- unique side-specific opportunities: 1,564;
- primary close-in-zone opportunities: 764;
- range-touch sensitivity opportunities: 800;
- instruments: exactly AUDUSD, EURUSD, GBPUSD, USDCAD, USDCHF and USDJPY;
- years: exactly 2015 through 2021;
- duplicate instrument × opportunity × target-tier rows: zero;
- post-development years: zero.

The ledger population matches the frozen contract.

## Stage reconciliation

Primary day-5 active opportunities recomputed: 15.

- AUDUSD 4;
- EURUSD 4;
- GBPUSD 3;
- USDCAD 2;
- USDCHF 1;
- USDJPY 1.

Day-10 active opportunities recomputed: 36.

- AUDUSD 9;
- EURUSD 7;
- GBPUSD 10;
- USDCAD 3;
- USDCHF 4;
- USDJPY 3.

These counts reproduce the decision JSON and both sample-gate failures.

## Outcome reconciliation

Recomputed fixed-landmark results:

- day-5 conservative: 5 of 11 treatment cases reached versus 132 of 730 controls;
- day-5 stretch: 3 of 11 versus 80 of 744;
- day-10 conservative: 12 of 25 versus 83 of 674;
- day-10 stretch: 6 of 31 versus 58 of 705.

The corresponding effects reproduce exactly:

- +27.3724 percentage points;
- +16.5200 percentage points;
- +35.6855 percentage points;
- +11.1279 percentage points.

## Clustered inference audit

The first aggregate artifact shuffled side-level rows and did not preserve the frozen instrument-month cluster. That artifact is not authoritative for p-values or q-values.

The corrected implementation:

- builds instrument-month clusters;
- orders side rows deterministically;
- groups clusters by instrument-year and cluster size;
- permutes complete treatment vectors between same-size clusters;
- retains 5,000 permutations;
- applies Benjamini-Hochberg adjustment across the four planned tests.

An independent implementation reproduced the corrected p-values to Monte Carlo tolerance:

- day-5 conservative approximately 0.12;
- day-5 stretch approximately 0.30;
- day-10 conservative approximately 0.0002;
- day-10 stretch approximately 0.052.

The repository artifact reports 0.1192, 0.3027, 0.0002 and 0.0518 respectively, with q-values 0.1589, 0.3027, 0.0008 and 0.1036.

## Causal boundary audit

Spot checks confirmed:

- location precedes new structural confirmation;
- health confirmation does not precede structure;
- pre-existing H4 direction is not classified as a new staged turn;
- target touches before the signal or fixed landmark are not successes;
- target touches on the signal or landmark bar are unavailable/ambiguous;
- fixed day-5 and day-10 landmarks prevent earlier signals from receiving extra comparison time;
- D1 relation is descriptive and does not alter treatment classification.

## Decision audit

Primary gate requirements versus observations:

- active opportunities: 50 required, 15 observed;
- pair breadth: four pairs with at least five required, zero observed;
- available conservative treatment: 30 required, 11 observed;
- controls: 100 required, 730 observed.

Sensitivity gate requirements versus observations:

- active opportunities: 80 required, 36 observed;
- pair breadth: four pairs with at least eight required, two observed;
- available conservative treatment: 40 required, 25 observed;
- controls: 120 required, 674 observed.

Both sample gates fail. The promotion rule cannot pass regardless of effect magnitude.

## Verdict

`APPROVE_FAIL_STAGED_SEQUENCE_PRIMARY_SAMPLE`

The day-10 conservative association is sufficiently strong and broad to justify an unchanged independent replication hypothesis. It is not sufficiently sampled to authorize integration, execution or deployment. Threshold rescue, reclassification of pre-consumed targets and additional in-sample window search should be rejected.
