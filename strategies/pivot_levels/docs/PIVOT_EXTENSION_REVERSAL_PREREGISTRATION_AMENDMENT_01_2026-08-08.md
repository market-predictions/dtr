# Directional Extension × Strong H1 Rejection — Preregistration Amendment 01

**Study:** `DFXC-20260808-010-extension-conditioned-reversal`  
**Status:** frozen before pooled outcome calculation  
**Reason:** remove two algebraic ambiguities in the original preregistration without changing any signal, threshold, horizon, cohort or promotion criterion.

## A. Pair-year clustered bootstrap

The bootstrap resampling unit is the complete `pair × calendar year` cluster.

For each of 5,000 deterministic draws:

1. sample the observed pair-year clusters with replacement, using the same number of cluster draws as observed clusters;
2. preserve all observations within each selected cluster and preserve multiplicity when a cluster is drawn more than once;
3. compute event-weighted means/contrasts from the resampled cluster sufficient statistics.

The continuous `REV4_ATR ~ EXT` slope is the ordinary unweighted event-level OLS slope with intercept. It is calculated from cluster sufficient statistics `n, sum(x), sum(y), sum(x^2), sum(x*y)` so the bootstrap is algebraically equivalent to concatenating the sampled clusters.

No pair weighting or winsorization is applied.

## B. Extension-matched pivot estimator

Within each eligible `pair × calendar year × rejection direction × 0.25-Daily-ATR extension stratum`:

- compute the mean `REV4_ATR` for the pivot-core cohort;
- compute the mean `REV4_ATR` for `NON_CORE`;
- form `pivot mean - NON_CORE mean`;
- assign the stratum weight `min(n_pivot, n_NON_CORE)`, representing the maximum one-for-one matched observation capacity of that stratum.

The overall matched effect is the weighted mean of those stratum differences. The pair-year bootstrap resamples the pair-year clusters, carrying all of their eligible direction/extension strata and weights with cluster multiplicity.

This same estimator is used unchanged for S2/R2-core and S1/R1-core secondary matched contrasts.

## C. Missingness

Each endpoint uses only observations with a valid executable value for that endpoint. The 4H endpoint remains primary. No imputation is performed.

No 2026 data has been opened or used in creating this amendment.
