# Independent review — DTR-FX-WP-20260724-23

Date: 2026-07-24

## Conclusion

`PASS — REPORTED REJECTION RECONSTRUCTED`

The saved 105-trade ledger independently reproduces the reported summary and the preregistered decision `REJECT_B1_ON_OLDER_HISTORY` with zero metric mismatches.

## Integrity checks

- Frozen runner SHA-256 matches: pass.
- Source qualification is recorded as passed before return inspection: pass.
- Summary metrics reconstructed from raw trades: pass.
- Annual decomposition reconstructed: pass.
- 1.5× execution-cost stress reconstructed: pass.
- Positive-year gate reconstructed: fail as reported, 3 of 7.
- Date-block confidence interval reconstructed: crosses zero as reported.
- Decision parity: pass.
- Deployment block retained: pass.

## Key reconstructed metrics

- Trades: 105
- Net R: +10.336779
- Net expectancy: +0.098446R
- Profit factor: 1.187675
- Maximum drawdown: 14.327014R
- 1.5×-cost expectancy: +0.053032R
- 2015–2019 expectancy: +0.011409R
- 2020–2021 expectancy: +0.326542R
- Positive years: 3 of 7
- Date-block 95% interval: [-0.158471R, +0.359370R]

## Evidence hashes

- Runner: `8bed9d9e0d7e198ff5a3d8f02cc8f4303ace7d1820885fcde13bcb5774a81e59`
- Trade ledger: `ea2fff239a4707315b4a4cfdfd7398808dbf2177f99ab52aa5f4c1ec91d269e3`
- Independent-review artifact: `cdde9c57b5ccd8743967e3cc4c55fe343d48d37d07bf89bb6465b079a7dd2d4a`

## Reviewer judgment

The aggregate positive return is insufficient to justify continuation. Four calendar years were negative, the 2015–2019 partition was effectively flat, maximum drawdown exceeded total net return, and uncertainty remains large. The scientifically correct action is to reject the frozen B1 contract on GBPUSD and prohibit post-hoc rescue tuning.
