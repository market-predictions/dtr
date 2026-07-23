# Asian Sweep — First Proxy Baseline Result

**Work package:** `AS-WP-20260723-07`  
**Baseline:** `asia_sweep_first_proxy_baseline_20260723`  
**Period:** 2023-01-01 through 2024-06-30  
**Data:** private Dukascopy NQ/ES index-CFD BID proxies  
**Overall classification:** `NOT_PROMISING_CURRENT_SPEC`

## Executive conclusion

The current preregistered Asian Sweep specification does **not** show sufficient promise to justify lockbox testing or incremental filter optimization.

All four variants had negative pooled after-cost expectancy. More importantly, all four also had negative pooled gross expectancy before commission. The weakness is therefore not explained by commissions alone.

The current specification should stop here. Any continuation must be a separately preregistered conceptual redesign, not post-hoc selection of favorable windows, directions, years or instruments.

## Frozen assumptions

- Four preregistered variants; no tuning or subgroup selection.
- Development data only; no observation after 2024-06-30.
- Directionally pessimistic conversion from 0.001 proxy quotes to a 0.25 execution grid.
- One tick adverse entry slippage.
- One tick adverse stop slippage.
- One tick adverse market/time/data-exit slippage.
- `$2.25` commission per side.
- Stop-first intrabar collision policy.
- Fixed 2.0R target and exact window-end time exit.
- NQ proxy point value `$20`; ES proxy point value `$50`.

## Headline results

| Variant | NQ exits | NQ exp. | ES exits | ES exp. | Pooled exits | Pooled net R | Pooled exp. | Gross exp. | PF | Max DD | Classification |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| AS-A aggressive reclaim | 212 | -0.146R | 151 | -0.337R | 363 | -81.70R | -0.225R | -0.190R | 0.708 | 96.70R | NOT_PROMISING_CURRENT_SPEC |
| AS-B wick-qualified | 59 | -0.044R | 48 | -0.066R | 107 | -5.75R | -0.054R | -0.028R | 0.922 | 15.30R | NOT_PROMISING_CURRENT_SPEC |
| AS-C displacement | 108 | -0.126R | 83 | -0.161R | 191 | -26.93R | -0.141R | -0.124R | 0.789 | 42.13R | NOT_PROMISING_CURRENT_SPEC |
| AS-D failed retest | 11 | +0.099R | 18 | -0.338R | 29 | -5.00R | -0.172R | -0.155R | 0.702 | 8.96R | NOT_PROMISING_CURRENT_SPEC |

All 690 signals produced terminal exits. There were zero blocked and zero unresolved executions.

## Period stability

| Variant | 2023 net R | 2024 H1 net R |
|---|---:|---:|
| AS-A | -41.26R | -40.44R |
| AS-B | -5.74R | -0.01R |
| AS-C | -24.82R | -2.11R |
| AS-D | -7.99R | +2.99R |

No variant was positive in both periods.

## Interpretation

### AS-A aggressive reclaim

The control variant failed decisively in both proxies and both periods. Its pooled profit factor was only 0.708 and its drawdown reached 96.70R. The simple range-sweep-and-reclaim hypothesis, as currently defined, is not supported.

### AS-B wick-qualified

AS-B was the least negative version, but it was still negative in both proxies, negative before commission on the full pooled sample and below the required ES sample floor. Its 2024-H1 result was almost flat after cost, but 2023 remained materially negative. This is not a promotable edge.

A London-only or other subgroup rescue would be post-hoc and is prohibited by the baseline preregistration.

### AS-C displacement

Displacement confirmation did not improve the control sufficiently. It remained negative in both instruments and both development periods.

### AS-D failed retest

The NQ proxy result was positive, but it contained only 11 trades and was contradicted by the ES proxy. The pooled sample was negative and too small. This is noise-level evidence, not cross-market confirmation.

## Promise-gate assessment

No variant passed the preregistered requirements for:

- positive expectancy in both proxies;
- pooled expectancy of at least +0.05R;
- pooled profit factor of at least 1.10;
- positive results in both 2023 and 2024 H1;
- sufficient sample in each proxy;
- acceptable cross-instrument concentration.

## Data and interpretation boundary

These are development-period results on Dukascopy index-CFD BID proxies under a deliberately conservative normalization and execution scenario. They do not establish CME futures fills, bid/ask behavior, roll handling, volume validity or deployment performance.

That limitation does not rescue the current specification: the pooled gross expectancy was negative before commission for every variant. A more precise futures feed could change individual trades, but there is no positive baseline signal here that warrants opening the historical lockbox.

## Decision

`STOP_CURRENT_SPEC_NO_LOCKBOX_NO_POSTHOC_FILTER_MINING`

Permitted next action: only a separately preregistered conceptual redesign with a materially different market hypothesis. The current AS-A through AS-D family should not proceed to validation, portfolio combination, Pine implementation or deployment research.
