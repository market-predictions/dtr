# Directional Extension × Strong H1 Rejection — Executable Reversal Study

**Study:** `DFXC-20260808-010-extension-conditioned-reversal`  
**Dataset:** Dukascopy FX Cash — ten pairs, M1 BID/ASK  
**Internal sample:** 2015–2025  
**2026 YTD:** **not opened**

## Executive conclusion

The intuitive mechanism that a strong H1 rejection should reverse more reliably after price has already travelled unusually far is **not supported as a stable executable 4H trading edge**.

There is one real but insufficient signal in the pooled data: the continuous relationship between pre-rejection extension and 4H executable countertrend return is positive at **+0.0239 H1 ATR of return per additional Daily ATR of extension**, with 95% pair-year clustered-bootstrap CI **[+0.0011,+0.0466]**.

However, the preregistered extreme-extension trading test fails:

- `E3` (`>=1.75` lagged Daily ATR travelled) mean 4H countertrend return: **-0.0861 H1 ATR**, CI **[-0.2012,+0.0279]**;
- `E3 - E0` improvement: **+0.0184 H1 ATR**, CI **[-0.0957,+0.1314]**;
- only **6/10 pairs** have positive `E3-E0`;
- the positive pattern is not stable through time and is driven mainly by 2022–2025;
- 4H same-pair/same-direction cooldown removes statistical support for the continuous slope and leaves E3 expectancy negative.

Decision:

`REJECT_EXTENSION_CONDITIONED_REVERSAL_NO_STABLE_EXECUTABLE_EDGE`

Scientific disposition: `REJECT_MECHANISM`.

The study therefore does not authorize 2026 exposure, threshold optimization, stop/target optimization, or a pivot-specific rescue.

## Frozen market question

> Does a strong H1 rejection become more reversal-prone as the market has already travelled farther in the incoming direction, independent of whether the rejection occurs at a named Daily pivot?

This deliberately tests **distance travelled itself**, rather than assuming that S2/R2 is a sufficient proxy for extension.

## Frozen extension definition

For every generic directional strong H1 rejection:

- strong wick fraction `>=30%`;
- dual-strong ambiguous bars excluded;
- upper rejection must occur above the NY17 FX-day open and is evaluated as a countertrend short;
- lower rejection must occur below the NY17 FX-day open and is evaluated as a countertrend long;
- directional travel is measured from the NY17 day open to the rejection extreme;
- normalization is lagged 20-day NY17 Daily ATR, using only completed prior days.

Bins:

| Bin | Extension |
|---|---|
| E0 | 0.00–0.75 Daily ATR |
| E1 | 0.75–1.25 |
| E2 | 1.25–1.75 |
| E3 | >=1.75 |

The executable response begins only after the H1 signal closes and crosses the real quoted spread.

## Population

The generic structural universe contains **249,882** eligible strong-rejection events.

Valid executable 4H outcomes: **242,866**.

| Extension bin | Valid 4H observations | Mean executable reversal return |
|---|---:|---:|
| E0 | 220,892 | **-0.1045 H1 ATR** |
| E1 | 17,244 | **-0.1147** |
| E2 | 3,451 | **-0.0671** |
| E3 | 1,279 | **-0.0861** |

Extreme extension is genuinely uncommon: about 0.5% of valid signals are in E3.

## Primary continuous dose result

Pooled 2015–2025 OLS slope, with pair-year clustered bootstrap:

- estimate: **+0.02389 H1 ATR return / Daily ATR extension**;
- 95% CI: **[+0.00106,+0.04663]**;
- bootstrap two-sided sign-mass p ≈ **0.0428**.

This says that, pooled across the full eleven-year sample, greater extension is associated with *less bad / somewhat better* countertrend performance.

It does **not** establish a profitable reversal rule, because the actual high-extension cohort remains negative after spread and the relationship is not stable across historical partitions.

## Temporal stability — the decisive failure

| Partition | Continuous slope | E0 mean | E3 mean | E3 − E0 |
|---|---:|---:|---:|---:|
| 2015–2019 development | **-0.0112** | -0.1016 | **-0.3307** | **-0.2292** |
| 2020–2021 validation | **-0.0292** | -0.1091 | +0.0188 | +0.1279 |
| 2022–2025 exposed stability | **+0.0981** | -0.1058 | **+0.1563** | **+0.2621** |

The recent sample behaves very differently from the earlier history.

In development, extreme extension is substantially **worse**, not better, for countertrend reversal. The continuous slope is also negative in both development and internal validation. The pooled positive slope is therefore not a stable cross-era relationship.

This is exactly why the preregistered gate required development/validation consistency rather than accepting the pooled headline alone.

## Pair breadth

Only **6/10 pairs** have positive E3-minus-E0 effects.

The dispersion is large. Several pairs show materially worse extreme-extension reversal, while others show materially better reversal. The preregistered breadth gate required at least 7/10 positive pairs and therefore fails.

No pair subset may be selected as a rescue.

## Cooldown robustness

A deterministic 4H same-pair/same-reversal-direction cooldown reduces the sample to **141,000** observations.

Under cooldown:

- continuous slope: **+0.02136**, CI **[-0.00220,+0.04550]**;
- E3 mean: **-0.10179**, CI **[-0.21435,+0.01064]**;
- E3-minus-E0: **+0.00268**, CI **[-0.11101,+0.11630]**.

Thus the weak pooled dose signal is not robust to de-duplicating clustered/repeated opportunities.

## Path diagnostics

Extreme-extension rejection creates **more movement in both directions**, rather than a clean reversal asymmetry.

| Path metric | E0 | E3 |
|---|---:|---:|
| 4H reversal-direction MFE | 0.955 H1 ATR | **1.058** |
| 4H adverse/continuation MAE | 1.163 | **1.316** |
| +0.5 ATR reversal first | 39.92% | **45.89%** |
| -0.5 ATR continuation first | 59.95% | **54.03%** |

Greater extension makes reversal first-passage less unfavorable, but continuation still reaches the adverse 0.5-ATR threshold first more often than reversal even in E3.

This is closer to a **higher post-extension two-sided movement state** than to a deterministic mean-reversion state.

## Secondary horizons

Secondary executable means are descriptive only:

- 1H E3: **-0.1142 H1 ATR**;
- 2H E3: **-0.1386**;
- 4H E3: **-0.0861**;
- 8H E3: **+0.0134**.

The late 8H sign change is not selection authority. The preregistration fixed 4H as primary and explicitly prohibited switching horizons after outcome inspection.

## Does S2/R2 add information after controlling for extension?

No.

Using the preregistered 0.25-Daily-ATR extension strata and one-for-one matched-capacity weighting within pair × year × direction × extension stratum:

### S2/R2 core minus generic NON_CORE

- matched effect: **-0.01844 H1 ATR**;
- 95% CI: **[-0.05674,+0.01893]**;
- development: **-0.05409**;
- validation: **-0.02906**;
- 2022–2025 stability: **+0.03409**.

So after controlling directly for how far price had already travelled, S2/R2 does **not** increase reversal expectancy historically. The point estimate is actually negative overall, and both development and validation are negative.

This directly rejects the narrower idea:

> “S2/R2 is reached less often, so a strong rejection there should reverse more because price has travelled farther.”

The recent 2022–2025 period shows the opposite sign, but that is not sufficient to override the earlier frozen history.

### S1/R1 core minus generic NON_CORE

For completeness:

- matched effect: **+0.00347 H1 ATR**;
- CI **[-0.01991,+0.02690]**.

No stable extension-adjusted first-order-pivot reversal increment is established either.

## Implementation validation

A direct-source audit selected 20 random valid 2024 observations and independently rebuilt:

- the lagged Daily-ATR extension metric;
- the first executable post-H1 entry quote;
- the four-hour executable BID/ASK return.

Maximum absolute errors:

- extension: **0.0**;
- entry price: **0.0**;
- REV4 return: **0.0**.

The result is therefore not attributable to a mismatch between the structural extension metric and executable quote engine.

## Promotion gate

The internal gate fails on multiple independent conditions:

- continuous slope positive: PASS;
- continuous slope CI lower bound positive: PASS;
- E3-minus-E0 positive: PASS point estimate;
- E3-minus-E0 CI lower bound positive: **FAIL**;
- E3 mean positive: **FAIL**;
- E3 mean CI lower bound positive: **FAIL**;
- development + validation E3-minus-E0 both positive: **FAIL**;
- at least 7/10 positive pair effects: **FAIL (6/10)**;
- cooldown preserves the core conclusions: **FAIL**.

Overall: **FAIL**.

## Holdout state

**2026 YTD was not opened.**

Because the internal promotion gate fails, the fresh partition remains available for a future genuinely distinct frozen hypothesis.

## Strategic interpretation

The principal's intuition was worth testing directly. The result refines it rather than simply dismissing it:

1. Greater prior directional travel can make a subsequent strong rejection *less unfavorable* for reversal in pooled data.
2. That relationship is not stable across eras.
3. Extreme extension does not have positive 4H executable expectancy overall.
4. The path after extreme extension expands in both directions.
5. S2/R2 does not add reversal information after extension is controlled.
6. The favorable-looking extension/reversal relationship is concentrated in the recent 2022–2025 regime.

Therefore the durable conclusion is:

> **Extension is a potentially regime-sensitive state variable, but “far travelled + strong rejection” is not a stable standalone mean-reversion edge, and S2/R2 does not supply the missing robustness.**

Further rescue mining on 2015–2025 is prohibited. A future study would need a materially different market question rather than another extension threshold or pivot subset.
