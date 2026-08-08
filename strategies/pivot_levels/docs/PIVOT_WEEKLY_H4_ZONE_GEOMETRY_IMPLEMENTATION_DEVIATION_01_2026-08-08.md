# Weekly H4 Zone Geometry — Implementation Deviation 01

Date: 2026-08-08
Study: `DFXC-20260808-004-pivot-weekly-h4-zone-geometry`
Status: `FIRST_WEEKLY_RUN_INVALIDATED_BEFORE_ACCEPTANCE`

## Trigger

The preregistered acceptance criterion requires `SP20_REF` to numerically reproduce the parent Weekly→H4 20%-spacing reference before any challenger geometry is trusted.

The first implementation run produced a tiny but non-zero discrepancy:

- structural `SP20_REF`: approximately +0.66797 pp versus parent +0.66856 pp;
- wick interaction `SP20_REF`: approximately +0.77351 pp versus parent +0.77367 pp.

Although economically immaterial, this fails the explicit deterministic-reproduction gate.

## Root cause

The new loader aggregated annual M1 fragments into H4 bars and only afterward applied the NY17 FX trading-date study boundary. The parent `DFXC-20260808-001/002` implementation first filtered M1 rows to the eligible FX trading-date window and then constructed H4 bars.

Only boundary bars are affected, but the ordering difference explains the small non-zero reference mismatch.

## Disposition

All Weekly/H4 zone-geometry outcomes from the first run are **invalidated and may not support a scientific conclusion**.

The Daily/H1 protected-holdout calculation is a separate study and is not changed by this weekly boundary issue.

## Corrective action

Without changing any preregistered hypothesis, width, ATR coefficient, wick threshold, pair universe, terminal definition, inference method or gate:

1. apply the parent ordering exactly: filter M1 by eligible NY17 FX trading date before H4 aggregation;
2. rebuild all ten Weekly/H4 base ledgers;
3. require `SP20_REF` deterministic reproduction against the parent combined structural and wick point estimates within floating-point tolerance;
4. only then rerun all seven frozen geometries and inference.

No additional geometry is added and no observed first-run challenger result is used to modify the preregistration.
