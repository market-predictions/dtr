# Asian Sweep Staged Reversal Entry — Decision

Date: 2026-07-26
Decision: `FAIL_STAGED_REVERSAL_DISCOVERY_STOP_BEFORE_VALIDATION`
Development: EURUSD and GBPUSD, 2015–2019
Protected: 2020–2025 unopened

## Authoritative evidence

- GitHub Actions run: `30204918985`;
- evaluated head: `8f9f1df01064b2f39efa48e0309069413e93f133`;
- decision artifact: `asia-sweep-staged-reversal-decision`;
- digest: `sha256:90dbd73e9da37bb854843dacfdca2ce2b823d0f43331d438a0c470532adea791`.

All tests, both pair simulations, pooled nested selection and artifact uploads completed. Only the deliberate pass-enforcement step failed.

## Policy results

| Policy | Attempts | Net R | Expectancy | +0.10-pip expectancy | +0.25-pip expectancy | Max DD | Positive pairs | Positive years |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Conservative, no T0 | 310 | -29.20R | -0.0942R | -0.1089R | -0.1308R | 34.95R | 0 | 1 |
| Conservative, T0 0.25R | 2,208 | -81.03R | -0.0367R | -0.0461R | -0.0601R | 83.65R | 0 | 0 |
| Balanced, no T0 | 310 | -40.44R | -0.1305R | -0.1503R | -0.1801R | 46.80R | 0 | 1 |
| Balanced, T0 0.25R | 2,208 | -99.97R | -0.0453R | -0.0556R | -0.0711R | 106.44R | 0 | 0 |
| Aggressive, no T0 | 310 | -41.49R | -0.1338R | -0.1558R | -0.1887R | 47.57R | 0 | 1 |
| Aggressive, T0 0.50R | 2,208 | -140.13R | -0.0635R | -0.0803R | -0.1056R | 141.91R | 0 | 0 |

## Nested decision

No policy passed the four-year inner gates in any held-out fold. Therefore:

- no held-out policy was selected for 2015, 2016, 2017, 2018 or 2019;
- the modal-policy gate failed;
- the out-of-fold policy ledger correctly contains zero trades;
- 2020–2025 validation remains closed.

## Interpretation

The staged architecture improved the per-attempt economics relative to waiting until T2 for a full entry, but not enough to create positive expectancy:

- small T0 probes obtained a better price and reduced average loss per attempt;
- continuation exits and later abstention management limited some individual losses;
- the broad T0 opportunity set produced very high turnover and large cumulative drawdown;
- T2-only entries remained too late and materially negative;
- no risk-allocation tier was positive in either pair.

The passing triage classifier is therefore useful for decision support, but these six causal add/reduce/cancel mappings do not convert it into a viable midpoint-target reversal strategy.

## Integrity audit

The retained policy ledger was independently reaggregated. Trade counts, net R, base and stressed expectancy, drawdowns, pair/year breadth and the zero-policy nested result reproduced exactly.

## Closed path

The following formulation is rejected before validation:

- first-event T0 provisional or first T2 reversal entry;
- elastic-net T2/T3 state transitions;
- the six frozen risk-allocation policies;
- original adverse stop;
- full Asian-midpoint target;
- 10:00 time exit.

No policy blend, pair selection, threshold change, daily ranking or risk-allocation rescue is permitted on this branch.

## Next valid use

The remaining authorized path is the independently preregistered extended-reversal model. A target-specific 2R/3R/4R or structural model may identify a narrower population where early provisional exposure and 50%/25%/0% midpoint structures have appropriate payoff. It must pass before those structures are opened.
