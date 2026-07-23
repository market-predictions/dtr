# USA500 Baseline Discovery Programme — 2026-07-23

## Decision

`NO_VIABLE_USA500_CORE_BASELINE`

The frozen Day Trader Rauf core logic does not produce a sufficiently robust, cost-tolerant USA500 proxy baseline over 2022–2025. London-only is the only promising session arm, but it fails the preregistered year-stability and concentration gates and is negative in both 2022 and 2025. It remains an exploratory diagnostic, not a promoted baseline.

This study uses Dukascopy `USA500.IDX/USD` one-minute bid-CFD proxy data. It is not CME ES futures validation.

## Evidence hierarchy

1. USA500 unfiltered core reference.
2. Frozen Monday × Asia factorial.
3. Bounded session decomposition.
4. Fixed context diagnostics.
5. One-at-a-time event diagnostics.
6. NQ E6 and NQ E6 no-FOMC retained as external controls only.

## Stage 1 — Monday × Asia factorial

| Arm | Trades | Net R | Expectancy | 2-tick expectancy | Max DD | Return/DD |
|---|---:|---:|---:|---:|---:|---:|
| Tue–Fri, all sessions | 601 | -19.56 | -0.033R | -0.086R | 31.72R | -0.62 |
| Mon–Fri, all sessions | 747 | -24.83 | -0.033R | -0.088R | 36.70R | -0.68 |
| Tue–Fri, no Asia | 470 | -2.25 | -0.005R | -0.054R | 20.31R | -0.11 |
| Mon–Fri, no Asia | 573 | -3.80 | -0.007R | -0.056R | 21.82R | -0.17 |

Adding Monday worsened the portfolio. Removing Asia improved net R and drawdown materially, but neither no-Asia arm became profitable after moderate execution costs or stable across years. No Stage 1 arm passed.

## Stage 1B — session decomposition

| Arm | Trades | Net R | Expectancy | 2-tick expectancy | 4-tick expectancy | Max DD | Return/DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| All sessions | 601 | -19.56 | -0.033R | -0.086R | -0.194R | 31.72R | -0.62 |
| London only | 253 | **+16.98** | **+0.067R** | **+0.007R** | -0.113R | 15.47R | **1.10** |
| New York only | 230 | -24.86 | -0.108R | -0.144R | -0.216R | 29.17R | -0.85 |
| Asia only | 145 | -16.08 | -0.111R | -0.181R | -0.320R | 25.10R | -0.64 |
| London + Asia | 384 | -0.33 | -0.001R | -0.065R | -0.193R | 20.27R | -0.02 |
| Asia + New York | 375 | -40.94 | -0.109R | -0.158R | -0.256R | 49.56R | -0.83 |

London-only improved net R by 36.54R versus all sessions. The paired date-block interval was -4.46R to +77.37R, so uncertainty still crossed zero. More importantly, annual results were:

- 2022: -2.72R
- 2023: +13.16R
- 2024: +12.80R
- 2025: -6.26R

The arm therefore failed the frozen requirement for at least three positive years and non-negative 2025 performance. Its positive result is concentrated in 2023–2024 and becomes negative at four ticks per side.

## Context diagnostics

Starting from the all-session reference, the only positive fixed context arm was exclusion of compressed initial ranges:

- 406 trades;
- +3.49R;
- +0.009R normal-cost expectancy;
- -0.040R at two ticks per side;
- 18.995R maximum drawdown;
- positive only in 2023 and 2025.

It failed cost robustness and year stability. The prior-day-extreme E6 transfer rule was positive from 2023 through 2025 in aggregate but lost 21.91R in 2022, producing -6.15R over the full sample. This indicates material regime dependence rather than a universal ES/USA500 filter.

No context candidate was promoted. Interaction searches were prohibited and were not run.

## Event diagnostics

No FOMC, CPI or NFP exclusion improved the all-session core into a viable strategy. Removing monthly option-expiration Fridays improved net R by 5.85R, but the resulting portfolio remained negative at -13.71R with -0.078R two-tick expectancy. It is not a usable event-policy candidate.

Because no session baseline passed Stage 1B, the preregistered stop rule prevented context or event optimization on London-only.

## Comparison with the NQ transfer controls

The earlier 2023–2025 NQ-derived E6 transfer test was positive on USA500. The full-period diagnostic explains why that was incomplete:

- E6 transfer, 2023–2025: approximately +15.76R in this broader reconstruction;
- E6 transfer, 2022: -21.91R;
- E6 transfer, 2022–2025: -6.15R.

Thus, the NQ-derived filter transferred during 2023–2025 but failed in the 2022 bear-market regime. The longer proxy sample materially changes the conclusion.

## Independent review

Two separate verification layers passed:

1. The original factorial/context/event programme was independently recalculated from saved trade streams and audited against the roadmap.
2. The Stage 1B session decomposition was independently re-sequenced from the complete cached signal-trade stream. All metrics and paired effects reproduced exactly, and the stop rule was confirmed.

## Strategic conclusion

The current DTR core is not yet a multi-index strategy. On USA500:

- London contains a plausible effect;
- New York and Asia are structurally harmful under the current core;
- the London effect is regime-dependent and execution-fragile;
- no fixed context or event rule repairs the instability without overfitting.

The correct action is not to force a profitable USA500 configuration from this sample. The next legitimate USA500/ES work should be one of:

1. acquire actual contract-audited ES futures data and test whether the 2022/2025 weakness is proxy-specific;
2. develop a new ES-specific core using nested chronological validation, with 2022–2023 development, 2024 selection confirmation and 2025 locked evaluation;
3. investigate why the reversal mechanism works in London but fails in New York and Asia before changing parameters.

No Pine, live sizing or deployment is authorized.
