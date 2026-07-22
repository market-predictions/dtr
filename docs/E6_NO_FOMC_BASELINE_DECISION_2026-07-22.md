# E6 No-FOMC Working Baseline Decision — 2026-07-22

## Decision

`PROMOTE_E6_NO_FOMC_DAY_AS_WORKING_BASELINE`

The user explicitly chose to avoid trading on FOMC statement dates despite the limited historical sample. This is therefore recorded as a user-mandated risk-policy decision rather than a statistically proven optimization.

## Exact rule

Use the same FOMC-day definition tested in Block 5:

- official Federal Reserve statement calendar date;
- Eastern Time entry timestamp;
- reject all entries whose calendar date equals that statement date;
- retain the frozen E6 signal logic, Tuesday–Friday calendar, all three sessions, exits, costs and one-global-position sequencing.

This rule does not expand into a previous-evening ETH-date blackout or a configurable announcement buffer.

## Exact re-sequenced result

| Baseline | Trades | Net R | Expectancy | Max DD | Return/DD |
|---|---:|---:|---:|---:|---:|
| Original E6 comparator | 304 | 48.94R | 0.161R | 8.63R | 5.67 |
| E6 no-FOMC working baseline | 291 | 53.48R | 0.184R | 9.15R | 5.84 |

At 1% current-equity risk, the re-sequenced historical path grew $100,000 to approximately $166,725 with an 8.87% maximum equity drawdown.

## Sequencing detail

Naively deleting the 14 FOMC-date trades would produce 290 trades. The exact portfolio rerun produced 291 trades because removing one overnight Asia position freed a later London signal. That newly enabled trade lost approximately 1.01R. The exact re-sequenced result is therefore authoritative.

## Evidence hierarchy

- Original E6 remains preserved as the frozen research comparator.
- `E6_NO_FOMC_DAY` becomes the working baseline for subsequent advanced tests and paper research.
- Future fresh-data or cross-market evaluation should retain original E6 as a control so the policy overlay can be measured separately.
- No Pine, live sizing or deployment authorization follows from this change.
