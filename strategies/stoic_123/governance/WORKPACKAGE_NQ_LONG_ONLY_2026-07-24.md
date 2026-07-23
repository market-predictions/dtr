# Work Package — NQ Long-Only Mechanism and Futures Replication

Work package: `STOIC123-WP-20260724-02`
Date opened: 2026-07-24
Branch: `agent/stoic-nq-long-only-validation`
Status: `PREREGISTERED_EXECUTION_PENDING`

## Strategic question

Does the exploratory long-only result represent a genuine Stoic 1-2-3 continuation effect, or merely generic Nasdaq long drift, altered exit behavior, or CFD-proxy-specific evidence?

## Root-cause correction before execution

The informal long-only counterfactual disabled short entries by setting `allow_short: false`. Because the management detector inherited that setting, it also removed opposite short 1-2-3 signals that normally exit long positions. That mixed an entry-direction restriction with an unplanned exit-system change.

This work package supersedes that interpretation. Entry direction may be restricted, but management remains two-directional. Long trades can still exit on a complete opposite short management sequence.

## Frozen source

- Instrument: NQ futures research archive.
- Expected archive SHA-256: `8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc`.
- Period: 2022-12-26 18:00 ET through 2025-12-10 23:58 ET.
- Raw data remains outside Git and outside result artifacts.
- Continuous-contract roll and exact timestamp semantics remain unresolved limitations.

## Frozen candidates

1. `S123_M0_NO_MAP_CONTROL` — simplicity benchmark.
2. `S123_M1_EMA_MAP` — primary candidate.
3. `S123_C1_STRICT_CLOSE` — secondary candidate.
4. `S123_M3_EMA_PLUS_BREAKOUT` — diagnostic candidate.

No other phase-one arm may be selected from the historical result.

## Mechanism controls

Each candidate is evaluated using:

- both-direction full 1-2-3 comparator;
- long-only full 1-2-3;
- short-only full 1-2-3 diagnostic;
- long EMA break only, with the Step-1 bar low as the causal protective boundary;
- long EMA break plus retest, with the lowest observed low from Step 1 through retest as the protective boundary;
- 50 deterministic matched-time long-entry controls preserving year, weekday, RTH/overnight status, 30-minute time bucket, map eligibility, and signal-to-protective-boundary distance.

## Robustness tests

- one tick per side baseline;
- two ticks per side cost stress with unchanged commission;
- one-minute entry delay;
- one-five-minute-bar entry delay;
- calendar-year and expanding-year test attribution;
- RTH versus overnight attribution;
- year/month concentration;
- exposure-normalized return;
- independent trade-ledger reconstruction.

## Promotion gates

Every gate is required:

1. Positive long-only expectancy.
2. At least three of four observed years positive.
3. Every full year from 2023 through 2025 positive.
4. No positive year contributes more than 60% of positive net R.
5. Positive under two ticks of slippage per side.
6. Positive with a one-minute delayed entry.
7. At least 25% lower maximum drawdown than the both-direction comparator.
8. Full sequence exceeds EMA-break-only by at least 0.05R expectancy or 20% return-to-drawdown.
9. Positive 95% date-block bootstrap lower bound.

## Restrictions

- No parameter, timeframe, threshold, session, stop, target, exit, or matched-control redesign after performance inspection.
- No pooled NQ/proxy result.
- No ES-proxy or GBPUSD result may tune NQ.
- No Pine port, sizing, deployment, alert, or profitability authorization.
