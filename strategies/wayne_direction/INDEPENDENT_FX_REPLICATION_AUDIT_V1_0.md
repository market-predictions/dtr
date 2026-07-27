# Wayne Independent FX Replication — Independent Audit v1.0

Date: 2026-07-27  
Audited run: `30260573288`  
Audited artifact digest: `sha256:cbed0761c03e9b71793b0100b23e04884db0d99154539a0e814930dc012251b9`

## Audit scope

The audit independently inspected the pooled target-level ledger rather than accepting the generated Markdown decision.

Checks included:

- pair and year boundaries;
- row and opportunity uniqueness;
- treatment and target-availability reconstruction;
- pair/year breadth;
- instrument-month clustering;
- an independent 50,000-sample cluster permutation;
- an independent 20,000-sample instrument-month bootstrap;
- binding gate reconstruction.

## Integrity checks

- target-level rows: 2,106;
- unique side-specific opportunities: 1,053;
- primary close-in-zone opportunities: 514;
- duplicate instrument × opportunity × target rows: zero;
- pairs: EURGBP, EURJPY, GBPJPY and NZDUSD only;
- observed years: 2015–2021 only;
- maximum observed outcome year: 2021;
- protected-year access: none.

## Independently reconstructed day-10 sample

- active opportunities: 26;
- EURGBP: 5;
- EURJPY: 11;
- GBPJPY: 8;
- NZDUSD: 2;
- maximum pair concentration: 42.31%;
- pair breadth with at least three active opportunities: three.

## Independently reconstructed conservative comparison

- clean treatment observations: 14;
- controls: 447;
- treatment successes: 5;
- control successes: 56;
- treatment rate: 35.71%;
- control rate: 12.53%;
- lift: +23.19 percentage points.

The independent 50,000-sample cluster-preserving permutation produced:

- p-value: 0.09246.

The authoritative 5,000-sample result was 0.09478. The difference is consistent with Monte Carlo error and does not alter any gate.

The independent 20,000-sample instrument-month bootstrap produced:

- fifth percentile: +1.69 percentage points;
- median effect: +22.80 percentage points;
- 95th percentile: +45.62 percentage points.

The authoritative interval was +1.48 to +43.70 percentage points. The independent interval confirms the same inference.

## Availability audit

Of 26 active opportunities:

- 14 had a conservative target available after the day-10 landmark;
- 12 were unavailable because the conservative target had been reached before the causal observation window or was same-bar ambiguous;
- GBPJPY contributed six of the unavailable conservative cases;
- no unavailable target was counted as a success.

## Breadth audit

Conservative pair eligibility requires at least three treatment and three control observations.

- EURJPY was the only eligible pair and had a positive effect;
- EURGBP, GBPJPY and NZDUSD each had two clean treatment observations;
- positive eligible pair count: one.

Year eligibility uses the same minimum counts.

- eligible years: 2015, 2018 and 2021;
- positive eligible years: 2018 and 2021;
- positive eligible year count: two.

## Audit conclusion

The authoritative binding decision is reproduced:

`FAIL_REPLICATION_SAMPLE_INSUFFICIENT`

The sample gate fails at 14 clean conservative treatments versus a frozen minimum of 15. Breadth and concentration gates also fail independently. The positive estimated effect and supportive stretch endpoint cannot override those failures.

No code correction, rerun or threshold amendment is warranted. The exact day-10 sequence remains an interesting sparse research candidate, not an authorized strategy or contextual-filter substrate.
