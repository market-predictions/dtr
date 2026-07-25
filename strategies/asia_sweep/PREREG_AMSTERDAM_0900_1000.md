# Preregistration — Asian Sweep Amsterdam 09:00–10:00

Date frozen: 2026-07-25  
Programme: `ASIAN_SWEEP_AMSTERDAM_0900_1000_V1`

## Status

This is a genuinely new, user-specified clock-window hypothesis after the broad ten-pair discovery formulation failed. It is not a retrospective rescue authorized by the earlier programme.

## Frozen hypothesis

For EURUSD and GBPUSD only, Asian-range first-boundary events whose causal state is confirmed between **09:00:00 inclusive and 10:00:00 exclusive in `Europe/Amsterdam`** may show positive 60-minute reversal value relative to matched non-rejection boundary events confirmed inside the same Amsterdam clock hour.

## Time handling

- Convert the timezone-aware state-detection timestamp to `Europe/Amsterdam`.
- Apply the exact half-open interval `[09:00, 10:00)`.
- Do not approximate the interval with fixed UTC or New York hours.
- Match controls by Amsterdam-local year, weekday and 30-minute bucket, so the non-overlapping US/EU DST weeks are handled correctly.

## Unchanged mechanics

- qualified Dukascopy BID/ASK M1 source artifacts;
- synchronized active midpoint OHLC;
- unchanged Asian Sweep auction-state detector;
- primary event state `REJECTION`;
- next-active-minute anchor after confirmation;
- reversal-signed 60-minute return divided by completed Asian-range width, capped at the existing London-window end;
- five distinct-date non-rejection controls;
- deterministic nearest matching on causal range percentile and breach depth;
- calendar-date block bootstrap and clustered sign permutation.

## Evidence partitions

- 2015–2019: post-hoc descriptive context only; no promotion authority.
- 2020–2021: first untouched confirmation set for this exact hypothesis.
- 2022 onward: unopened and blocked.

## All-required confirmation gates

1. at least 40 pooled matched events;
2. at least 15 matched events in each pair;
3. neither pair exceeds 70% of the pool;
4. pooled mean effect at least `+0.02` Asian-range fractions;
5. positive 95% date-block bootstrap lower bound;
6. one-sided clustered sign-permutation p-value at most `0.05`;
7. both EURUSD and GBPUSD positive;
8. both 2020 and 2021 positive.

Failure of any mandatory gate stops this Amsterdam-window formulation. No direction, weekday, month, volatility, pair or year rescue is authorized.

## Prohibitions

No entry, stop, target, spread, slippage, R multiple, strategy P&L, Pine, alert or deployment work is authorized in this stage.
