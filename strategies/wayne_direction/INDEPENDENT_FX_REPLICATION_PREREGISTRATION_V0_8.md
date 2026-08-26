# Independent FX Replication Preregistration v0.8

Date: 2026-07-27
Status: `FROZEN_BEFORE_OUTCOMES`
Branch: `agent/wayne-direction-first-research`

## Purpose

Test whether the unchanged day-10 monthly-location -> new H4 structure -> healthy aligned EMA sequence replicates on an independently qualified panel of liquid FX pairs.

This phase is a cross-sectional replication. It is not an optimization phase and must not use 2022-2025 outcomes to repair sample size.

## Frozen development reference

Development instruments:

- AUDUSD
- EURUSD
- GBPUSD
- USDCAD
- USDCHF
- USDJPY

Development period: 2015-2021.

The development result remains descriptive evidence only. It cannot be pooled into the primary independent-panel effect estimate.

## Candidate universe

The candidate universe is defined before any Wayne sequence outcomes are generated.

Eligible instruments must:

1. be spot FX pairs available from the same Dukascopy BID/ASK M1 acquisition path used by the development panel;
2. contain two freely traded currencies from the following liquid set: AUD, CAD, CHF, EUR, GBP, JPY, NZD, USD;
3. not duplicate a development instrument;
4. not contain pegged, tightly managed, offshore, synthetic, precious-metal or crypto legs;
5. provide complete source coverage for every calendar year from 2015 through 2021 on both BID and ASK;
6. pass the source-quality gates below without reference to strategy outcomes.

Initial candidate inventory to qualify:

- AUDCAD
- AUDCHF
- AUDJPY
- AUDNZD
- CADCHF
- CADJPY
- CHFJPY
- EURAUD
- EURCAD
- EURCHF
- EURGBP
- EURJPY
- EURNZD
- GBPAUD
- GBPCAD
- GBPCHF
- GBPJPY
- GBPNZD
- NZDCAD
- NZDCHF
- NZDJPY
- NZDUSD

This list is a data-qualification universe, not a promise that every pair will be admitted.

## Source-quality gates

All gates are evaluated independently for each candidate pair using only raw BID/ASK files and derived quote-quality diagnostics.

### Gate Q1 — complete annual files

Required:

- one non-empty M1 BID file and one non-empty M1 ASK file for each year 2015-2021;
- 14 expected files in total;
- readable gzip and CSV structure;
- valid timestamps and OHLC fields.

Failure is binding.

### Gate Q2 — timestamp integrity

Required:

- timestamps strictly increasing after deterministic duplicate handling;
- no impossible timestamps;
- no annual timestamp overlap;
- duplicate-timestamp share <= 0.05% after raw ingestion;
- BID and ASK timestamps align on at least 99.0% of retained minutes.

Failure is binding.

### Gate Q3 — quote validity

Required:

- finite positive BID and ASK OHLC values;
- ASK >= BID for at least 99.99% of synchronized closes;
- negative-spread observations are removed and separately counted;
- invalid-OHLC share <= 0.01%;
- high >= max(open, close) and low <= min(open, close) for both sides after parser normalization.

Failure is binding.

### Gate Q4 — temporal coverage

For each year:

- at least 95% of expected weekday trading minutes after excluding the standard Friday-close to Sunday-open market closure;
- no unexplained continuous gap longer than five trading days;
- no more than three unexplained gaps longer than one trading day;
- yearly coverage must pass separately; strong years cannot compensate for a failed year.

Failure is binding.

### Gate Q5 — spread plausibility

Using synchronized close quotes:

- median spread must be positive;
- 99th-percentile spread must be finite;
- median spread as a fraction of median price must be <= 0.15%;
- no single year may have a median relative spread more than three times the pair's seven-year median;
- anomalous spread spikes may be retained in the source but must not indicate a scale or decimal-format error.

Failure is binding when caused by source corruption or implausible quoting. Genuine market stress is not removed merely because spreads widen.

### Gate Q6 — activity and tradability proxy

Because Dukascopy M1 data does not provide centralized FX volume, liquidity is proxied without strategy outcomes.

Required:

- synchronized quotes on at least 250 distinct trading days per complete non-leap year, adjusted for calendar conventions;
- median active synchronized minutes per trading day >= 1,200;
- 10th percentile active synchronized minutes per trading day >= 900;
- no persistent multi-month collapse in quote activity unexplained by source outages.

Failure is binding.

## Panel-admission rule

A pair is admitted only when all binding gates pass for all seven years.

No pair may be excluded because its eventual sequence effect is weak, negative or inconvenient. No failed pair may be reinstated because it improves sample size or performance.

The panel is frozen in a manifest containing:

- candidate pair;
- included/excluded status;
- each gate result;
- annual file inventory;
- annual synchronized-minute counts;
- duplicate, invalid and negative-spread shares;
- spread statistics;
- unexplained gap diagnostics;
- raw-file checksums;
- acquisition run and code commit.

The manifest must be committed before sequence outcomes are generated.

## Frozen replication treatment

The replication reuses the development implementation unchanged:

1. primary location is `CLOSE_IN_ZONE` within the first five pivot days;
2. a new H4 structural confirmation must occur after location;
3. H4 EMA21/55/200 must become directionally aligned and stable or expanding while structure remains valid;
4. the sensitivity landmark is pivot day 10;
5. pre-existing aligned direction at location is not a new turn;
6. targets touched before or on final confirmation/landmark are unavailable;
7. conservative and stretch monthly-pivot targets are unchanged;
8. instrument-month is the cluster unit;
9. complete bull/bear treatment bundles remain intact in permutation inference.

No threshold, target, window, structure, EMA-health, invalidation or availability rule may change during replication.

## Primary replication analysis

Primary replication endpoint:

- day-10 conservative target reach after the landmark among target-available opportunities.

Primary comparison:

- `COMPLETE_ACTIVE` treatment versus all eligible non-treatment opportunities under the frozen control definition.

The independent-panel estimate is reported separately from development. A secondary combined estimate may be shown only after the independent result is disclosed.

## Frozen sample gates

The independent panel must satisfy all of the following before effect interpretation:

- at least 80 `COMPLETE_ACTIVE` day-10 sequences;
- at least 40 target-available conservative treatment rows;
- at least 120 target-available controls;
- at least four admitted pairs with eight or more active day-10 sequences;
- at least four admitted pairs with five or more target-available conservative treatment rows.

If these gates fail, the binding result is `FAIL_INDEPENDENT_REPLICATION_SAMPLE` regardless of observed lift or p-value.

## Effect and breadth criteria

Conditional on passing the sample gates, evidence is considered replication-supportive only when:

- conservative lift is positive;
- clustered permutation p <= 0.05;
- FDR-adjusted q <= 0.10 across the frozen conservative and stretch comparisons;
- bootstrap 90% interval for conservative lift excludes zero;
- at least 60% of eligible admitted pairs have positive conservative lift;
- at least four eligible years have positive conservative lift;
- no single pair contributes more than 35% of available treatment rows;
- removal of the largest contributing pair does not reverse the sign of the pooled conservative lift.

These are evidence criteria, not authorization for execution or deployment.

## Decision table

### `PASS_INDEPENDENT_TECHNICAL_REPLICATION`

All sample gates pass and the conservative endpoint satisfies the frozen effect and breadth criteria.

Consequence: authorize the minimal external-context phase consisting of two-year yield differential followed by a simple VIX regime test.

### `FAIL_INDEPENDENT_REPLICATION_EFFECT`

Sample gates pass but the conservative endpoint fails the effect or breadth criteria.

Consequence: reject the staged sequence as a generalized FX direction edge. Do not rescue it through looser technical thresholds, seasonality or macro conditioning.

### `FAIL_INDEPENDENT_REPLICATION_SAMPLE`

One or more sample gates fail.

Consequence: report the observed census but do not interpret performance. Decide separately whether an independently justified additional asset family or older qualified history is available. Keep 2022-2025 locked.

### `FAIL_PANEL_QUALIFICATION`

Fewer than four independent pairs pass all source-quality gates.

Consequence: stop before outcomes and report the data wall.

## Locked data

The following remain unavailable during this phase:

- all 2022-2025 pair outcomes;
- seasonality conditioning;
- yields, policy rates and macro releases;
- VIX or other risk-regime conditioning;
- execution, costs, entries, exits, sizing or Pine implementation.

## Audit requirements

The final evidence package must contain:

- frozen panel manifest;
- source-quality ledger;
- admitted and excluded pair list with reasons;
- pair-level sequence ledgers;
- pooled replication ledger;
- stage census;
- frozen comparisons;
- cluster-preserving inference output;
- leave-one-pair-out diagnostics;
- decision JSON and human-readable report;
- independent audit confirming no post-outcome panel changes.
