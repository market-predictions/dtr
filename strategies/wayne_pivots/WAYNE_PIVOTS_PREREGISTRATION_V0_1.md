# Wayne McDonell Pivot Methodology — Preregistration v0.1

Date frozen: 2026-07-27  
Branch: `agent/wayne-pivots-research`  
Work package: `WP-WP-20260727-01`

## Purpose

Test whether Wayne McDonell's traditional pivot framework supplies causal, economically useful price-path information beyond generic prior-range geometry, and only then determine whether a bounded execution policy has positive expectancy.

This programme is separate from DTR and Asian Sweep. It may reuse data ingestion, manifests, execution semantics, statistics and CI infrastructure, but it must not inherit their strategy assumptions or results.

## Source-faithful methodology under test

Traditional daily pivots from the previous completed period:

- `P = (H + L + C) / 3`
- `R1 = 2P - L`
- `S1 = 2P - H`
- `R2 = P + (H - L)`
- `S2 = P - (H - L)`
- `M1 = (S2 + S1) / 2`
- `M2 = (S1 + P) / 2`
- `M3 = (P + R1) / 2`
- `M4 = (R1 + R2) / 2`

Core Wayne directional zones:

- bullish bias: entry zone `M2..P`, conservative target `M4`, extended target `R2`, invalidation `S1`;
- bearish bias: entry zone `P..M3`, conservative target `M1`, extended target `S2`, invalidation `R1`.

R3, S3, M0, M5, Camarilla, Fibonacci and ATR pivots are excluded from the first programme.

## Primary causal period definition

- FX trading day: 17:00 America/New_York to the next 17:00 America/New_York;
- previous-period H/L/C must be complete before current-period pivots exist;
- timestamps remain stored in UTC with explicit New York and Amsterdam calendar fields;
- DST transitions are resolved by timezone libraries, never fixed UTC offsets.

A London-midnight day boundary is a preregistered sensitivity analysis only. It cannot replace the primary boundary based on better results.

## Initial universe

Primary intended universe:

- EURUSD
- GBPUSD
- USDJPY
- USDCHF
- AUDUSD
- USDCAD

If only a subset has already-qualified BID/ASK data, framework validation may begin on that subset, but no multi-pair scientific conclusion is authorized until at least four primary pairs are available.

Replication universe, unopened initially:

- NZDUSD
- EURJPY
- GBPJPY
- EURGBP

## Evidence stages

### Stage A — Deterministic pivot contract

1. exact traditional formulas;
2. exact New York period boundaries;
3. strict prior-period causality;
4. BID/ASK-aware price paths;
5. DST and incomplete-day handling;
6. deterministic same-bar ambiguity policy;
7. sampled parity audit against an independent implementation.

No outcome inspection is authorized before Stage A passes.

### Stage B — Pivot anatomy

For every pair-day, build an event ledger containing:

- prior-period H/L/C and complete pivot structure;
- current pivot versus previous pivot direction and normalized displacement;
- opening location relative to `M2`, `P`, `M3`;
- first touch and first entry time for each Wayne zone;
- target-before-invalidation outcomes;
- time to target/invalidation;
- MFE and MAE normalized by entry risk, ATR and prior-day range;
- session, weekday, month, year and scheduled-news tags;
- whether a level had already been consumed before the candidate event.

Primary bullish anatomy outcomes after first entry into `M2..P`:

- `M4` before `S1`;
- `R1` before `S1`;
- `R2` before `S1`.

Primary bearish anatomy outcomes after first entry into `P..M3`:

- `M1` before `R1`;
- `S1` before `R1`;
- `S2` before `R1`.

No executable trade policy is promoted from anatomy alone.

### Stage C — Placebo and falsification

Wayne geometry is compared with frozen controls:

1. prior close anchor;
2. prior-range midpoint anchor;
3. prior-range quartiles;
4. complete pivot structure translated by `+/-0.25` prior-day range;
5. seeded synthetic convex combinations of prior H/L/C;
6. matched non-pivot observations with similar volatility, trend and event time.

A Wayne zone must outperform matched controls. Equality means prior-range information exists but the Wayne formula adds no unique edge.

### Stage D — Direction attribution

Bias families are evaluated separately:

- `B0`: no bias, anatomy only;
- `B1`: central-pivot slope (`P_today > P_yesterday` bullish; lower bearish);
- `B2`: opening-location diagnostics;
- `B3`: frozen technical state using H4 21/55/200 and M15 5/8;
- `B4`: market-based macro proxy, only after pivot geometry passes;
- `B5`: full point-in-time fundamental bias, only after earlier gates justify the data work.

The book pivot-slope interpretation and later external-bias interpretation must never be silently blended.

### Stage E — Bounded execution

Only after geometry and at least one bias family pass:

Entries:

- `E1`: first central-zone entry;
- `E2`: first deep-zone touch (`M2` bullish, `M3` bearish);
- `E3`: completed M15 5/8 reversal confirmation after zone entry.

Targets:

- `T1`: `M4` bullish / `M1` bearish;
- `T2`: `R2` bullish / `S2` bearish.

Invalidation:

- bullish `S1`;
- bearish `R1`.

This creates exactly six canonical execution arms. No partial exits, breakeven, trailing stop, runner, position scaling or continuous threshold search is allowed initially.

## Execution semantics

- at most one trade per pair per pivot day and candidate arm;
- first qualifying event only;
- bullish entry executes on ASK and exits on BID;
- bearish entry executes on BID and exits on ASK;
- no fill may use a price printed before the signal became observable;
- unresolved same-minute stop and target collision is treated stop-first;
- gaps cannot receive optimistic limit fills;
- open positions liquidate no later than the pivot-day boundary;
- standard and stressed spread/slippage scenarios are reported separately;
- missing-data gaps use the framework's causal gap policy.

## Historical partitions

- development and mechanism specification: 2015–2019;
- mechanism validation: 2020–2021;
- locked historical strategy validation: 2022–2023;
- final historical confirmation: 2024–2025;
- genuine prospective OOS: observations after final preregistration.

Existing inspection of FX data elsewhere does not make 2022–2025 pristine. Results must be labelled historical confirmation rather than untouched validation.

## Promotion gates

### Geometry gate

At least one source-faithful Wayne zone must satisfy all of:

- at least 400 eligible pooled events;
- at least 75 events in each of four primary pairs;
- target-before-invalidation lift at least `+5` percentage points versus matched placebo;
- positive normalized path-value effect;
- positive effect in at least four primary pairs;
- positive effect in a majority of eligible years;
- no pair above 40% of the pooled effect;
- no year above 30% of the pooled effect;
- date-block bootstrap probability of positive effect at least 90%;
- familywise/FDR-adjusted q-value at most 0.10.

Failure closes the programme before directional and execution optimization.

### Bias gate

A bias family must improve both target probability and economic path value, with positive pair/year breadth and multiple-testing control. Higher hit rate with negative economic effect is insufficient.

### Execution gate

A frozen execution arm must satisfy approximately:

- mean expectancy at least `+0.07R` after standard costs;
- profit factor at least `1.15`;
- positive expectancy under elevated cost stress;
- positive expectancy in at least four primary pairs;
- positive expectancy in a majority of validation years;
- no pair or year above 35% of total net R;
- return-to-drawdown and bootstrap uncertainty reported;
- familywise correction across all six arms and all authorized bias families.

Exact numerical execution thresholds will be frozen before execution outcomes are opened.

## Future-pivot boundary

Developing next-period pivots repaint. They are excluded from the initial strategy test. A later calibration study may snapshot projected next-day levels at fixed New York times, but final historical values may never be substituted for the earlier snapshots.

## Explicit exclusions

- selecting the best day boundary after inspection;
- optimizing EMA lengths or chart timeframes;
- combining failed bias families to rescue them;
- pair, weekday, direction, year or news-window rescue after inspection;
- role-reversal breakout research before pivot geometry passes;
- weekly or monthly pivots before daily evidence;
- Pine, alerts, sizing, paper trading or deployment before historical confirmation and prospective evidence.

## Decision hierarchy

1. validate formulas, time boundaries and causality;
2. prove or reject unique pivot geometry versus placebo;
3. prove or reject directional attribution;
4. test the six bounded execution arms;
5. validate historically with locked partitions;
6. replicate prospectively or cross-asset without changing the rules;
7. only then consider Pine parity and deployment.
