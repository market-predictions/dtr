# Independent Review — DTR-NQ-WP-20260722-09

## Result

`PASS`

## Checks

- Dataset checksum matched the registered NQ archive.
- All 12 portfolio metric sets were independently reconstructed from trade rows.
- All arm weekday and session restrictions were exact.
- No portfolio contained overlapping positions.
- Frozen A0, E5 and E6 references reproduced exactly.
- Independent date-block bootstrap used a separate implementation and seed.

## Findings

- Adding Monday to the unfiltered strategy is statistically unresolved and lowers expectancy.
- Adding Monday under E5 is economically adverse.
- Adding Monday under E6 increases net R but lowers expectancy and return/DD; its positive effect is concentrated in Asia Monday.
- Removing Asia reduces net R under all three layers.
- The proposed combined arm is inferior under all three layers.

## Review conclusion

`DO_NOT_REMOVE_ASIA; DO_NOT_PROMOTE_MONDAY`

Retain Tuesday–Friday and all three sessions. E6+Monday may remain a shadow forward-data coverage diagnostic only.
