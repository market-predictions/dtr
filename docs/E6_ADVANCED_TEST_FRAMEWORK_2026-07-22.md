# E6 Advanced Test Framework — 2026-07-22

## Decision state

`FRAMEWORK_FROZEN_EXECUTION_NOT_STARTED`

E6 is adopted as the **working research baseline** for the next advanced-test programme. It does not replace the unfiltered timing-corrected comparator as the project control and it is not authorized for deployment.

## Baseline hierarchy

### Engine regression benchmark

`DTR_PY_NQ_CANDIDATE_0_1_CAUSAL_GAP`

- 495 trades;
- 86.004761R net;
- 0.173747R expectancy.

Purpose: detect unintended execution-engine changes.

### Non-selectable research control

`DTR_CAUSAL_BAR_CLOSE_RANGE_SHIFT_MINUS1`

- 477 trades;
- 42.577515R net;
- 0.089261R expectancy;
- 16.426493R maximum drawdown.

Purpose: remain visible in every advanced-test report so filtering gains are not evaluated only inside a historically selected subset.

### Working research baseline

`E6_EXCLUDE_NEAR_PRIOR_DAY_DIRECTIONAL_EXTREME`

- Tuesday–Friday;
- Asia, London and New York;
- exclude a setup when its directional session-range extreme is within 0.25 completed-D1 ATR of the corresponding prior-day extreme;
- 304 trades;
- 48.937550R net;
- 0.160979R expectancy;
- 8.632571R maximum drawdown;
- 5.668942 return/DD.

All strategy parameters, timing correction, gap policy, costs, targets and exits remain frozen.

## Strategic question

Can causal information available between the initial sweep and entry, the structural reward space ahead of the entry, or portfolio sequencing improve E6 in a way that is economically meaningful, robust across time and sessions, and simple enough to reproduce in Pine Script?

The goal is not to maximize historical net R. The goal is to identify at most one or two coherent fresh-OOS challengers and reject the rest.

## Non-negotiable controls

- No E6 threshold change.
- No weekday or session search.
- No entry, stop, target, partial, breakeven or time-exit change.
- No dynamic threshold selected after inspecting results.
- No more than one predeclared two-factor interaction.
- No third-factor interaction.
- No historical result may promote a rule directly into Pine or production.
- The unfiltered comparator and E6 A0 must reproduce exactly before every execution block.
- The original NQ archive checksum and all generated compact artifact hashes must be recorded.

# Execution blocks

## Block 0 — Provenance and regression

Before inspecting any new result:

1. verify the registered market-data SHA-256;
2. reproduce the 477-trade unfiltered comparator exactly;
3. reproduce E6 exactly at 304 trades and 48.937550R;
4. verify the frozen session windows, Tuesday–Friday calendar, one-minute execution, causal gap liquidation, one tick slippage each side and $2.25 commission each side;
5. emit deterministic signal and trade-stream hashes.

Failure stops the programme.

## Block 1 — E6 mechanism audit

This block is diagnostic and cannot select a new filter.

Compare E6-kept signals with the E6-rejected near-prior-day-extreme cohort. Report both raw and session × year × direction stratified comparisons for:

- expectancy, median R, win rate and profit factor;
- MFE, MAE, stop-first rate, TP1 hit rate and TP2 hit rate;
- time to MFE, holding time and adverse excursion during the first 15 and 30 minutes;
- initial risk points and friction measured in R;
- sweep-to-reclaim, reclaim-to-BOS and sweep-to-entry latency;
- BOS body fraction, directional close location and range/ATR;
- structural clearance to TP1 and TP2;
- session, direction, year and half-year concentration.

The mechanism is classified as `SUPPORTED`, `MIXED` or `UNEXPLAINED`. No threshold may be created from this audit.

## Block 2 — Setup-path quality family

All features are causal at entry. Three fixed candidate rules are allowed.

### P1 — Total path latency

`P1_TOTAL_PATH_LE_12_BARS`

- `sweep_to_entry_bars = entry_index - sweep_index`;
- retain signals with `sweep_to_entry_bars <= 12` five-minute bars;
- rationale: reject reversals that require more than 60 minutes to complete the sweep-to-entry sequence.

### P2 — BOS quality

`P2_BOS_QUALITY_2_OF_3`

A BOS bar receives one point for each condition:

1. `abs(close - open) / (high - low) >= 0.60`;
2. directional close location is at least 0.75: `(close-low)/(high-low)` for longs and `(high-close)/(high-low)` for shorts;
3. true range is at least `1.00 × ATR14` known on that bar.

Retain signals with at least two points. Zero-range bars fail safely.

### P3 — Entry extension

`P3_ENTRY_EXTENSION_LE_0_35R`

- compute frozen initial risk from the normal slipped entry and frozen stop;
- `entry_extension_r = abs(entry_price_raw - pivot) / initial_risk_points`;
- retain signals with `entry_extension_r <= 0.35`.

No alternative latency, score or extension threshold is permitted on the current sample.

## Block 3 — Reward-space geometry family

Levels must be fully known at entry. Directionally ahead levels are drawn from:

- the opposite boundary of the active session range;
- completed prior-day midpoint and opposite extreme;
- completed prior-week midpoint and opposite extreme.

Levels behind the entry are ignored. If no level is ahead, clearance is treated as infinite.

`structural_clearance_r` is the distance to the nearest directionally ahead level divided by frozen initial risk points.

### R1 — TP1 clearance

`R1_CLEAR_TO_TP1`

Retain signals with `structural_clearance_r >= 1.25`, matching the frozen TP1 objective.

### R2 — Runner clearance

`R2_CLEAR_TO_RUNNER`

Retain signals with `structural_clearance_r >= 2.50`, matching the frozen runner objective. This rule is shadow-only unless it retains at least 250 trades.

### Frozen interaction

`I1_BOS_QUALITY_AND_TP1_CLEARANCE`

Apply P2 and R1 together. This is the only interaction authorized and remains shadow-only on the historical sample.

## Block 4 — Portfolio sequencing family

No signal logic changes. Compare four fixed execution architectures:

### S0 — Current global sequencing

One global open position at a time. This is E6 A0.

### S1 — First trade per ETH market date

Accept only the first eligible E6 trade whose entry occurs in each ETH market date beginning at 18:00 ET.

### S2 — Sixty-minute cooldown

After any exit, reject new entries for 60 minutes.

### S3 — Session sleeves

Maintain independent Asia, London and New York sleeves, one open trade per sleeve. Risk-normalized portfolio reporting assigns one-third of the normal risk budget to each sleeve so maximum simultaneous planned risk does not exceed the S0 budget.

S3 must report both raw trade statistics and normalized portfolio equity. It may not be compared on unscaled net R.

## Block 5 — Event, holiday and rollover stress

This block is attribution-only on the current sample. Dates must come from official Federal Reserve, US Bureau of Labor Statistics and CME calendars.

Report E6 behavior on and off:

- FOMC announcement dates;
- CPI release dates;
- Employment Situation/NFP release dates;
- quarterly equity-index futures expiration dates and the preceding five business days;
- early-close and shortened-session dates;
- detected contract-roll discontinuity windows.

No event exclusion becomes a candidate from 2023–2025 alone. Any event rule requires separate preregistration and new or longer data.

## Block 6 — Equity and risk stress

For E6 and every surviving challenger, report fixed-fraction equity paths at:

- 0.50%;
- 1.00%;
- 1.50%

of current equity risked per trade.

Run normal-cost, two-tick-each-side and four-tick-each-side stress. Use market-date and month-block resampling to report:

- median and 5th/95th percentile final equity;
- median and 95th percentile maximum drawdown;
- longest losing sequence;
- probability of 10%, 20% and 30% drawdown;
- time under water.

Risk fractions are scenario outputs, not optimization candidates.

# Required metrics for every selectable arm

- qualifying signals and executed trades;
- net R, expectancy, median R, profit factor and win rate;
- maximum drawdown and return/DD;
- R per 100 eligible sessions;
- normal, two-tick-each-side and four-tick-each-side costs;
- calendar year and half-year net R;
- Asia, London and New York attribution;
- long/short attribution;
- maximum session and half-year contribution share;
- paired session-date return difference versus E6;
- market-date and month-block confidence intervals;
- familywise-adjusted incremental test within each family;
- trade-stream hash and changed-trade attribution.

# Historical classification gates

Historical evidence cannot promote a strategy. It can only classify a rule for future testing.

## `FRESH_OOS_CHALLENGER`

All conditions must hold:

- at least 250 executed trades;
- expectancy at least E6 + 0.03R, or maximum drawdown at most 80% of E6 while expectancy is no worse than E6 by more than 0.01R;
- return/DD at least 1.15 × E6;
- positive two-tick-each-side expectancy and no more than 0.02R below E6 under that stress;
- positive net R in all three years, or two positive years with the worst year no lower than -3R;
- maximum session and half-year net contribution shares no greater than 60%;
- familywise-adjusted incremental p-value no greater than 0.05;
- no unexplained portfolio-sequencing or causality discrepancy.

## `SHADOW_ONLY`

A coherent effect exists, but one or more promotion gates fail, or the arm retains 180–249 trades.

## `REJECT`

The arm has no meaningful effect, worsens efficiency, fails cost robustness, is highly concentrated, retains fewer than 180 trades, or depends on an unexplained implementation artifact.

## `DIAGNOSTIC_ONLY`

Used for mechanism, events, risk scenarios and other non-selectable evidence.

# Multiplicity and stopping rules

- P1–P3 form one family.
- R1–R2 form one family.
- S1–S3 form one family.
- I1 is reported separately as shadow-only.
- Use a joint market-date block max-t adjustment within each family.
- Do not search neighboring thresholds.
- Do not create a new rule from the strongest descriptive bucket.
- Stop a family when all candidates are `REJECT`.
- At most one candidate per family can advance to fresh-OOS status.
- Do not combine family winners on the current sample beyond frozen I1.

# Execution sequence

1. Block 0 regression.
2. Block 1 E6 mechanism audit.
3. Blocks 2 and 3 in one frozen run.
4. Independent reconstruction and decision checkpoint.
5. Block 4 sequencing in a separate run.
6. Block 5 event/roll attribution.
7. Block 6 risk/equity stress for E6 and surviving challengers.

No result from a later block may change the definitions of an earlier or later block.

# Expected deliverables

Each execution work package must include:

- claim and handover;
- immutable preregistration;
- compact CSV/JSON evidence;
- full human-readable report;
- independent review;
- deterministic repeat and hashes;
- changelog, roadmap, status and decision-ledger update;
- explicit statement that no Pine or deployment authorization follows from historical evidence.
