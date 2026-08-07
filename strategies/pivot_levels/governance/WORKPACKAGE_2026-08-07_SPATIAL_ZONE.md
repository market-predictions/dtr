# Work Package — Pivot Spatial-Zone Follow-up

- **ID:** `PIV-WP-20260807-02`
- **Status:** Active
- **Branch:** `agent/pivot-spatial-zone-followup`
- **Parent:** `PIV-WP-20260807-01` / PR #72
- **Implementation role:** `implementation_operations`
- **Assurance role:** `governance_release_assurance`

## Objective

Determine whether the prior exact-coordinate null result was caused by contaminated nearby controls because the economically relevant object is a broad pivot zone.

## Reconstructed variables

- Broad-zone concern and request to rerun: `EXPLICIT`.
- 20% local-spacing half-width as primary broad zone: `DEFAULTED`, chosen before outcomes because it sits materially wider than the parent zone while remaining separated from midpoint controls.
- 5/10/15/20/25% response curve: `DERIVED` from the approved follow-up design.
- Equal-width midpoint controls: `DERIVED` as the cleanest far-control implementation inside the adjacent-pivot interval.
- Continuous occupancy-adjusted distance gradient: `DERIVED` to test spatial influence without a hard zone boundary.
- Existing 2015–2019 / 2020–2021 split and 2022–2025 holdout: `DERIVED` from project governance.

## Acceptance criteria

1. Preregistration exists before any spatial-zone outcome is calculated.
2. All ten registered pairs are reused from the local/cache-qualified source; no market-data reacquisition.
3. Same pivot formulas, NY17 boundaries, trend state, M15 ordering, barriers and dwell windows as parent programme.
4. Real and midpoint-control zones are non-overlapping at primary 20% width.
5. S1–S5 are produced separately for development, validation and combined samples on all eligible timeframes.
6. Primary inference uses 5,000 pair-year-week clustered bootstrap draws and Holm correction across 25 hypotheses.
7. Secondary widths are reported as a response curve and cannot rescue a failed 20% primary.
8. 2022–2025 remains unopened.
9. Independent assurance recomputes source identities, spatial geometry, primary effects, sample boundaries and the binding decision without modifying the candidate.
10. Report, compact evidence, changelog/status, work-package closure and handover are recorded.

## Non-scope

- pivot formula variants;
- retuning trend or barrier definitions;
- post-outcome width selection;
- pair/session/year/level rescue;
- execution P&L;
- Pine, alerts, sizing, paper trading or deployment.

## Definition of done

A broad-zone conclusion is frozen and independently assured, with the prior exact-coordinate interpretation either materially revised or retained on evidence.
