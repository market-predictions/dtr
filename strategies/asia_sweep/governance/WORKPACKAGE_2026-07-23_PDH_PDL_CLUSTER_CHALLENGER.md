# Work Package AS-WP-20260723-09 — Final PDH/PDL Liquidity-Cluster Challenger

## Objective

Test one final, fully frozen London reversal ruleset: a complete sweep and confirmed rejection of an Asian-boundary liquidity cluster aligned with PDH or PDL, only when the completed Asian range is neither abnormally small nor abnormally wide.

This package is not a filter search over AS-A through AS-D. It is a separate auction hypothesis motivated by the small positive London external-rejection association in `AS-WP-20260723-08`.

## Data boundary

- Registered private Dukascopy NQ and ES index-CFD BID proxies.
- Development period only: 2023-01-01 through 2024-06-30.
- Data on or after 2024-07-01 remain closed.
- Raw private sources may not be committed or uploaded.

## Frozen session and reference

- Session timezone: `America/New_York`.
- Asian reference range: 18:00 previous local date through 02:00 trade date.
- London execution window: 02:00 through 06:00, half-open.
- Monday through Friday.
- First complete cluster sweep in the London window owns the event.

## Frozen Asian-range regime

Compare the current Asian range width with the preceding 60 valid Asian ranges for the same proxy. At least 20 prior ranges are required.

Eligible percentile band: **20th through 80th percentile, inclusive**.

- below 20%: too small;
- above 80%: too wide;
- no alternative percentile bands may be tested in this package.

## Frozen liquidity cluster

### Long

- PDL is within 10% of the Asian-range width of the Asian low;
- price trades strictly below the lower of PDL and the Asian low;
- price closes back above the upper of those two levels within the sweep bar plus the next two five-minute bars;
- the next two completed five-minute closes remain above the upper cluster boundary.

### Short

Symmetric rules apply to PDH and the Asian high.

A same-bar sweep of both eligible clusters is invalid. A breach of the opposite Asian boundary before rejection confirmation is invalid.

## Frozen entry

- Define the rejection impulse from the reclaim bar through the second hold-confirmation bar.
- Long: first later five-minute close above the rejection impulse high.
- Short: first later five-minute close below the rejection impulse low.
- Enter at the first one-minute open after that five-minute close.
- Entry must occur before 06:00.
- No re-entry.

## Frozen risk and exit

- Stop: two 0.25 execution ticks beyond the complete sweep extreme through confirmation.
- Target: completed Asian-range midpoint.
- If the midpoint is not ahead of the entry before and after normalization, block the trade.
- Full-position exit only.
- Mandatory time exit at 06:00.
- Directionally pessimistic 0.001-source to 0.25-execution normalization.
- One tick adverse entry slippage.
- One tick adverse stop slippage.
- One tick adverse market-exit slippage.
- $2.25 commission per side.
- Stop-first same-minute collision policy.
- NQ proxy point value: $20 per point; ES proxy: $50 per point.

## Frozen promotion gate

Promotion requires all of:

1. at least 20 exited trades in NQ;
2. at least 20 exited trades in ES;
3. positive expectancy in each proxy;
4. pooled expectancy at least +0.05R;
5. pooled profit factor at least 1.10;
6. positive pooled expectancy in 2023;
7. positive pooled expectancy in 2024 H1;
8. zero validation-partition access;
9. no unresolved execution defect affecting the conclusion.

Failure closes the Asian Sweep research line. No threshold expansion, weekday/direction selection, ES-only or NQ-only rescue, Pine implementation or validation access is permitted after failure.

## Required outputs

- daily eligibility/audit ledger;
- qualified signal ledger;
- one-minute execution ledger;
- funnel counts;
- instrument, pooled and subperiod metrics;
- exact cost and normalization disclosure;
- independent review and final stop/promote decision.
