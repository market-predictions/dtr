# Asian Sweep Extended Target Selection Amendment v6.3

Date frozen: 2026-07-26  
Applies to v6.0–v6.2.

## 1. Model operation

Each T0/T1 extended target uses:

- elastic-net logistic and histogram-gradient-boosting families;
- the frozen causal feature sets from the early-entry programme;
- balanced sample weights computed inside each fit fold;
- five leave-one-year-out outer folds;
- Amsterdam-week grouped three-fold inner tuning;
- fold-local Platt calibration;
- the same elastic-net and HGB grids used by the early-entry frontier.

No target shares labels or fitted probabilities with another target.

## 2. Top/bottom construction

- quintiles are formed independently inside each outer test year;
- ties are broken by stable event ID ordering;
- all reported candidate metrics are pooled only after year-block quintiles are assigned.

## 3. Expected-value proxy

For a predicted success probability `p` and reward multiple `r`:

`EV = p × r − (1 − p)`

Reward multiple:

- `EXTENDED_1_5R_1300`: `1.5`;
- `EXTENDED_2R_1300`: `2.0`;
- `EXTENDED_3R_1600`: `3.0`;
- `OPPOSITE_ASIAN_BOUNDARY_1300`: event-specific executable reward/risk to the opposite Asian boundary;
- `LATE_TREND_HOLD_1600`: conservative `2.0R` proxy.

The primary EV predicate uses the median top-quintile proxy after `0.10` pip adverse entry and stop/market-exit stress. Fixed-R target reward is reduced by entry slippage divided by initial risk; the loss remains at least `−1R` plus applicable slippage.

## 4. Passing-target selection

If multiple targets pass:

1. choose highest median top-quintile stressed EV;
2. then higher target reward multiple;
3. then earlier landmark T0 before T1;
4. then HGB before elastic-net only as a deterministic final tie-break.

The selected target is frozen before any TP1/runner management P&L.

## 5. Staged feasibility selection

The staged feasibility study reports all six frozen policies. A development staged candidate passes only if the original Phase-B gate passes and it improves against the reference with the same initial timing:

- T0 staged policies compare with `T0_STATIC_025` on the identical T0-eligible event set;
- `T1_QUARTERS` compares with an internal `T1_STATIC_025` diagnostic on the identical T1-qualified event set;
- `T0_STATIC_100` is diagnostic and cannot be selected.

Among passing staged policies choose:

1. highest return/drawdown;
2. then highest expectancy;
3. then fewer mean tranches;
4. then lower maximum allocated risk.

No protected validation opens unless a candidate passes every gate.
