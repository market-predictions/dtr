# Independent Review — DTR-CROSSMARKET-WP-20260722-18

## Verdict

`INDEPENDENT_REVIEW_PASS`

## Checks completed

- NQ archive and USA500 cleaned-source checksums reproduced exactly.
- NQ E6 and E6-no-FOMC trade counts, net R, expectancy and maximum drawdown reproduced exactly.
- Every summary metric was reconstructed from the four written trade streams.
- No overlapping positions were found in any instrument/arm stream.
- Two-tick and four-tick expectancy adjustments were reconstructed from entry-to-stop risk geometry.
- FOMC removed and newly enabled trade attribution was reconstructed.
- Independent 10,000-run date-block bootstraps used a different seed family.
- A complete second primary execution produced byte-identical comparable artifacts.

## Review conclusion

The USA500 proxy supports only partial directional replication:

- one-tick E6 expectancy is positive at 0.047441R;
- two-tick expectancy is negative at -0.011853R;
- the date-block interval crosses zero broadly;
- aggregate profitability is concentrated in London;
- no-FOMC does not improve proxy total R after exact resequencing.

The framework is suitable for unchanged longer-history and actual-ES replication. It does not support proxy-specific tuning, session selection, pooled trading or an ES futures claim.
