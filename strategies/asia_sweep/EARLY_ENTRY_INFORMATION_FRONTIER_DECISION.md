# Asian Sweep Early-Entry Information Frontier — Decision

Date: `2026-07-26`  
Actions run: `30197859712`  
Evaluated head: `bb8a160cde7dd0c4771e4c2c760eb62e537ddcd2`  
Decision artifact: `sha256:11af76fba3e5167f838ddda6f7840fb26e7cc6829646187435c2fa985ddd9bb8`

## Decision

`FAIL_EARLY_ENTRY_INFORMATION_FRONTIER_STOP_BEFORE_POLICY_PNL`

No causal T0, T1, T2 or T3 candidate satisfied the complete frozen information-and-payoff gate on grouped 2015–2019 out-of-fold evidence.

The 2020–2025 early-entry partitions remain unopened. No entry landmark, probability model or position-management structure is authorized for execution-policy P&L.

## Binding position structures

The user's requested payoff structures are frozen for a conditional phase 2:

1. `TP1_50_RUNNER_50` — 50% at the Asian midpoint and 50% retained;
2. `TP1_25_RUNNER_75` — 25% at the midpoint and 75% retained;
3. `NO_TP1_FULL_RUNNER` — no midpoint reduction and 100% retained.

Phase 1 was explicitly prohibited from using realized policy P&L to select a landmark. Because no landmark passed, none of these three structures was opened. This prevents partial fractions or a full runner from rescuing a weak entry signal after outcome inspection.

## Landmark semantics

- `T0`: sweep-bar close; next active quote is the hypothetical entry;
- `T1`: one completed active M1 bar after the sweep;
- `T2`: two completed active bars after the sweep;
- `T3`: three completed active bars after the sweep;
- `LEGACY_T5`: exact frozen five-bar-inclusive confirmation snapshot used by the validated fingerprint programme.

The old `T5` implementation normally closes at sweep minute `m+4` and enters at `m+5`; it is therefore labeled `LEGACY_T5` here rather than silently redefined.

## Population

| Landmark | Eligible events | Base midpoint-success rate | Median executable R:R to midpoint |
|---|---:|---:|---:|
| T0 | `2,506` | `23.86%` | `2.21R` |
| T1 | `2,393` | `24.95%` | `2.00R` |
| T2 | `2,254` | `26.44%` | `1.92R` |
| T3 | `2,162` | `27.38%` | `1.86R` |
| LEGACY_T5 | `2,065` | `16.22%` | `1.75R` |

The landmark population becomes smaller because events already resolved at the midpoint or adverse barrier are removed before each later decision point. Model comparisons are therefore conditional landmark decisions, not identical-population score comparisons.

## Nonlinear information-payoff frontier

The nonlinear HGB challenger was the strongest family at each pre-T5 landmark.

| Landmark | PR-AUC lift over base | Top-quintile success | Top lift | Bottom/base ratio | Median top-quintile R:R | Top candidates with ≥1.5R | Median stressed EV proxy |
|---|---:|---:|---:|---:|---:|---:|---:|
| T0 | `+25.15%` | `31.67%` | `1.33×` | `0.39×` | `1.97R` | `78.09%` | `-0.015R` |
| T1 | `+43.91%` | `38.54%` | `1.54×` | `0.41×` | `1.36R` | `39.38%` | `-0.112R` |
| T2 | `+56.83%` | `42.92%` | `1.62×` | `0.28×` | `0.99R` | `18.81%` | `-0.110R` |
| T3 | `+69.07%` | `47.00%` | `1.72×` | `0.29×` | `0.85R` | `13.13%` | `-0.121R` |
| LEGACY_T5 | `+103.31%` | `32.61%` | `2.01×` | `0.33×` | `1.07R` | `26.09%` | `-0.309R` |

The frozen primary gates required, among other conditions:

- PR-AUC lift of at least 50%;
- top-quintile lift of at least 1.75×;
- median top-quintile R:R of at least 1.0;
- at least 35% of top candidates retaining 1.5R;
- positive median 0.10-pip-stressed expected-value proxy;
- both-pair and at least four-year breadth.

No candidate passed every predicate.

## Exact failure anatomy

### T0 — payoff remains, information is inadequate

T0 preserved almost `2R` median reward/risk in the highest-scored quintile and 78% of those candidates retained at least `1.5R`. But:

- PR-AUC lift was only `25.15%`;
- top-quintile lift was only `1.33×`;
- stressed expected-value proxy remained slightly negative.

The sweep bar alone does not identify genuine reversals reliably enough.

### T1 — first response helps, but not enough

T1 improved discrimination, but top-quintile lift was only `1.54×`. Median top-quintile R:R had already fallen to `1.36R`, and the stressed expected-value proxy remained negative.

### T2 — predictive gate begins to pass as payoff deteriorates

T2 exceeded the PR-AUC-lift gate and remained positive on both pairs and all five years. However:

- top lift was `1.62×`, below `1.75×`;
- nonlinear top candidates had only `0.99R` median reward/risk;
- only 18.81% retained at least `1.5R`;
- stressed expected-value proxy was negative.

### T3 — strongest early information, economically late

T3 HGB was the strongest pre-T5 model:

- PR-AUC lift `+69.07%`;
- top-quintile success `47.00%` versus `27.38%` base;
- bottom quintile only `7.82%` success;
- both pairs and all five years showed positive top-quintile lift;
- pair-week Hit@1 improved by `67.27%` relative to the candidate base rate.

But the highest-scored candidates retained only `0.85R` median reward/risk to the midpoint, and just `13.13%` retained `1.5R`. Its stressed expected-value proxy remained `-0.121R`.

T3 therefore confirms the same structural problem observed at T5: confirmation quality rises after price has already consumed too much of the available move.

## Breadth of T3 HGB

| Segment | Base success | Top-quintile success |
|---|---:|---:|
| EURUSD | `25.87%` | `46.01%` |
| GBPUSD | `28.90%` | `47.96%` |
| 2015 | `30.68%` | `50.55%` |
| 2016 | `26.92%` | `49.40%` |
| 2017 | `25.44%` | `41.25%` |
| 2018 | `26.19%` | `44.09%` |
| 2019 | `27.42%` | `49.43%` |
| Lower sweep / long reversal | `26.49%` | `50.93%` |
| Upper sweep / short reversal | `28.29%` | `43.12%` |

The failure is not caused by a lack of pair or year breadth. It is caused by the information-payoff tradeoff.

## Independent verification

The retained evidence was independently reconstructed and checked:

- `11,381` landmark rows;
- EURUSD: `5,663` rows and `1,220` unique T0 events;
- GBPUSD: `5,718` rows and `1,286` unique T0 events;
- zero duplicate event-landmark keys;
- years exactly 2015–2019;
- all next-open entries matched the original active BID/ASK minute files;
- zero quote-side discrepancies;
- zero landmark/entry ordering discrepancies;
- zero stop, reward, risk or R:R arithmetic discrepancies;
- target labels exactly reproduced from midpoint-before-barrier first passage after each landmark;
- all nine PR-AUC, ROC-AUC, Brier, quintile, R:R and expected-value metrics reproduced to floating-point tolerance;
- each candidate contained one out-of-fold probability per event and no duplicate event ID.

No source, timing, feature-window, quote, target, geometry, model-aggregation or reporting defect explains the negative decision.

## Interpretation boundary

This result rejects the current landmark architecture:

> choose a single entry after T0, T1, T2 or T3 using a landmark-specific reversal classifier, with viability judged against the Asian midpoint and the original adverse barrier.

It does not establish that every earlier execution architecture must fail. It specifically shows that a one-shot entry creates a difficult frontier:

- enter early enough for attractive R:R and prediction quality is weak;
- wait for enough confirmation and the remaining midpoint payoff is too small.

## Disposition

- stop before phase-2 execution-policy P&L;
- do not test 50%, 25% or 0% TP1 as a post-hoc rescue on this failed landmark family;
- keep 2020–2025 unopened;
- no pair, weekday, side, range-width or threshold rescue;
- no Pine, alerts, paper trading or deployment.

## Valid next hypotheses

1. **Direct continuation/fake-rejection triage** — model reversal, continuation and abstention directly rather than forcing a reversal entry.
2. **True staged information entry** — a separate preregistered architecture with small provisional risk at T0/T1, additions only as confirmation develops, and rapid cancellation on adverse evidence. This is not equivalent to selecting one fixed landmark.
3. **Target-specific directional model** — train directly on extended directional continuation after reversal rather than using midpoint success as the sole predictive objective. This is required before a no-TP1/full-runner policy can be assessed fairly.

No new hypothesis may reuse 2015–2019 as untouched evidence, and none may open 2020–2025 before its complete contract is frozen.
