# Wayne Direction-First Staged Monthly Sequence — Preregistration v0.5

Date frozen: 2026-07-27
Branch: `agent/wayne-direction-first-research`
Parent evidence:
- corrected D1 census run `30227738020`;
- H4 sensitivity run `30227738024`.

## Research question

When price acquires a monthly directional location early in the month, does the ordered sequence

1. monthly location;
2. new H4 structural confirmation in the location direction;
3. aligned healthy H4 EMA21/55/200 state;
4. subsequent monthly reach

produce a sufficiently broad and materially better reach profile than early-month location without a completed sequence?

This is a technical attribution study. It is not an executable strategy and does not yet include macro, policy regime, seasonality, entries, stops, sizing or costs.

## Population

- instruments: AUDUSD, EURUSD, GBPUSD, USDCAD, USDCHF and USDJPY;
- development years: 2015–2021 only;
- qualified M1 BID/ASK source run: `30111481052`;
- New York pivot day: 17:00–17:00 America/New_York;
- D1 and H4 bars use causal close timestamps and retain DST-short and DST-long sessions;
- 2022–2025 remain unopened.

## Frozen directional structure

The H4 structural engine remains unchanged:

- double bottom/top;
- break of structure;
- retest;
- confirmed higher low/lower high;
- continuation close beyond the complete pre-retest impulse extreme;
- ATR-normalized frozen tolerances;
- causal two-bar swing confirmation.

No structural threshold search is authorized.

## Monthly levels and sides

Levels use the completed prior month only.

- bullish location zone: M2 through P;
- bearish location zone: P through M3;
- bullish conservative/stretch targets: M4/R2;
- bearish conservative/stretch targets: M1/S2.

A month may produce one opportunity per side. Bullish and bearish opportunities from the same pair-month remain in one statistical cluster and are never treated as independent.

## Location acquisition

### Primary rule — `CLOSE_IN_ZONE`

Location is acquired when either:

- the month opens inside the applicable zone; or
- the first completed H4 bar whose close is inside the zone occurs within the first five pivot days.

The causal timestamp is the month-open timestamp or the H4 close timestamp.

### Sensitivity rule — `RANGE_TOUCH`

A separate labeled sensitivity allows the first completed H4 bar whose high-low range intersects the zone within the first five pivot days.

The range-touch population cannot authorize promotion by itself.

## Ordered sequence

For each side-specific location:

1. search strictly after the location timestamp for a new H4 trend-confirmation event in the same direction;
2. after that event, search for the first H4 close where:
   - H4 structure remains in that direction; and
   - EMA health is `BULL_EXPANDING`/`BULL_STABLE` or `BEAR_EXPANDING`/`BEAR_STABLE`;
3. stop the sequence if H4 structure invalidates before MA health appears.

MA health on the structural-confirmation bar is allowed but labeled `SAME_BAR`. A strict-later diagnostic will also be reported.

Pre-existing aligned H4 structure at location is not counted as a new staged turn. It is retained as a separate control category.

## Time windows

- primary window: complete the sequence by the end of pivot day 5;
- development sensitivity: complete the sequence by the end of pivot day 10;
- location must always be acquired by the end of pivot day 5.

The ten-day result cannot rescue a failed five-day primary result.

## Stage categories at each landmark

- `COMPLETE_ACTIVE`: sequence completed and H4 structure plus MA health remain aligned at the landmark;
- `COMPLETE_DECAYED`: sequence completed but alignment no longer remains active;
- `STRUCTURE_NO_HEALTH`: new H4 structure confirmed but MA health did not mature;
- `STRUCTURE_FAILED`: structure invalidated before MA health;
- `PREEXISTING_ALIGNED`: aligned H4 structure existed at location but no new post-location confirmation occurred;
- `LOCATION_ONLY`: no new H4 structural confirmation.

D1 relation is recorded at location and at final confirmation as aligned, none or opposed. It is a frozen stratum, not an optimization variable.

## Target eligibility and outcomes

A target touched before final confirmation is `PRECONSUMED` and cannot count as a staged success.

A target touched on the final-confirmation H4 bar is same-bar ambiguous and is excluded from clean signal-time success.

Signal-time outcome:

- observation begins with the next completed H4 bar after final confirmation;
- ends at target, H4 structural invalidation or month end;
- target and invalidation on the same H4 bar are ambiguous and excluded from clean success.

Landmark comparison:

- classifications are frozen at the end of pivot day 5 and day 10;
- targets already touched by the landmark are unavailable;
- future month-end reach begins with the next H4 bar;
- this fixed landmark prevents completed sequences from receiving extra observation time merely because they formed earlier.

## Primary comparison

Within the primary `CLOSE_IN_ZONE` population and among targets available at day 5:

- treatment: `COMPLETE_ACTIVE` at day 5;
- control: all other eligible stage categories;
- outcomes: conservative and stretch target reach from after the day-5 landmark to month end.

Signal-time reach before H4 invalidation is reported separately and is not used as the only treatment-control comparison.

## Statistical plan

- cluster unit: instrument × month, including both sides and both targets;
- 2,000 cluster-bootstrap resamples for effect intervals;
- 5,000 label permutations stratified by instrument-year;
- Benjamini-Hochberg correction across four planned tests:
  - day-5 conservative;
  - day-5 stretch;
  - day-10 conservative;
  - day-10 stretch.

Effect is treatment reach rate minus control reach rate.

## Sample gates

Primary day-5 sample gate:

- at least 50 unique `COMPLETE_ACTIVE` opportunities pooled;
- at least 5 in four pairs;
- at least 100 available control opportunities.

Ten-day sensitivity gate:

- at least 80 unique `COMPLETE_ACTIVE` opportunities pooled;
- at least 8 in four pairs;
- at least 120 available control opportunities.

## Promotion gate

The technical sequence can open macro/regime/seasonality integration only when the primary `CLOSE_IN_ZONE` day-5 conservative target satisfies all of:

- sample gate passes;
- absolute reach lift at least 10 percentage points;
- cluster-permutation p-value at most 0.05;
- full-family q-value at most 0.10;
- positive treatment-control effect in at least four pairs;
- positive effect in at least five development years;
- no single pair contributes more than 35% of completed primary opportunities.

Stretch reach is supportive only. The range-touch and day-10 sensitivities cannot authorize promotion independently.

## Binding decisions

- `PASS_STAGED_SEQUENCE_OPEN_DIRECTION_LAYERS`;
- `FAIL_STAGED_SEQUENCE_PRIMARY_SAMPLE`;
- `FAIL_STAGED_SEQUENCE_NO_REACH_LIFT`;
- `SENSITIVITY_ONLY_DO_NOT_PROMOTE`;
- `DATA_OR_CAUSALITY_WALL`.

## Protected boundaries

- no daily-pivot research;
- no threshold rescue;
- no weighted direction score;
- no macro, regime or seasonality outcomes before point-in-time contracts;
- no entry, stop, partial exit, runner, breakeven or sizing research;
- no 2022–2025 outcomes;
- no Pine, alerts, paper trading or deployment.
