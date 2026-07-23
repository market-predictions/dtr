# Work Package AS-WP-20260723-08 — Auction-State Development Diagnostic

## Objective

Replace the failed AS-A through AS-D first-sweep/reclaim family with a mechanism-level diagnostic that distinguishes rejection, acceptance, two-sided auction and unresolved boundary behavior.

This package is exploratory development research. A local preview was used to verify feasibility and therefore no diagnostic association may be treated as out-of-sample evidence. The untouched 2024-07-01 through 2025-12-31 partition remains closed until a complete challenger rule is frozen in a separate work package.

## Strategic question

When a session-specific reference range is breached, does the market show observable price acceptance outside the range or rejection back into it, and do those states produce directionally consistent forward behavior across NQ and ES proxies?

## Data boundary

- Private Dukascopy NQ and ES index-CFD BID proxies.
- Development observations only: 2023-01-01 through 2024-06-30.
- Prior data may be used causally for rolling reference distributions and prior-session levels.
- No data on or after 2024-07-01 may enter the diagnostic.
- Raw private data may not be committed or uploaded in artifacts.

## Session-specific reference ranges

### London

- Reference range: 18:00 previous local date through 02:00 New York time.
- Observation window: 02:00 through 06:00 New York time.

### New York

- Reference range: 02:00 through 08:30 New York time.
- Observation window: 08:30 through 11:30 New York time.

London and New York are separate auctions. New York may not reuse the stale Asian range.

## Boundary event

For each instrument, trade date and session:

1. Calculate the completed reference high, low and width.
2. Find the first five-minute bar that trades strictly above the high or strictly below the low.
3. A bar breaching both sides is `TWO_SIDED` immediately.
4. If no side is breached, emit no diagnostic event.

## Frozen causal state labels

### `ACCEPTANCE`

Within the breach bar plus the next two five-minute bars, two consecutive bars close outside the breached boundary. Detection occurs at the end of the second outside close.

### `REJECTION`

Within the breach bar plus the next two five-minute bars, a bar closes back inside the boundary and the next two five-minute closes remain inside. Detection occurs at the end of the second confirming inside close.

### `TWO_SIDED`

The opposite range boundary is breached before either acceptance or rejection is confirmed, including a same-bar double breach. Detection occurs at the second-side breach.

### `UNRESOLVED`

Neither acceptance nor rejection is confirmed within the frozen decision horizon and the auction has not become two-sided.

## Causal descriptors

Record without selecting thresholds:

- breach side and depth as a fraction of reference-range width;
- outside-close count through state detection;
- consecutive inside closes after reclaim;
- minutes from breach to state detection;
- whether the opposite side is subsequently swept;
- prior local-day high/low;
- prior US cash-session high/low;
- prior completed calendar-week high/low;
- whether the first breach also crosses an external same-side level at or beyond the reference boundary;
- reference-range percentile versus the preceding 60 same-session ranges;
- fixed compression categories: bottom third, middle third, top third;
- held outside retest and resumed breakout as descriptive fields only.

No percentile or retest threshold may be optimized.

## Directional outcome definitions

- `ACCEPTANCE`: measure in the breach direction.
- `REJECTION`: measure opposite the breach direction.
- `TWO_SIDED`: descriptive only; no challenger promotion from this package.
- `UNRESOLVED`: descriptive only; no challenger promotion from this package.

Anchor is the first one-minute open after causal state detection.

Measure signed return, MFE and MAE as fractions of the reference-range width at fixed horizons:

- 5 minutes;
- 15 minutes;
- 30 minutes;
- 60 minutes;
- session end.

Also record:

- reference midpoint hit;
- opposite boundary hit;
- one-range projection hit.

These are diagnostics, not P&L and not execution simulations.

## Candidate mechanism families

Only two mechanism families may be considered:

1. confirmed rejection with external-liquidity confluence;
2. confirmed acceptance after a compressed reference range.

The held-retest field is diagnostic only. It may be required in a future challenger only if it improves continuation behavior in at least three of four instrument/session cells without collapsing every cell below 30 observations.

## Development promotion standard

A mechanism/session combination may be carried into a separately preregistered challenger only when:

- at least 40 observations exist in each proxy;
- 30-minute and 60-minute mean signed returns have the same positive sign in NQ and ES;
- the relationship is not produced solely by one calendar subperiod;
- the mechanism is directionally coherent rather than a single favorable bucket;
- bootstrap uncertainty and multiple-comparison limitations are disclosed;
- no more than one final challenger architecture is selected.

Failure to meet this standard closes the redesign line without opening the untouched validation partition.

## Required outputs

- per-event diagnostic ledger per proxy;
- state distribution by instrument and session;
- fixed-horizon outcome summaries;
- rejection external-confluence comparison;
- acceptance compression-tertile comparison;
- held-retest comparison;
- 2023 versus 2024-H1 stability;
- deterministic bootstrap intervals by instrument/session/mechanism;
- candidate-selection decision with explicit limitations;
- independent reconstruction on a deterministic sample.

## Prohibited

- strategy P&L or stop/target optimization;
- accessing data on or after 2024-07-01;
- selecting weekdays, directions or instruments;
- inventing narrower percentile thresholds;
- testing additional technical indicators;
- reusing AS-A through AS-D as challenger variants;
- combining with DTR;
- Pine implementation or deployment claims.

## Decision consequence

- If no coherent mechanism passes the development promotion standard, stop Asian Sweep redesign research.
- If one mechanism passes, freeze one complete challenger—including entry, invalidation, target, costs and session scope—in a new work package before opening the untouched validation partition.
