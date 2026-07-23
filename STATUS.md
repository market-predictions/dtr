# DTR Optimization Lab Status

## Current work package

`DTR-USA500-WP-20260723-20 — USA500 baseline discovery programme`

Status: **completed and independently reviewed**

Decision: `NO_VIABLE_USA500_CORE_BASELINE`

Draft PR: #21 (`agent/usa500-baseline-discovery`)

## Evidence hierarchy

### Execution regression benchmark

`DTR_PY_NQ_CANDIDATE_0_1_CAUSAL_GAP`

- 495 trades;
- 86.004761R net;
- 0.173747R expectancy.

This bar-open-labelled result remains a historical execution regression only.

### Scientific NQ reference control

`DTR_CAUSAL_BAR_CLOSE_RANGE_SHIFT_MINUS1`

- 477 trades;
- 42.577515R net;
- 0.089261R expectancy;
- 16.426493R maximum drawdown.

The maintenance-boundary census supports bar-close labels: 732 normal `17:00 → 18:01` pairs, zero normal `16:59 → 18:00` pairs, and no candidate reopen at exactly 18:00. Decision: `SUPPORT_BAR_CLOSE_RETAIN_SHIFT_MINUS_ONE`.

### Frozen historical NQ challenger

`E6_EXCLUDE_NEAR_PRIOR_DAY_DIRECTIONAL_EXTREME`

- 304 trades;
- 48.937550R net;
- 0.160979R expectancy.

E6 remains a historically suggestive challenger. It is not statistically promoted over the unfiltered reference.

### Working NQ policy candidate

`E6_NO_FOMC_DAY`

- 291 trades;
- 53.483342R net;
- 0.183792R expectancy.

This is the user-selected paper-research policy candidate, not a validated or deployment baseline. Original E6 and the unfiltered reference remain mandatory controls.

No deployment baseline exists.

## Neutral NQ reference risk recalibration

Observed $100,000 account under normal costs:

- 0.50% risk: $122,595 final equity; 7.94% maximum drawdown.
- 1.00% risk: $147,582 final equity; 15.34% maximum drawdown.
- 1.50% risk: $174,491 final equity; 22.24% maximum drawdown.

At normal costs, the resampled probability of reaching a 20% drawdown is approximately:

- 0.50% risk: 1.0–1.5%;
- 1.00% risk: 32.4–33.7%;
- 1.50% risk: 77.3–77.8%.

At severe four-tick-per-side costs, 1.00% risk reaches 20% drawdown in approximately 60.7–61.7% of resamples. No live sizing authorization follows.

## NQ historical research freeze

Further 2023–2025 NQ threshold, weekday, session, event, entry, exit, sequencing, interaction and sizing searches are frozen. The original 904-selection chronology remains permanently unreconstructible from surviving artifacts.

## Dukascopy Nasdaq-proxy evidence

The 2022–2025 overlap study found that Dukascopy `USATECH.IDX/USD` is a high-quality temporary NQ research proxy:

- one-minute return correlation: approximately 0.951;
- five-minute return correlation: approximately 0.959;
- daily return correlation: approximately 0.970;
- signal-direction agreement: approximately 99.6%;
- shared-trade outcome agreement: approximately 95.8%.

The sealed 2026 proxy sample produced approximately -1.80R for the unfiltered reference, +5.63R for E6 and +6.31R for E6 no-FOMC. This is Nasdaq-100 bid-CFD proxy evidence, not CME NQ futures validation.

## USA500 baseline-discovery result

The USA500 programme started from the unfiltered frozen core and did not inherit NQ filters.

### Frozen Monday × Asia factorial

- Tue–Fri, all sessions: 601 trades, -19.56R, -0.033R expectancy.
- Mon–Fri, all sessions: 747 trades, -24.83R, -0.033R expectancy.
- Tue–Fri, London + New York: 470 trades, -2.25R, -0.005R expectancy.
- Mon–Fri, London + New York: 573 trades, -3.80R, -0.007R expectancy.

Adding Monday worsened the portfolio. Removing Asia materially improved it but did not create a positive, cost-robust baseline.

### Session decomposition

London-only was the sole positive diagnostic:

- 253 trades;
- +16.98R net;
- +0.067R expectancy;
- +0.007R expectancy at two ticks per side;
- -0.113R expectancy at four ticks per side;
- 15.47R maximum drawdown.

Annual London-only results were -2.72R in 2022, +13.16R in 2023, +12.80R in 2024 and -6.26R in 2025. It therefore failed the preregistered year-stability and concentration gates and was not promoted.

New York-only and Asia-only were materially negative. No fixed context or event policy repaired the all-session core into a viable strategy. The NQ E6 transfer rule was positive over 2023–2025 but lost 21.91R in 2022, showing regime dependence.

Decision: `NO_VIABLE_USA500_CORE_BASELINE`.

## Next evidence gate

The next legitimate multi-index step is one of:

1. acquire actual contract-audited ES futures data and test whether USA500 2022/2025 weakness is proxy-specific;
2. open a separately preregistered ES-specific core-development programme using nested chronological validation;
3. investigate the London-versus-New-York/Asia mechanism difference before any parameter changes.

## Existing unresolved gates

- authoritative vendor timestamp metadata: documentation limitation, while the working interpretation is resolved by census;
- NQ continuous-contract methodology: `UNRESOLVED`;
- qualified fresh CME NQ OOS comparison: `NOT_RUN`;
- actual contract-audited ES replication: `NOT_RUN`;
- Python/Pine parity: `NOT_RUN`.

## Scope restrictions

No further NQ in-sample optimization, neighboring USA500 threshold or interaction search, pooled NQ/proxy portfolio, dynamic sizing, Pine port, live sizing recommendation, leverage increase or deployment is authorized.
