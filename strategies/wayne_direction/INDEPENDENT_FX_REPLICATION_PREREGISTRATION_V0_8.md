# Wayne Direction-First Independent FX Replication — Preregistration v0.8

Date frozen: 2026-07-27  
Branch: `agent/wayne-independent-fx-replication`  
Parent evidence: PR #64, pair run `30253362740`, corrected aggregate `30254100112`.

## Purpose

Test whether the unchanged day-10 monthly-location → H4 structure → H4 moving-average-health sequence reproduces outside the original six-pair development panel.

This is a staged programme. Source qualification is completed and frozen before any replication outcome is opened.

## Phase A — source qualification

Frozen candidates:

- EURGBP;
- EURJPY;
- GBPJPY;
- NZDUSD.

These are the only additional pairs already produced by qualified Dukascopy BID/ASK M1 source run `30111481052`. No additional symbol may be added after qualification begins.

Source years are 2015–2021. The 2022–2025 partitions remain excluded.

### Pair qualification gates

Every accepted pair must pass all of:

- all seven annual BID and ASK files present;
- exact calendar-minute row count for 2015–2021;
- unique, sorted and one-to-one BID/ASK timestamps;
- zero BID/ASK active-quote disagreement;
- zero invalid active OHLC rows;
- zero invalid or negative active close spreads;
- active-minute fraction between 65% and 76% of calendar minutes;
- at least 90% of observed New York pivot days contain at least 1,200 active minutes;
- at least 90% of observed H4 bars contain at least 180 active minutes;
- median active spread no greater than 3 pips;
- 95th-percentile spread no greater than 8 pips;
- 99th-percentile spread no greater than 20 pips.

At least three of four candidates must qualify before outcomes can open. Excluded pairs remain excluded without replacement.

No structure events, monthly locations, target reaches, returns or P&L may be calculated in Phase A.

## Phase B — unchanged technical replication

Phase B opens only after `PASS_PANEL_QUALIFICATION_OPEN_REPLICATION_OUTCOMES`.

The following remain byte-for-byte or logically unchanged from the authoritative development study:

- New York 17:00 pivot calendar;
- prior-month traditional pivots;
- primary location rule `CLOSE_IN_ZONE`;
- bullish M2–P and bearish P–M3 locations acquired by pivot day 5;
- new H4 double-bottom/top → BOS → retest → HL/LH → continuation confirmation after location;
- continuation beyond the complete pre-retest impulse extreme;
- H4 EMA21/55/200 aligned `STABLE` or `EXPANDING` health after structure;
- sequence active at the end of pivot day 10;
- conservative targets M4 for bullish and M1 for bearish opportunities;
- stretch targets R2 and S2 as supportive diagnostics;
- pre-consumed and same-bar targets excluded;
- fixed day-10 landmark comparison;
- instrument-month cluster unit;
- cluster-preserving permutation within instrument-year;
- no threshold, target, location, timeframe or window search.

## Replication comparison

Primary treatment is `COMPLETE_ACTIVE` at day 10 among primary close-in-zone conservative targets still available after the day-10 landmark.

Control is every other eligible day-10 stage category.

Primary outcome is subsequent conservative-target reach by month end.

The stretch target is supportive only.

## Replication gates

The independent panel passes only when all primary conservative predicates hold:

- at least 20 active day-10 opportunities;
- at least 15 available conservative treatment observations;
- at least 200 available controls;
- at least three treatment opportunities in at least three pairs;
- no pair contributes more than 40% of active opportunities;
- reach lift at least 10 percentage points;
- one-sided cluster-permutation p-value at most 0.10;
- positive effect in at least three eligible pairs;
- positive effect in at least four eligible years;
- effect direction agrees with the original six-pair result.

The four-pair sample gates are separately frozen for this independent panel. Signal construction, target availability, outcome definitions and inference remain unchanged.

## Binding decisions

- `PASS_REPLICATION_AUTHORIZE_MINIMAL_CONTEXT_PHASE`;
- `FAIL_REPLICATION_SAMPLE_INSUFFICIENT`;
- `FAIL_REPLICATION_EFFECT_NOT_REPRODUCED`;
- `FAIL_REPLICATION_BREADTH_OR_CONCENTRATION`;
- `FAIL_PANEL_QUALIFICATION_DATA_WALL`.

## After a pass

Only after replication passes may the next minimal context programme open:

1. nominal two-year yield differential and its 20-day change;
2. simple VIX expanding-percentile risk state;
3. independent attribution of each layer before combination.

Seasonality and full release-level macro remain postponed.

## Protected boundaries

- no 2022–2025 outcome access;
- no original-pair retuning;
- no additional in-sample time window;
- no daily-pivot research;
- no yield, VIX, seasonality or macro outcome interaction before replication passes;
- no entry, stop, partial exit, runner, costs, sizing or P&L;
- no Pine, alerts, paper trading or deployment.
