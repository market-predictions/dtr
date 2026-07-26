# Wayne Pivots — Geometry Authorization Gate v0.3

Date frozen: 2026-07-27

## Comparison family

For each of six source-faithful Wayne side/target candidates:

- bull to M4;
- bull to R1;
- bull to R2;
- bear to M1;
- bear to S1;
- bear to S2;

compare the Wayne structure with all ten preregistered placebo structures on pair-days where both structures produce a fresh touched-zone event.

## Individual comparison gate

A Wayne-versus-placebo comparison passes only when all conditions hold:

- at least 400 matched events;
- at least 75 matched events in at least four primary pairs;
- Wayne success-rate lift at least +5 percentage points;
- Wayne mean strict-payoff effect greater than 0R;
- positive success and payoff effects in at least four primary pairs;
- positive success and payoff effects in at least four eligible years;
- maximum pair concentration of absolute payoff effect at most 40%;
- maximum year concentration of absolute payoff effect at most 30%;
- date-block bootstrap probability of positive payoff effect at least 90%;
- full-family FDR q-value at most 0.10.

## Candidate gate

A side/target candidate passes geometry only when:

- the unpaired Wayne anatomy population has at least 400 fresh events;
- at least four primary pairs have at least 75 fresh Wayne events;
- success lift is positive against at least 8 of 10 placebos;
- payoff effect is positive against at least 8 of 10 placebos;
- at least 5 of 10 placebo comparisons pass the complete individual gate;
- Wayne has positive payoff effect versus both `PRIOR_CLOSE` and `RANGE_MID`;
- at least one of `PRIOR_CLOSE` or `RANGE_MID` passes the complete individual gate.

## Programme authorization

- one or more candidate gates pass: authorize a separately frozen directional-bias attribution stage;
- no candidate gate passes: `FAIL_DAILY_PIVOT_GEOMETRY_STOP_BEFORE_BIAS`.

No threshold refinement, placebo removal, pair rescue, year rescue, direction rescue or target rescue is allowed after inspection.
