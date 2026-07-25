# Asian Sweep Fingerprint Study — Binding Feature Amendment v1.1

Date frozen: `2026-07-25`  
Branch: `agent/asia-sweep-fingerprint-study`  
Applies to: `FINGERPRINT_STUDY_PREREGISTRATION.md` v1.0.0  
Status: `FROZEN_BEFORE_FEATURE_OUTCOME_INSPECTION`

This amendment is binding and forms part of the preregistered feature contract. It adds two user-requested feature families before any fingerprint outcome, model coefficient, feature importance, 2022–2023 validation result, or 2024–2025 holdout result is inspected:

1. Asian-range width and volatility-normalized compression;
2. side-specific layered-liquidity topology around the Asian high and low.

The amendment does not alter the primitive sweep universe, success label, failure taxonomy, decision timestamps, model families, validation partitions or gates.

## 1. Design rationale

External Asian-range guidance commonly treats a relatively tight overnight range as relevant to a later London expansion or liquidity sweep. Fixed pip guidance such as approximately 20–30 pips is useful descriptively but is not stable across pairs or volatility regimes. The primary implementation therefore uses causal ATR, average-daily-range and rolling same-window normalization rather than adopting a fixed-pip trading filter.

Layered liquidity is represented as a topology, not a discretionary confluence checkbox. The study distinguishes:

- liquidity already consumed before 08:00;
- liquidity available beyond the Asian boundary at 08:00;
- liquidity consumed between 08:00 and the candidate sweep;
- liquidity consumed by the sweep itself;
- liquidity still remaining beyond the sweep extreme.

This distinction permits two competing hypotheses to be tested without assuming the answer:

- `exhaustion hypothesis`: a sweep that completes a nearby liquidity stack is more likely to reverse;
- `attraction hypothesis`: unswept liquidity remaining just beyond the sweep extreme is more likely to pull price into continuation.

## 2. Asian-range width and compression

All calculations use synchronized active midpoint prices and completed information only.

### 2.1 Completed daily volatility references

For each Amsterdam date, compute daily high, low and close from `[00:00, 24:00)` `Europe/Amsterdam`. Daylight-saving days may contain 23 or 25 clock hours; the timezone-aware interval is authoritative.

For completed day `d`:

- `true_range_d = max(high_d - low_d, abs(high_d - close_d-1), abs(low_d - close_d-1))`;
- `ATR20_d = arithmetic mean of true_range over the previous 20 completed eligible Amsterdam dates`;
- `ADR20_d = arithmetic mean of high-minus-low over the previous 20 completed eligible Amsterdam dates`.

The current date is excluded. A feature is missing until all 20 prior eligible observations exist. No future backfilling is permitted.

### 2.2 Frozen width features

The following features are added to both T0 and T5 because they are fully known at 08:00:

- `asian_range_price`: Asian high minus Asian low;
- `asian_range_pips`;
- `asian_range_atr20`: Asian range divided by prior completed `ATR20`;
- `asian_range_adr20`: Asian range divided by prior completed `ADR20`;
- `asian_range_vs_median20`: Asian range divided by the median of the previous 20 eligible Asian ranges;
- `asian_range_percentile20`;
- `asian_range_percentile60`;
- `asian_range_zscore60`: robust z-score using rolling median and median absolute deviation;
- `asian_range_20_30_pip_flag`: descriptive only for EURUSD/GBPUSD; it has no independent gate or rule authority;
- `asian_range_under_20_pip_flag` and `asian_range_over_30_pip_flag`: descriptive only.

Primary model inputs remain continuous. Fixed pip flags cannot be used alone to authorize or reject an event.

### 2.3 Causal compression buckets

For anatomy reporting, assign the current Asian range using only the previous 60 eligible Asian ranges:

- `ULTRA_COMPRESSED`: at or below the prior 20th percentile;
- `LOW_NORMAL`: above the 20th and at or below the 50th percentile;
- `HIGH_NORMAL`: above the 50th and below the 80th percentile;
- `EXPANDED`: at or above the prior 80th percentile;
- `WARMUP`: fewer than 20 prior eligible ranges.

These quantile buckets are descriptive fingerprints. They are not tunable cutoffs and cannot be replaced after development results are seen.

### 2.4 Predeclared width interactions

The following interactions are permitted because they reflect distinct market mechanisms rather than unrestricted feature search:

- Asian-range width × sweep depth;
- Asian-range width × exact sweep time;
- Asian-range width × pre-sweep realized volatility;
- Asian-range width × same-side liquidity density;
- Asian-range width × remaining unswept liquidity beyond the sweep;
- Asian-range width × T5 reclaim depth.

Elastic-net models receive these explicit interactions. The nonlinear challenger may learn their nonlinear form without additional manual bins.

### 2.5 Required width analysis

The development report must show, separately for EURUSD and GBPUSD and for upper/lower sweeps:

- success rate and failure-class distribution by rolling compression bucket;
- continuous success curves versus `asian_range_atr20`, `asian_range_adr20` and percentile;
- whether very narrow ranges increase two-sided sweeps or false reversals;
- whether wide ranges reduce midpoint reachability merely because the target is farther away;
- calendar-week clustered uncertainty;
- stability by year and weekday.

No conclusion may rely only on a fixed 20–30 pip narrative.

## 3. Layered-liquidity topology

### 3.1 Frozen external level universe

Only levels deterministically known before the candidate sweep are permitted.

#### Session and higher-timeframe levels

- previous eligible Amsterdam-day high and low;
- previous completed New York-session high and low, using `[08:00, 17:00)` `America/New_York` on the preceding eligible New York business date;
- previous completed Amsterdam calendar-week high and low;
- current Amsterdam-week high and low formed before 08:00, excluding the current Asian boundary itself.

#### Confirmed structural pivots

- M15 pivot highs/lows confirmed by two completed bars on each side;
- H1 pivot highs/lows confirmed by two completed bars on each side.

A pivot is usable only after both right-hand confirmation bars have closed. At T0, retain:

- the five most recent unswept M15 pivots from the previous five eligible dates;
- the three most recent unswept H1 pivots from the previous twenty eligible dates.

A high pivot is unswept when no later active midpoint high has exceeded it by the invalidation tolerance before the feature snapshot. A low pivot is unswept analogously.

#### Equal-high/equal-low clusters

A structural cluster requires at least two distinct confirmed M15/H1 pivots of the same side whose prices lie within:

`max(one pip, 0.03 × ATR20)`.

The cluster price is the arithmetic mean of its member levels. Record member count, timeframe diversity and age. Clusters are features in addition to their constituent pivots; model preprocessing must prevent accidental duplicate weighting through regularization and correlation diagnostics.

### 3.2 Side-correct level selection

For an upper Asian sweep, the relevant prospective liquidity set contains only active levels at or above the Asian high. For a lower sweep, it contains only active levels at or below the Asian low.

Levels inside the completed Asian range are recorded as `already_internalized` and cannot count as external same-side liquidity.

All level identities, timestamps, prices and source families must be preserved in an event-level audit ledger.

### 3.3 Frozen proximity measures

For every relevant level, record signed distance from:

- the Asian boundary at 08:00;
- the market price immediately before the sweep minute;
- the sweep extreme at T0;
- the price at T5.

Distances are expressed in:

- pips;
- Asian-range fractions;
- `ATR20` fractions.

The following causal summary features are frozen:

- nearest same-side level distance;
- second-nearest and third-nearest distances;
- number of levels within `0.05 ATR20` of the Asian boundary;
- number within `0.10 ATR20`;
- number within `0.20 ATR20`;
- number within `0.25 × Asian range`;
- distinct source-family count within `0.10 ATR20`;
- total level count and source diversity beyond the boundary;
- exponentially weighted density `sum(exp(-distance_ATR / 0.10))` for non-negative same-side distances;
- nearest opposite-side level distance, retained separately as a potential reversal destination.

Proximity thresholds are frozen for anatomy reporting. Continuous distances remain the primary model inputs.

### 3.4 Liquidity-stack definition

A `layered stack` exists when at least two levels from at least two distinct source families lie within `0.10 ATR20` of one another and the nearest member is within `0.15 ATR20` of the relevant Asian boundary.

Record:

- stack present flag;
- member count;
- source-family diversity;
- stack centroid distance from the Asian boundary;
- stack span in pips, range fractions and ATR fractions;
- whether the Asian boundary itself overlaps the stack tolerance;
- whether a confirmed equal-high/equal-low cluster is part of the stack.

No discretionary visual grouping is permitted.

### 3.5 Consumption and residual-liquidity features

At 08:00, immediately before the sweep, at T0 and at T5, classify every relevant level as:

- `available`;
- `consumed_before_sweep`;
- `consumed_by_sweep`;
- `remaining_beyond_extreme`;
- `invalidated_or_internalized`.

A high-side level is consumed when active midpoint high reaches or exceeds the level. A low-side level is consumed when active midpoint low reaches or falls below the level.

Frozen event features include:

- count and source diversity available at 08:00;
- count and source diversity remaining immediately before the sweep;
- count and source diversity consumed by the sweep bar;
- count and source diversity consumed through T5;
- fraction of the pre-sweep stack consumed at T0 and T5;
- full-stack-exhausted flag;
- number of unswept levels remaining beyond the sweep extreme;
- distance to the nearest remaining level beyond the sweep extreme;
- residual weighted density beyond the sweep extreme;
- whether the sweep takes only the Asian boundary, one external level, or multiple external levels;
- whether the sweep terminates beyond the furthest nearby layer or stops inside the stack.

These features explicitly test exhaustion versus attraction. A single `external_confluence` boolean is insufficient and is demoted to a legacy comparison field.

### 3.6 Directional destination features

The study also records liquidity on the reversal side because a reversal requires somewhere for price to travel:

- nearest opposite-side prior-day, prior-New-York, prior-week and confirmed-pivot level;
- distance from T0 and T5 to that destination in range and ATR fractions;
- opposite-side source diversity;
- whether the Asian midpoint lies before the nearest opposite-side liquidity;
- whether an opposing layered stack lies between midpoint and the opposite Asian boundary.

These are causal destination fingerprints, not profit targets.

### 3.7 Required layered-liquidity comparisons

The development anatomy must compare successful midpoint reversals with each failure class on:

- no external layer versus a single level versus a layered stack;
- full-stack exhaustion versus partial consumption;
- no residual level versus a nearby residual level beyond the sweep;
- prior-day-only, prior-New-York-only, prior-week-only, pivot-only and mixed-source stacks;
- same result by pair, direction, weekday, year and Asian-range compression bucket.

The report must identify whether failed sweeps are characterized by:

- price stopping before the dominant liquidity cluster;
- price continuing because another unswept level remains nearby;
- excessive sweep depth through multiple layers;
- lack of an opposing destination;
- or a consumed stack followed by failure to displace back into the range.

## 4. Model and validation safeguards

- Width and liquidity features must be computed inside the causal event builder before any outcome joins.
- Rolling references may use development history but never future observations.
- Missing levels remain missing; they are not imputed from future sessions.
- Feature preprocessing and imputation occur within each grouped training fold.
- 2022–2023 cannot be opened until unit tests prove timestamp causality, DST correctness, pivot-confirmation delay, level invalidation and future-append invariance.
- Neither fixed pip ranges nor a single liquidity source may be promoted as a trading rule after development inspection.
- The five highest-ranked stable fingerprints in the existing validation gate may include width or liquidity features, but their sign and definition must be frozen before validation.

## 5. External guidance used as design input

The sources below motivate measuring range width and external liquidity, but they do not supply empirical proof or gate thresholds for this programme:

- The Inner Circle Trader, *ICT Forex — Implementing The Asian Range*;
- Fidelity, *What Is Average True Range?*;
- general Asian-range educational material describing the overnight period as comparatively compressed and emphasizing range width;
- session-liquidity material identifying previous-session, previous-day and structural highs/lows as potential liquidity references.

All thresholds and features in this amendment are preregistered research definitions. They are not presented as validated trading rules.