# Asian Sweep Auction-State Diagnostic — Corrected Development Result

Date: 2026-07-23  
Work package: `AS-WP-20260723-08`  
Official workflow: `30029236403`  
Artifact digest: `sha256:20483971b77be96f3c73492ec9b098423854e6f1a0ad34772f5fac762cc300e6`

## Decision

`NO_MECHANISM_PASSES_DEVELOPMENT_PROMOTION_STANDARD`

The corrected development-only diagnostic classified 1,436 London and New York boundary events across the registered NQ and ES Dukascopy BID proxies. No candidate mechanism/session passed the frozen sample, cross-instrument and subperiod-stability requirements. The protected 2024-07-01 onward validation partition remained closed.

## Corrected causal contract

Independent review found and corrected two implementation defects before accepting the result:

- opposite-side breaches are evaluated through the actual causal confirmation bar;
- one-minute fixed horizons and session paths use half-open endpoints, preventing an extra minute from entering each outcome window.

Repository CI, isolated Asia Sweep tests, unchanged proxy event audit and the corrected private diagnostic all passed on exact head `ab785b8a1eb44ae9c0e21ced31bedfb57e3a3b29`.

## External-liquidity rejection

### London

| Instrument | Observations | Mean 30m return / range | Mean 60m return / range | 30m bootstrap 95% CI | 60m bootstrap 95% CI |
|---|---:|---:|---:|---:|---:|
| NQ proxy | 32 | +0.036 | +0.119 | [-0.040, +0.107] | [-0.023, +0.265] |
| ES proxy | 23 | +0.058 | +0.023 | [-0.042, +0.164] | [-0.146, +0.208] |

The direction was positive in both proxies, but the frozen minimum was 40 observations per proxy and both uncertainty intervals included zero. This is a research hint only.

### New York

Both proxies were negative at 30 and 60 minutes. The New York rejection mechanism is rejected.

## Compressed-range acceptance

- London failed cross-instrument consistency because NQ was negative at 60 minutes.
- New York was positive over the full development sample but reversed materially in 2024 H1; the apparent effect was concentrated in 2023.
- Requiring a held retest collapsed the sample and generally worsened outcomes.

## Research consequence

The broad Auction-State redesign is closed without a challenger. The only permitted continuation is a separately preregistered London liquidity-cluster hypothesis that tests whether an Asian boundary aligned closely with PDH/PDL behaves differently from the broader external-level sample. That follow-up must freeze its cluster distance and Asian-range regime before execution results are viewed.

## Limitations

- Index-CFD BID proxies are not CME futures reconstruction.
- The diagnostic measured causal forward paths, not executable strategy P&L.
- Bootstrap intervals are descriptive and unadjusted.
- The development study was informed by a feasibility preview and is not out-of-sample evidence.
