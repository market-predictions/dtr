# NQ Monday × Asia Factorial Research — 2026-07-22

## Decision

`RETAIN_TUE_FRI_AND_ASIA`

The historical evidence does **not** justify adding Monday to the primary strategy and strongly rejects the proposed combination of adding Monday while removing Asia.

Asia is not diluting the strategy. It adds direct positive return and improves portfolio sequencing. Monday is mixed: approximately flat on the unfiltered strategy, detrimental under E5, and positive under E6 only because of Monday Asia trades.

## Provenance and regression

The uploaded NQ one-minute archive matched the registered SHA-256 exactly:

`8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc`

The frozen timing-corrected A0 comparator reproduced exactly:

- 477 trades;
- 42.577515R net;
- 0.089261R expectancy;
- 16.426493R maximum drawdown;
- 2.592003 return/DD.

The E5 and E6 comparator regressions also reproduced exactly:

- E5: 335 trades, 49.464423R, 0.147655R expectancy;
- E6: 304 trades, 48.937550R, 0.160979R expectancy.

## Primary factorial results

| Arm | Trades | Net R | Expectancy | Max DD | Return/DD | 2-tick expectancy | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A0 — Tue–Fri, all sessions | 477 | 42.58 | 0.089 | 16.43 | 2.59 | 0.072 | 8.07 | 28.21 | 6.18 |
| A1 — add Monday | 604 | 44.65 | 0.074 | 15.16 | 2.95 | 0.056 | 13.47 | 23.29 | 7.77 |
| A2 — remove Asia | 349 | 27.83 | 0.080 | 9.49 | 2.93 | 0.065 | 0.95 | 26.47 | −1.78 |
| A3 — add Monday, remove Asia | 433 | 21.62 | 0.050 | 12.26 | 1.76 | 0.035 | 3.43 | 19.83 | −3.84 |

### Monday

Adding Monday with Asia retained added only **2.07R** while adding 127 trades. Expectancy declined from 0.089R to 0.074R. The paired date-block 95% interval for incremental net R was **−24.61R to +29.78R**.

The 130 executed Monday trades produced only 2.27R in total:

- Monday Asia: 46 trades, +8.48R;
- Monday London: 45 trades, −6.50R;
- Monday New York: 39 trades, +0.30R.

Monday is therefore not a broad weekday edge. Its positive contribution is concentrated in Asia.

### Asia

Removing Asia from the current Tuesday–Friday strategy reduced net return by **14.75R**. The date-block interval was **−45.49R to +14.67R** for the remove-Asia arm versus A0, with only a 16.7% bootstrap probability of improvement.

The A0 Asia trades themselves generated 7.38R. The additional loss from removal came through portfolio sequencing: with Asia absent, more weaker London trades became eligible. In 2025, the remove-Asia arm became negative.

### Interaction

Adding Monday without Asia lost 6.21R versus A2. The proposed combined A3 arm lost **20.96R** versus A0 and was negative in 2025.

The factorial interaction was negative: Monday performed worse when Asia was absent. This directly contradicts the hypothesis that Monday should be restored while Asia is removed.

## Robustness under E5

| Arm | Trades | Net R | Expectancy | Max DD | Return/DD |
|---|---:|---:|---:|---:|---:|
| A0 | 335 | 49.46 | 0.148 | 9.47 | 5.22 |
| A1 add Monday | 408 | 40.46 | 0.099 | 14.08 | 2.87 |
| A2 remove Asia | 245 | 35.48 | 0.145 | 9.94 | 3.57 |
| A3 combined | 303 | 21.22 | 0.070 | 13.11 | 1.62 |

Both calendar changes degraded E5. The combined arm lost 28.24R versus E5 A0. E5’s rolling same-session percentile was recomputed within each arm’s declared weekday universe; the frozen A0 comparator remained exact.

## Robustness under E6

| Arm | Trades | Net R | Expectancy | Max DD | Return/DD |
|---|---:|---:|---:|---:|---:|
| A0 | 304 | 48.94 | 0.161 | 8.63 | 5.67 |
| A1 add Monday | 390 | 58.36 | 0.150 | 11.25 | 5.19 |
| A2 remove Asia | 216 | 32.17 | 0.149 | 7.08 | 4.55 |
| A3 combined | 274 | 29.44 | 0.107 | 8.81 | 3.34 |

E6 is the only layer where Monday increased net R: +9.43R. However:

- expectancy declined;
- drawdown increased;
- return/DD declined;
- the incremental 95% interval remained −12.70R to +32.27R;
- all +9.43R came from the Monday portfolio effect, which was dominated by Monday Asia.

E6 Monday trades by session:

- Asia: 28 trades, +12.16R, 0.434R expectancy;
- London: 29 trades, −4.68R;
- New York: 29 trades, +1.94R.

When Asia was removed, Monday became negative at −2.74R. The E6 interaction interval was nearly wholly negative, confirming that the apparent Monday extension depends on Asia rather than replacing it.

## Independent review

A separate reviewer:

- reconstructed every reported metric from all 12 trade files;
- verified each arm’s weekday and session contract;
- verified no overlapping open positions;
- reproduced the A0, E5 and E6 frozen references;
- reran date-block bootstraps with a different fixed seed.

All checks passed. The independent inference agreed with the primary result.

## Interpretation

### Strategic

The strategy is a liquidity-session reversal architecture. Asia is not simply a low-liquidity nuisance; it contributes useful reversals and can prevent weaker later-session entries. Removing it changes the opportunity set and portfolio path adversely.

### Tactical

- Keep Tuesday–Friday as the primary calendar.
- Keep Asia, London and New York.
- Do not implement A3.
- Do not add Monday to E5.
- E6+Monday may be retained only as a **shadow coverage extension**, not as a superior strategy, because its extra net return comes with lower expectancy and weaker drawdown efficiency.

### Operational

No Pine change is justified. The fresh-OOS Arms 0/A/B specification remains the primary forward test. A shadow E6+Monday series may be recorded separately without affecting the primary decision.

## Sample-size implication

The 250-trade guardrail does not drive this decision:

- A1 unfiltered, A1 E5 and A1 E6 all exceed 250 trades;
- the adverse or mixed findings remain;
- A2 E5 and A2 E6 fall below 250, but they are already economically inferior;
- more history would improve precision but is unlikely to reverse the current first-order conclusion that Asia should not be removed.

Longer NQ history and unchanged ES replication remain valuable for E5/E6 validation, not as a rescue search for the rejected Monday-without-Asia configuration.

## Final disposition

- Primary strategy calendar/session architecture: **unchanged**.
- Monday promotion: **rejected**.
- Asia removal: **rejected**.
- Monday + remove Asia: **rejected**.
- E6 + Monday: **shadow-only fresh-data coverage diagnostic**.
- Deployment/Pine/sizing authorization: **none**.
