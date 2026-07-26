# Asian Sweep Extended-Reversal Model — Decision

Date: 2026-07-26  
Decision: `FAIL_EXTENDED_REVERSAL_MODEL_STOP_BEFORE_POSITION_STRUCTURE_PNL`  
Development: EURUSD and GBPUSD, 2015–2019  
Protected: 2020–2025 unopened

## Authoritative evidence

- GitHub Actions run: `30209186651`;
- evaluated head: `fa791e82eb7cf24804aacec44ac3203519b48b3e`;
- decision artifact: `asia-sweep-extended-reversal-model-decision`;
- artifact digest: `sha256:7e8a0102cf55f709958f9adf2d3c5763de0b1bd2ca0c80a8c1847538077d78ec`;
- 40 of 40 frozen target/landmark/family candidates completed.

All focused tests, repository CI, pair reconstruction, candidate fitting, candidate-count enforcement and frozen aggregation completed. The workflow is red only because the deliberate scientific pass-enforcement step rejected the negative decision.

## Integrity repairs before the final run

Two operational defects were corrected without changing any target, feature, model, gate, hierarchy or protected boundary:

1. the candidate pooling heredoc originally searched a literal `${RUNNER_TEMP}` path rather than the runner environment path;
2. the inherited fingerprint evidence serialized only sweep-side levels, so the preregistered opposing-liquidity target had no population.

The final workflow reconstructed the already-defined causal external-liquidity universe directly from the same qualified 2015–2019 BID/ASK source and retained the required reversal-side roles:

- lower sweep / reversal long: nearest confirmed HIGH beyond entry;
- upper sweep / reversal short: nearest confirmed LOW beyond entry.

Hard guards now fail if either role or any frozen target population disappears.

## Final target evidence

| Pair | Target rows | Event-landmarks | Opposing-liquidity levels | Opposing-liquidity events |
|---|---:|---:|---:|---:|
| EURUSD | 23,059 | 4,613 | 11,135 | 1,241 |
| GBPUSD | 23,506 | 4,705 | 12,764 | 1,291 |
| **Pooled** | **46,565** | **9,318** | **23,899** | **2,532** |

All five frozen targets, all four T0–T3 landmarks, both model families and all five development years were present.

## Candidate decision

No candidate passed every frozen gate. Therefore no target, landmark or model family was selected.

The descriptively closest candidate for each target is shown only to explain the failure; none has promotion authority.

| Target | Candidate | Events | Positives | PR-AUC relative lift | Top-decile lift | Stressed median R:R | Stressed median EV proxy | Failed gates |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 3R by 12:00 | T2 HGB | 2,254 | 448 | +11.9% | 1.11x | 2.88R | -0.043R | EV, PR lift, top lift, year breadth |
| 4R by 14:00 | T0 HGB | 2,506 | 405 | +12.5% | 1.15x | 3.86R | -0.077R | EV, PR lift, top lift |
| 2R by 11:00 | T2 HGB | 2,254 | 598 | +9.8% | 1.20x | 1.93R | -0.078R | bottom decile, EV, PR lift, top lift |
| Opposing liquidity by 14:00 | T0 HGB | 2,503 | 385 | +14.4% | 1.16x | 3.61R | -0.042R | EV, PR lift, top lift |
| Opposite Asian boundary by 11:00 | T3 HGB | 2,162 | 322 | +70.2% | 2.05x | 1.55R | -0.181R | EV, R:R breadth |

## Strongest discriminator

`EXT_OPPOSITE_BOUNDARY_1100 / T3 / HGB` was the only candidate to clear the frozen PR-AUC and top-decile lift gates convincingly:

- base target rate: 14.89%;
- top-decile target rate: 30.59%;
- PR-AUC: 0.2535, or +70.19% relative lift;
- top-decile lift: 2.054x;
- bottom-decile ratio: 0.368x;
- calibrated Brier: 0.12077 versus 0.12675 constant baseline;
- positive top-decile lift in EURUSD, GBPUSD and every year from 2015 through 2019.

It still failed economically:

- stressed median top-decile R:R: 1.548R;
- only 71.69% of top-decile cases retained at least 1.25R, below the frozen 75% gate;
- stressed median expected-value proxy: -0.181R.

The model can identify cases more likely to reach the opposite boundary, but confirmation at T3 occurs after too much favorable path has already been consumed. Higher success probability does not compensate for the remaining payoff geometry.

## Interpretation

The final evidence resolves the central decision problem:

- early landmarks preserve attractive reward/risk but do not discriminate extended winners strongly enough;
- later landmarks improve discrimination, especially for the opposite boundary, but reduce remaining payoff;
- fixed 2R/3R/4R targets and opposing liquidity never combine sufficient PR-AUC lift, top-decile lift and positive stressed EV;
- no target-specific model creates a robust economic population on which midpoint reduction or a full runner can be tested legitimately.

This is the same information-payoff frontier observed in the earlier one-shot entry study, now tested against materially different extended targets rather than midpoint completion. The result is therefore not a failure of one arbitrary target. It is a failure to find a causal pre-T5/T3 population that simultaneously offers prediction and executable payoff under the frozen adverse stop.

## Decision and authorization boundary

The preregistered result is binding:

`FAIL_EXTENDED_REVERSAL_MODEL_STOP_BEFORE_POSITION_STRUCTURE_PNL`

Consequences:

- do not open `TP1_50_RUNNER_50`;
- do not open `TP1_25_RUNNER_75`;
- do not open `NO_TP1_FULL_RUNNER`;
- do not access 2020–2025;
- do not rescue by pair, year, weekday, direction, target, threshold, stop or landmark;
- do not proceed to Pine, alerts, paper trading or deployment.

## Programme disposition

The current Asian Sweep / Stacey Burke-inspired executable-reversal line is exhausted:

- the validated T5 fingerprint predicts midpoint completion but did not produce positive post-T5 execution;
- staged exits and broad runner policies failed;
- one-shot early entry failed the information-payoff gate;
- continuation geometry failed as a standalone trade;
- six staged reversal policies failed;
- the final target-specific extended-reversal programme failed all 40 candidates.

No materially different authorized path remains inside the present programme. Further work on the same entries, adverse stop, feature family and Asian-range objectives would be post-hoc optimization. Reopening research requires a genuinely new market hypothesis and a new preregistration, not a parameter or management variation.
