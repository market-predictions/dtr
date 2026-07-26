# Context and Regime Atlas — Review Checklist

## Causality

- [ ] Daily features use only completed Amsterdam daily bars before the event date.
- [ ] Weekly features use only completed ISO weeks before the event week.
- [ ] The context anchor stops before 08:00 Amsterdam.
- [ ] T5 payoff entry is strictly after T5.
- [ ] No outcome or post-event field enters a regime state.

## Population

- [ ] T5 eligibility matches the frozen fingerprint population.
- [ ] Event ids are unique within and across pairs.
- [ ] Years are exactly 2015–2021.
- [ ] Both EURUSD and GBPUSD are present.

## Economics

- [ ] Long entries use ASK and short entries use BID.
- [ ] The original 0.20 Asian-range adverse stop is unchanged.
- [ ] Entry and stop each receive 0.10-pip adverse stress.
- [ ] Non-positive remaining reward or risk is excluded only from economic attribution.

## Inference

- [ ] Date-block bootstrap uses the frozen seed and 5,000 draws.
- [ ] Clustered sign permutation uses the frozen seed and 5,000 draws.
- [ ] FDR includes every non-warmup tested state.
- [ ] Pair, year and concentration predicates are enforced.
- [ ] Two independent factor families are required before interactions.

## Boundaries

- [ ] No weekly-profile rescue.
- [ ] No threshold refinement after outcomes.
- [ ] No entry, stop, target, runner or position-management search.
- [ ] No Pine or deployment authorization.
