# Asian Sweep Context and Regime Atlas — Preregistration v10.0

Date frozen: 2026-07-26  
Branch: `agent/asia-sweep-context-regime-atlas`  
Base: validated fingerprint programme head `038f5f40a898d826665400f4d03fc6bc23dc2346`

## Purpose

Return to the broader higher-timeframe, regime and trend-condition roadmap without reopening the failed weekly-profile hypotheses, entry timing, stop geometry, target grid or runner policies.

The first stage is a causal attribution atlas. It asks which pre-event market contexts materially change the validated Asian Sweep reversal fingerprint and executable payoff distribution. It is not an optimisation grid and cannot promote a trading strategy by itself.

## Fixed event population

- EURUSD and GBPUSD Asian Sweep fingerprint events;
- Amsterdam Asian range `[00:00, 08:00)`;
- candidate sweeps `[08:00, 10:00)`;
- causal T0 and T5 landmarks only;
- development years 2015–2021 for attribution;
- 2022–2025 are not represented as untouched data because they were used by the completed fingerprint validation programme;
- any candidate emerging from this atlas requires fresh future data or a separately qualified cross-asset replication before promotion.

## Factor families

### A. Higher-timeframe direction

1. completed-day D1 direction;
2. completed-week W1 direction;
3. D1/W1 alignment versus conflict;
4. sweep/reversal direction aligned with or opposed to D1 and W1.

### B. Trend strength and trend change

1. normalized D1 slope magnitude;
2. normalized W1 slope magnitude;
3. trend improvement versus deterioration;
4. acceleration, deceleration and structural conflict;
5. directional persistence over completed daily bars.

Direction and improvement are kept separate. A bullish change in slope while price remains structurally bearish is not labelled as an established bullish trend.

### C. Volatility regime

1. daily ATR percentile;
2. weekly realized-range percentile;
3. Asian-range width relative to daily ATR;
4. compression, normal and expansion states;
5. rising, falling and stable volatility transitions;
6. short-horizon realized volatility relative to its trailing distribution.

### D. Causal location

1. entry position within the completed prior-day range;
2. entry position within the completed prior-week range;
3. distance to PDH, PDL, PWH and PWL in ATR units;
4. distance to daily and weekly open;
5. Monday-range position when causally available;
6. overnight displacement and gap context.

The previously rejected compact PDH/PDL cluster formulation is not reopened. Broad causal location is a different attribution question and cannot inherit that cluster's rules.

### E. Session and calendar diagnostics

1. weekday;
2. sweep time bucket;
3. DST-safe Amsterdam session state;
4. month and quarter only as stability diagnostics, never promotion filters.

## Research sequence

1. Construct one causal context ledger with all factor values available strictly before T0 or T5.
2. Reconcile event identities and labels against the frozen fingerprint evidence.
3. Evaluate every factor independently using fixed, coarse bins defined from trailing causal distributions.
4. Report absolute outcome rates, lift versus the full eligible population, stressed payoff proxies, pair breadth, year breadth, concentration and date-block uncertainty.
5. Rank factors by predeclared evidence score, not by the best isolated bucket.
6. Permit at most six two-factor interactions, selected before interaction outcomes are inspected from the strongest non-redundant single factors.
7. Open an adaptive regime router only if at least two independent factor families show broad and economically meaningful attribution.

## Minimum evidence for a factor family

A factor family is `PROMISING_FOR_REPLICATION` only when at least one coarse state satisfies all of the following and the family-level multiple-testing adjustment remains significant:

- at least 150 eligible events pooled;
- at least 50 events per pair;
- representation in at least five development years;
- no pair above 70% concentration;
- no year above 35% concentration;
- absolute hit-rate lift of at least 5 percentage points or relative lift of at least 35%;
- positive economic effect under the frozen stressed payoff proxy;
- positive effect in both pairs;
- positive effect in at least four development years;
- date-block bootstrap probability of positive effect at least 90%;
- false-discovery-rate adjusted q-value at most 0.10 across the complete single-factor atlas.

Failure means the family is descriptive only. No threshold refinement, direction rescue, pair rescue or year rescue is allowed.

## Interaction boundary

- maximum six interactions;
- each interaction must combine two non-redundant factor families;
- no three-way interactions;
- no continuous threshold search;
- no model family comparison until the interaction gate passes;
- no entry, stop, target, time-exit or position-structure changes.

## Explicit exclusions

This programme does not reopen:

- early-week retracement followed by HTF trend resumption;
- Monday/Tuesday retracement continuation;
- later weekly-transition continuation after 0.75 ATR displacement;
- the compact PDH/PDL liquidity-cluster challenger;
- T0–T3 entry optimisation;
- staged-entry policies;
- extended target or runner grids;
- pair, weekday, direction or year selection after inspection.

## Promotion boundary

The atlas may produce a replication candidate, not a validated strategy. Any candidate requires either:

1. genuinely fresh future EURUSD/GBPUSD data not used in the current programme; or
2. separately qualified cross-asset replication with an unchanged causal definition.

No Pine, alerts, sizing, paper trading or deployment is authorized from discovery attribution alone.
