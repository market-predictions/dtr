# Asian Sweep Context and Regime Atlas — Final Decision

Date: 2026-07-26  
Decision: `FAIL_SINGLE_FACTOR_ATLAS_STOP_BEFORE_INTERACTIONS`

## Authoritative evidence

- GitHub Actions run: `30219172600`;
- evaluated scientific head: `1b3f9dcea472e6120123139343f6a6523cb77934`;
- decision artifact: `asia-sweep-context-regime-atlas-decision`;
- artifact digest: `sha256:9053ef2cbc8251a97468020a339d61dc997078e25aabb14d9c08e99ae9a0b95a`;
- general repository CI: success;
- isolated Asia Sweep CI: success;
- focused tests, lint, source restoration, 2015–2021 isolation, both pair-ledger builds, pooled attribution, bootstrap, permutation and FDR calculation completed successfully;
- the workflow failed only at the deliberate interaction-authorization step.

## Population

- EURUSD and GBPUSD;
- exact frozen T5 population;
- 2015–2021;
- 2,900 unique events across 1,661 dates;
- 2,899 events with positive remaining stressed reward and risk;
- baseline strict midpoint-success rate: 16.3448%;
- baseline stressed remaining-payoff proxy: -0.5684R.

The payoff measure is a conservative attribution proxy. It is not strategy execution P&L.

## Family decisions

| Family | States tested | Passing states | Best state | Hit-rate lift | Economic effect | Best q-value | Decision |
|---|---:|---:|---|---:|---:|---:|---|
| Higher-timeframe direction | 21 | 0 | D1 direction up | +0.62 pp | +0.0152R | 0.9817 | Descriptive only |
| Trend strength | 12 | 0 | D1 efficiency ordered | +2.54 pp | +0.0699R | 0.9817 | Descriptive only |
| Trend change | 6 | 0 | D1 trend decelerating | +1.16 pp | +0.0118R | 0.9817 | Descriptive only |
| Volatility | 21 | 0 | realized volatility compressed | +1.05 pp | +0.0343R | 0.9817 | Descriptive only |
| Causal location | 38 | 0 | above prior-day range | +0.16 pp | +0.0817R | 0.9817 | Descriptive only |
| Session/calendar | 8 | 1 | sweep 09:00–09:29 Amsterdam | +9.49 pp | +0.1737R | 0.0168 | Replication candidate only |

None of the requested higher-timeframe, trend, volatility or location families passed the complete frozen standard.

## The only passing attribution state

State: `sweep_half_hour::0900_0929`

- 600 events and 155 strict successes;
- 25.8333% success rate versus 16.3448% pooled baseline;
- +9.4885 percentage-point absolute lift;
- +58.052% relative lift;
- mean stressed payoff proxy -0.3947R versus -0.5684R baseline;
- +0.1737R relative economic effect;
- positive relative effect in both pairs and all seven years;
- bootstrap probability of positive relative economic effect: 99.98%;
- bootstrap 10th percentile: +0.1162R;
- clustered permutation p-value: 0.0004;
- full-atlas FDR q-value: 0.0168.

### Pair attribution

| Pair | Events | Success rate | Mean payoff proxy | Relative economic effect |
|---|---:|---:|---:|---:|
| EURUSD | 316 | 24.37% | -0.4605R | +0.1240R |
| GBPUSD | 284 | 27.46% | -0.3214R | +0.2308R |

### Year attribution

The relative effect was positive in every year from 2015 through 2021. The absolute payoff proxy remained negative in every year, including the strongest year, 2021, at -0.1725R.

## Interpretation

The 09:00–09:29 state is a robust attribution signal inside the frozen T5 population: later sweeps produced better strict midpoint-completion rates and a less-negative remaining-payoff distribution.

It is not evidence of an executable profitable strategy:

- absolute stressed payoff remained -0.3947R;
- the study did not simulate a complete event-time trading policy;
- the time state was discovered inside already-inspected 2015–2021 evidence;
- 2022–2025 cannot be relabelled as untouched regime validation because those years were used by the completed fingerprint programme;
- prior broader 09:00–10:00 sweep/rejection research also failed its own distinct untouched confirmation, so no time-window promotion is inferred from this attribution result.

## Binding decision

`FAIL_SINGLE_FACTOR_ATLAS_STOP_BEFORE_INTERACTIONS`

Consequences:

- no two-factor interaction outcome is opened;
- no regime-aware router model is opened;
- no entry, stop, target, runner or position-structure research is reopened;
- no higher-timeframe, trend, volatility, location, pair, year, direction or weekday rescue is permitted;
- the 09:00–09:29 state may be retained only as a future unchanged replication hypothesis;
- no Pine, alerts, sizing, paper trading or deployment is authorized.

## Programme conclusion

The completed broad atlas does not support the hypothesis that coarse higher-timeframe direction, trend strength/change, volatility state or prior-day/prior-week location provides a sufficiently strong and stable standalone gate for this Asian Sweep T5 architecture.

The only strong contextual discriminator is intraday timing, and even that improves a negative payoff distribution rather than creating positive expectancy. The current regime-atlas path is therefore closed before interactions.
