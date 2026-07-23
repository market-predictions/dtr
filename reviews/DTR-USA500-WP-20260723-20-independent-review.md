# Independent Review — DTR-USA500-WP-20260723-20

## Conclusion

`INDEPENDENT_REVIEW_PASS`

## Calculation review

The verifier independently recalculated all saved Stage 1, Stage 2 and Stage 3 trade-stream metrics, including trade count, net R, expectancy, maximum drawdown and return/drawdown. All values reproduced to the declared numerical tolerance.

Observed paired date-block effects were independently reconstructed for every calendar, context and event arm. A separate seed family was used for descriptive uncertainty.

## Roadmap review

The programme complied with the agreed sequence:

- started from the unfiltered frozen core;
- ran the Monday × Asia factorial before session decomposition;
- retained NQ E6 and NQ E6 no-FOMC as external controls only;
- tested fixed single-factor context rules without interactions;
- tested event exclusions one at a time;
- did not retune core signal, stop, target, session-time, cost or gap parameters;
- did not authorize deployment.

## Stage 1B review

The session-decomposition verifier independently re-sequenced every arm from the complete cached signal-trade stream. All metrics and paired effects reproduced exactly.

London-only was positive at one and two ticks per side, but failed the preregistered gate because:

- 2022 was -2.72R;
- 2025 was -6.26R;
- the positive result was concentrated in 2023–2024;
- the paired interval versus all sessions crossed zero;
- four-tick expectancy was negative.

The stop rule was correctly applied. No context or event optimization was run on London-only after the failed session gate.

## Final independent decision

`NO_VIABLE_USA500_CORE_BASELINE`

London-only remains an exploratory diagnostic. It is not an ES/USA500 baseline, and no Pine, sizing or deployment work follows.
