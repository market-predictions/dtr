# Asian Sweep Staged Reversal Policies — Amendment v6.4

Date: 2026-07-26
State: FROZEN_BEFORE_STAGED_PNL
Branch: `agent/asia-sweep-staged-reversal`
Development: EURUSD and GBPUSD, 2015–2019
Protected: 2020–2025

## Purpose

Define the exact six staged-reversal policies authorized by the passing Phase A triage decision before any staged return is inspected.

## Common trade geometry

This work package isolates entry and state-transition economics. Every policy uses:

- reversal direction: upper sweep short; lower sweep long;
- adverse stop: `0.20 * Asian range` beyond the sweep extreme;
- target: Asian midpoint;
- target and stop active immediately after each entry/add;
- final time exit: last active quote before 10:00 Amsterdam;
- actual BID/ASK execution;
- stop-first resolution when stop and midpoint touch in the same M1 bar;
- one completed reversal attempt per pair/day;
- no continuation trade or same-day direction flip.

The midpoint is deliberately the full exit in this work package because runner management is tested only after an extended-reversal model passes. This prevents entry and target optimization from being mixed.

## Risk accounting

- `1.00R` is the maximum daily initial stop risk for a pair;
- each entry/add is sized so its loss at the common frozen stop equals its assigned risk allocation;
- total assigned open risk may never exceed `1.00R`;
- reductions close the specified fraction of open units at the next active quote;
- total trade P&L is the sum of leg P&L in daily R units;
- market entries and state exits are stressed by +0.10 and +0.25 pip per execution leg;
- midpoint limit exits receive no extra slippage; stop/time exits are stressed adversely.

## Causal landmarks

- T0 provisional entry uses the first active open after the sweep bar;
- T2 and T3 actions use the first active open after their completed landmark;
- if stop or midpoint resolves before a later action, that action is not executed;
- continuation always exits and blocks further adds;
- a T3 action cannot reopen a position closed by T2 continuation;
- missing later-landmark rows mean the event was already resolved and no action is taken.

## Daily selection

### Policies with a T0 provisional entry

Use the first valid T0 event for the pair/day. No later event may replace it, even when the first attempt exits early.

### Policies without T0 provisional entry

Remain flat until the first event for that pair/day that produces a T2 `REVERSAL` decision. Later events are ignored after that first entry.

This selection is chronological and causal. No weekly or daily hindsight ranking is used.

## Six frozen policies

### `CONSERVATIVE_NO_T0`

- T0: flat;
- first T2 REVERSAL: enter `0.50R`;
- T2 CONTINUATION or ABSTAIN while flat: no trade;
- T3 REVERSAL: add `0.25R`, maximum `0.75R`;
- T3 CONTINUATION or ABSTAIN: exit full position.

### `CONSERVATIVE_T0_025`

- first valid T0: enter `0.25R` provisional;
- T2 REVERSAL: add `0.25R`, total `0.50R`;
- T2 CONTINUATION: exit full position;
- T2 ABSTAIN: hold `0.25R`;
- T3 REVERSAL: add `0.25R`, maximum `0.75R`;
- T3 CONTINUATION or ABSTAIN: exit full position.

### `BALANCED_NO_T0`

- T0: flat;
- first T2 REVERSAL: enter `0.75R`;
- T2 CONTINUATION or ABSTAIN while flat: no trade;
- T3 REVERSAL: add `0.25R`, maximum `1.00R`;
- T3 CONTINUATION: exit full position;
- T3 ABSTAIN: reduce 50% of open units and retain the remainder.

### `BALANCED_T0_025`

- first valid T0: enter `0.25R` provisional;
- T2 REVERSAL: add `0.50R`, total `0.75R`;
- T2 CONTINUATION: exit full position;
- T2 ABSTAIN: reduce 50% of open units;
- T3 REVERSAL: add up to total assigned risk `1.00R`;
- T3 CONTINUATION: exit full position;
- T3 ABSTAIN: retain the reduced provisional position.

### `AGGRESSIVE_NO_T0`

- T0: flat;
- first T2 REVERSAL: enter `1.00R`;
- T2 CONTINUATION or ABSTAIN while flat: no trade;
- T3 REVERSAL: hold full position;
- T3 CONTINUATION: exit full position;
- T3 ABSTAIN: reduce 50% of open units.

### `AGGRESSIVE_T0_050`

- first valid T0: enter `0.50R` provisional;
- T2 REVERSAL: add `0.50R`, total `1.00R`;
- T2 CONTINUATION: exit full position;
- T2 ABSTAIN: hold `0.50R`;
- T3 REVERSAL: hold full position;
- T3 CONTINUATION: exit full position;
- T3 ABSTAIN: reduce 50% of open units.

## Selection and gates

All six policies are simulated on the full 2015–2019 discovery partition. Promotion uses leave-one-year-out policy selection:

1. for each held-out year, select among policies passing inner four-year minimum gates;
2. inner gates: positive +0.10-pip expectancy, positive both pairs, positive at least three of four years, maximum drawdown <=12R and at least 200 completed trades;
3. selection score: stressed expectancy, then return/drawdown, then lower turnover, then policy order above;
4. evaluate the selected policy only on the held-out year;
5. pool all out-of-fold selected trades;
6. freeze the stable modal policy only when selected in at least three of five folds.

Final staged-entry gates remain those in v6.0:

- +0.10-pip stressed expectancy >0R;
- return/max drawdown >=1.5;
- positive net R in both pairs and at least four of five held-out years;
- no single pair/year contributes >45% of positive net R;
- maximum drawdown <=12R;
- at least 250 completed trades;
- survives +0.25-pip stress;
- calendar-week bootstrap probability of positive expectancy >=0.90.

## Stop rules

- no policy parameter, target, stop or daily-selection change after this amendment;
- if the nested result fails, 2020–2025 staged-reversal P&L remains unopened;
- no pair-only or policy-blend rescue;
- runner and TP1 fraction research remains delegated to the extended-reversal branch.
