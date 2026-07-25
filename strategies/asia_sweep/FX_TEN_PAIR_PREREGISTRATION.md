# Asian Sweep Ten-Pair FX Study — Preregistration

Version: `v1.0.0`  
Date frozen: `2026-07-25`  
Work package: `AS-WP-20260725-10`  
Status: `FROZEN_BEFORE_REAL_OUTCOME_INSPECTION`

## Research question

After the London session first breaches the completed Asian range and then causally confirms a rejection, does the reversal-signed 60-minute midpoint return exceed the corresponding return after matched non-rejection boundary breaches across a diversified ten-pair FX universe?

This first phase is a controlled mechanism study. It cannot calculate executable P&L or optimize trading rules.

## Fixed universe

EURUSD, GBPUSD, USDCHF, AUDUSD, NZDUSD, USDCAD, USDJPY, EURJPY, GBPJPY and EURGBP.

Factor blocks:

- `usd_europe`: EURUSD, GBPUSD, USDCHF;
- `usd_commodity`: AUDUSD, NZDUSD, USDCAD;
- `jpy`: USDJPY, EURJPY, GBPJPY;
- `europe_cross`: EURGBP.

## Frozen source

- qualified Dukascopy BID and ASK one-minute annual files;
- synchronized rows only;
- a minute is active only when both BID and ASK are active;
- midpoint OHLC equals the arithmetic mean of corresponding BID and ASK OHLC fields;
- no missing minute is synthesized;
- source caches and annual hashes are inherited unchanged from the qualified ten-pair source programme.

## Frozen partitions

- 2015–2019: discovery mechanism study;
- 2020–2021: mechanism validation, blocked until discovery passes;
- 2022–2023: executable strategy validation, blocked until an execution contract is frozen;
- 2024–2025: untouched final holdout;
- 2026 YTD: monitoring only.

No result from 2020 onward may influence the discovery definition or thresholds.

## Frozen market clock

The inherited Asian Sweep clock remains unchanged and is evaluated in `America/New_York` with IANA daylight-saving rules:

- Asian reference range: 18:00 previous day inclusive to 02:00 current day exclusive;
- London execution window: 02:00 inclusive to 06:00 exclusive.

This is equivalent to approximately 23:00 previous day through 07:00 and 07:00 through 11:00 in `Europe/London` across the normal US/UK DST alignment. The implementation uses the original New York wall-clock contract to preserve detector identity.

## Frozen state definition

The existing causal auction-state detector is reused unchanged:

1. identify the first five-minute breach of the completed Asian high or low;
2. inspect only the breach bar plus the next two five-minute bars;
3. rejection requires a close back inside followed by two inside closes;
4. two consecutive closes outside constitute acceptance;
5. an opposite-boundary breach through the causal confirmation bar constitutes a two-sided state;
6. all other states are unresolved.

The primary event is `LONDON × REJECTION`. The reversal direction is short after an upper-boundary breach and long after a lower-boundary breach.

## Primary endpoint

The primary endpoint is the reversal-signed midpoint return from the first active synchronized minute at or after state confirmation to the last active synchronized minute before the earlier of:

- 60 elapsed minutes; or
- the 06:00 New York window end.

The return is divided by the completed Asian-range width. An endpoint is ineligible when the final active minute is more than two minutes before the required endpoint.

## Matched controls

Each primary event is matched to five non-rejection first-boundary events from distinct London dates.

Exact matching dimensions:

- same pair;
- same calendar year;
- same weekday;
- same 30-minute state-confirmation time bucket;
- different trade date.

Eligible control states are `ACCEPTANCE` and `UNRESOLVED`; two-sided events are excluded. Nearest matching is deterministic on:

- causal trailing-60-session Asian-range percentile;
- breach depth divided by Asian-range width.

No future return enters control selection. An event is excluded when five distinct-date controls are unavailable.

## Discovery inference

The pooled effect is event return minus the mean return of its five matched controls.

Dependence controls:

- 10,000-iteration calendar-date block bootstrap;
- 10,000-iteration calendar-date clustered sign permutation;
- pair-level and factor-block attribution;
- concentration checks by pair and date.

The calendar date is the clustering unit so same-day cross-pair dependence is preserved.

## Discovery promotion gate

Every predicate must pass on 2015–2019:

1. at least 400 matched events;
2. at least 8 of 10 pairs contribute at least 20 matched events;
3. all four factor blocks contribute at least 40 matched events;
4. no pair contributes more than 25% of matched events;
5. no London date contributes more than 10% of matched events;
6. pooled mean event-minus-control effect is at least `+0.02` Asian-range fractions;
7. the 95% date-block bootstrap lower bound is above zero;
8. the one-sided date-clustered permutation p-value is at most 0.05;
9. at least 7 of 10 pair point estimates are positive;
10. at least 3 of 4 factor-block point estimates are positive.

Failure stops this formulation before 2020–2021 is inspected. Thresholds, states, matching rules and partitions may not be changed after observing the result.

## Conditional later programme

Only after discovery passes unchanged:

- rerun the identical mechanism study on 2020–2021 with the same effect, inference and breadth requirements;
- freeze a side-correct BID/ASK execution contract before inspecting 2022–2023;
- use actual spread, explicit adverse slippage stress, stop-first collision handling and one global cross-pair rule;
- open 2024–2025 only after executable validation passes.

## Explicit exclusions

Until both mechanism stages pass, the programme may not:

- calculate entries, stops, targets, R multiples, commissions or strategy P&L;
- select the PDH/PDL cluster subset, weekdays, pairs, directions or range regimes by result;
- revive failed AS-A through AS-D variants as hidden co-primary trials;
- inspect 2022–2025 outcomes;
- build Pine, alerts, sizing, paper trading or live deployment.
