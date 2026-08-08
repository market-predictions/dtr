# Weekly H4 Zone Geometry — Implementation Deviation 02

Date: 2026-08-08
Study: `DFXC-20260808-004-pivot-weekly-h4-zone-geometry`
Status: `REFERENCE_REPRODUCTION_NOT_YET_ACCEPTED`

## Finding

After correcting the study-boundary aggregation ordering described in Deviation 01, `SP20_REF` still differed minutely from the parent result.

An exact core/outer ledger comparison localized the entire remaining discrepancy to **four non-terminal observations** across approximately 178,000 reference core/control observations:

- EURGBP 2015 S2 low, 30–40% wick;
- EURGBP 2017 PP low, 10–20% wick;
- USDCHF 2019 R2 low, <10% wick;
- USDJPY 2018 PP high, 10–20% wick.

No terminal count differed.

## Root cause

The parent implementation defines normalized distance first:

`d = distance / spacing`

and classifies core with:

`d < 0.20`.

The new generic geometry evaluator used the algebraically equivalent expression:

`distance < 0.20 * spacing`.

For four observations numerically on the 20% boundary, floating-point evaluation differed by one side of the strict inequality.

## Corrective action

- Spacing-only variants (`SP10`, `SP15`, `SP20_REF`, `SP25`) will classify core/control using the preregistered normalized distance `d = distance/spacing`, matching the parent semantics exactly.
- Hybrid ATR variants continue to require absolute-width comparison because their width is observation-specific and not reducible to a fixed normalized threshold.
- No threshold, coefficient, pair, level, wick definition, terminal definition, bootstrap method or gate changes.

## Acceptance rule

No Weekly/H4 challenger result will be accepted unless `SP20_REF` reproduces the parent combined structural and wick point estimates exactly within normal floating-point calculation tolerance after this correction.

All Weekly/H4 challenger outcomes observed before this final reproduction pass remain invalid for scientific decision-making.
