# Asian Sweep Staged-Exit Research Contract v3.0

Date frozen: `2026-07-26`  
Branch: `agent/asia-sweep-staged-exit-research`  
Upstream execution decision: `FAIL_DISCOVERY_STOP_BEFORE_EXECUTION_VALIDATION`

## Research question

Does treating the Asian midpoint as TP1 rather than the final target convert the validated T5 reversal fingerprint into positive and stable executable expectancy?

This study changes only exit management. Signal selection, entry timing, threshold, source data, stop geometry and daily lockout remain unchanged.

## Interpretation boundary

The previous execution study rejected only this formulation:

> Enter after T5 and liquidate 100% at the Asian midpoint, otherwise stop or exit at 10:00 Amsterdam.

It did not test partial profit-taking followed by a runner.

## Frozen signal and entry

- instruments: EURUSD and GBPUSD;
- Asian range: `[00:00, 08:00)` Europe/Amsterdam;
- candidate sweeps: `[08:00, 10:00)`;
- decision landmark: T5, five completed minutes after the sweep;
- exact out-of-fold 2015–2019 T5 probabilities from run `30177831134`;
- exact probability threshold: `0.18252984704127595`;
- event-time policy only; retrospective weekly Hit@1 is prohibited;
- entry: `MKT_NEXT_OPEN`, first active BID/ASK minute open strictly after T5;
- maximum one filled trade per pair per Amsterdam date;
- unchanged original stop: `0.20 × Asian range` beyond the sweep extreme.

The two failed passive-entry variants are not reopened. This isolates whether staged exits improve the closest-to-neutral primary entry.

## Frozen position split

- initial position: `1.00` risk unit;
- TP1 fraction: `0.50`;
- runner fraction: `0.50`;
- no optimization of the split is authorized in this programme.

## TP1 rule

- TP1 price: Asian midpoint;
- TP1 must be touched on the executable quote side before 10:00 Amsterdam;
- if TP1 is not reached before 10:00, close the complete position on the final active M1 quote before 10:00;
- if the original stop and TP1 are both touched in the same M1 bar, score the original stop first for the complete position;
- TP1 is a limit exit at the midpoint price and realizes 50% of the position.

## Runner objective and horizon

After TP1:

- runner target: the opposite Asian-range boundary;
- runner time exit: final active M1 quote before 11:00 Amsterdam;
- if the original stop and runner target are both touched in the same M1 bar, score the active stop first;
- if TP1 and the opposite boundary are reached in the same bar without the stop, both targets are filled;
- no trailing stop, partial runner exits or alternative liquidity target is authorized.

The 11:00 endpoint is a conservative one-hour continuation audit after the primary 09:00–10:00 reversal window. A different horizon requires a new preregistration.

## Frozen runner-management variants

### `MIDPOINT_50_RUNNER_ORIGINAL_STOP`

After TP1, the runner retains the original adverse-barrier stop.

### `MIDPOINT_50_RUNNER_BE`

After TP1, the runner stop moves to the actual executable entry price.

Break-even activation rules:

- the break-even stop becomes active on the first subsequent active M1 bar after the TP1 bar;
- it is not retroactively active inside the TP1 bar;
- spread is already embedded in the entry and exit quote sides;
- no `BE+`, pip buffer or commission offset is permitted.

## Costs and fill ordering

- actual Dukascopy BID/ASK M1 quotes;
- market entry uses ask for longs and bid for shorts;
- long exits use bid; short exits use ask;
- spread is therefore embedded;
- stop and time exits receive additional slippage stresses of `0.10` and `0.25` pip;
- market entry also receives the same stress;
- target limit exits receive no additional slippage;
- missing or inactive quotes are not forward-filled;
- same-bar ambiguity is always resolved conservatively in favor of the active stop.

## R accounting

Initial risk is based on the complete position's executable entry-to-original-stop distance.

Total trade R is:

`0.50 × TP1-leg R + 0.50 × runner-leg R`.

The initial market-entry slippage applies to the complete position. Each leg's exit slippage is applied according to its own exit type.

The report must separately show:

- TP1 hit rate;
- runner target hit rate;
- runner stop/BE rate;
- runner time-exit rate;
- TP1-leg contribution;
- runner-leg contribution;
- total R under all cost assumptions.

## Research hierarchy

1. discovery: 2015–2019 only;
2. validation: 2020–2021 only if discovery passes;
3. first holdout: 2022–2023 only if validation passes;
4. final holdout: 2024–2025 only if the first holdout passes.

All later execution P&L remains unopened until authorized by the preceding frozen gate.

## Discovery gates

Each variant must independently satisfy all gates:

- at least 150 filled trades pooled;
- at least 50 filled trades per pair;
- expectancy greater than `+0.05R`;
- median annual expectancy above zero;
- positive expectancy in at least 4 of 5 years;
- positive expectancy on both pairs;
- maximum drawdown below `20R`;
- return/max-drawdown at least `1.50`;
- calendar-week bootstrap probability expectancy positive at least 95%;
- positive expectancy under `0.10` pip slippage stress.

Selection hierarchy:

1. evaluate `MIDPOINT_50_RUNNER_ORIGINAL_STOP` first;
2. freeze it if it passes every gate;
3. otherwise evaluate `MIDPOINT_50_RUNNER_BE`;
4. BE may replace it only if BE passes every gate and improves expectancy by at least `+0.03R` and return/drawdown by at least `+0.30`;
5. if neither passes, stop before 2020–2025.

## Explicit prohibitions

- no change to the model, threshold or entry;
- no EURUSD-only, weekday, year, sweep-side or score-bucket rescue;
- no TP1 fraction grid;
- no later runner horizon, New York-session exit or alternative TP2 in this programme;
- no trailing stop, BE buffer or partial runner management;
- no blending management variants by context;
- no continuation trades;
- no Pine, alerts, paper trading or deployment before all strategy gates pass.

## Required decision

The study must terminate with exactly one of:

- `PASS_STAGED_EXIT_DISCOVERY_AUTHORIZE_2020_2021_VALIDATION`;
- `FAIL_STAGED_EXIT_DISCOVERY_STOP_BEFORE_VALIDATION`.
