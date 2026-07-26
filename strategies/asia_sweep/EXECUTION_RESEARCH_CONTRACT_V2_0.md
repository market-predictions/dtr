# Asian Sweep Executable Reversal Research Contract v2.0

Date frozen: `2026-07-26`  
Work package: `AS-WP-20260726-11`  
Branch: `agent/asia-sweep-execution-research`

## Research question

Can the fully validated T5 Asian Sweep reversal fingerprint be converted into a causal, bid/ask-executable EURUSD/GBPUSD strategy with positive and stable expectancy after spread and modest slippage?

The object under test is not whether the model predicts its label. That question has already passed development, untouched validation and final holdout. The object under test is whether the validated event ranking leaves enough tradable reward after T5 to compensate for the required stop distance and execution friction.

## Immutable upstream inputs

- Amsterdam-native fingerprint engine;
- frozen T5 event population;
- frozen histogram-gradient-boosting model from run `30177831134`;
- out-of-fold T5 predictions for 2015–2021;
- frozen-model predictions for 2022–2025;
- exact threshold `0.18252984704127595`;
- qualified Dukascopy BID and ASK M1 source run `30111481052`.

No model component may be refit, recalibrated, reweighted or thresholded differently.

## Decision time and data availability

The T5 timestamp is the timestamp of the fifth completed M1 bar beginning with the sweep minute. The strategy may act only on an active quote strictly after that bar is complete.

The first eligible market-entry timestamp is therefore the first active M1 timestamp satisfying:

`timestamp > t5_timestamp_utc`

and occurring before 10:00 Europe/Amsterdam.

No sweep-minute, T5-bar or future-week information may be used for fills.

## Trade direction

- upper Asian-range sweep (`UP`): short reversal;
- lower Asian-range sweep (`DOWN`): long reversal.

## Signal eligibility

An event is executable only when:

1. it belongs to the frozen T5-unresolved population;
2. the frozen probability is at least `0.18252984704127595`;
3. both BID and ASK quotes are active at the required decision/fill timestamps;
4. no earlier trade has been taken in the same pair on the same Amsterdam date;
5. no same-pair position remains open;
6. the entry occurs before 10:00 Amsterdam;
7. the entry price remains between the frozen stop and midpoint target.

The full-week top-ranked event is prohibited because it requires knowledge of later candidates.

## Entry variants

### E1 — MKT_NEXT_OPEN

Enter at the first active minute open strictly after T5:

- long: ASK open;
- short: BID open.

### E2 — LIMIT_ASIAN_BOUNDARY

After T5, place a limit at the swept Asian boundary:

- long after a lower sweep: buy limit at Asian low;
- short after an upper sweep: sell limit at Asian high.

The order expires at 10:00 Amsterdam. A fill requires the executable quote to trade through the limit:

- long: ASK low at or below the limit;
- short: BID high at or above the limit.

### E3 — LIMIT_HALF_RETRACE

At T5, compute the midpoint-market close as the average of BID close and ASK close. Place a post-T5 limit halfway between that T5 midpoint close and the swept Asian boundary.

The order expires at 10:00. Fill-side rules are identical to E2.

## Stop

The stop is the exact adverse-continuation barrier used by the validated label:

- upper sweep/short: `sweep_extreme + 0.20 × Asian range`;
- lower sweep/long: `sweep_extreme - 0.20 × Asian range`.

Trigger side:

- long stop: BID low at or below stop;
- short stop: ASK high at or above stop.

Base fill is the stop price. Additional slippage stress is applied away from the trade direction.

## Target

Target is the frozen Asian midpoint:

- long target: BID high at or above midpoint;
- short target: ASK low at or below midpoint.

Target fills at the midpoint price. No favorable limit-price improvement is credited.

## Time exit

If neither stop nor target resolves first, exit at the executable close of the last active M1 bar with Amsterdam timestamp before 10:00:

- long exit: BID close;
- short exit: ASK close.

## Intrabar ambiguity

When stop and target are both touched in the same M1 bar, stop is assumed to occur first. The trade is marked `AMBIGUOUS_STOP_FIRST` for audit.

For limit entries, if entry and stop or target are all touched in the same bar, the conservative ordering is:

1. entry;
2. stop;
3. target.

This prohibits favorable path assumptions unsupported by M1 data.

## Costs

Qualified BID/ASK data embeds spread.

Additional deterministic slippage stresses:

- base: `0.00` pip;
- moderate: `0.10` pip per market or stop execution;
- severe: `0.25` pip per market or stop execution.

Target-limit fills receive no additional slippage. Time exits are treated as market exits and receive the stated stress.

## Return and R

Initial risk is measured from executable entry price to stop price before additional stress:

- long: `entry_ask - stop`;
- short: `stop - entry_bid`.

A trade is invalid when initial risk is non-positive or target distance is non-positive.

Net R is executable signed price return divided by initial risk. Spread is already included because entry and exit use the correct BID/ASK sides.

## Chronological lockout

Events are processed by pair, Amsterdam date, T5 timestamp and event ID.

- maximum one filled trade per pair per Amsterdam date;
- an unfilled limit does not consume the daily trade allowance;
- once a trade fills, all later same-pair events that day are ignored;
- EURUSD and GBPUSD may both trade; portfolio correlation is deferred.

## Partitions and prediction provenance

### Discovery — 2015–2019

Use only out-of-fold T5 probabilities from the frozen development decision.

### Validation — 2020–2021

Use only out-of-fold T5 probabilities. The selected execution variant and all rules are frozen before inspection.

### First execution holdout — 2022–2023

Use probabilities generated by the unchanged serialized model.

### Final execution holdout — 2024–2025

Use probabilities generated by the unchanged serialized model.

## Variant hierarchy

- E1 is evaluated first and has primary authority.
- E2 and E3 may gain selection authority only when E1 fails at least one discovery gate.
- A challenger must pass every discovery gate and improve over E1 by at least `0.05R` expectancy and `0.50` return/max-drawdown.
- No blended entry rule is permitted.

## Discovery gates

All must pass:

1. at least 150 filled trades pooled;
2. at least 50 per pair;
3. expectancy greater than `0.05R`;
4. median annual expectancy positive;
5. at least four of five years positive;
6. both pairs positive;
7. max drawdown below `20R`;
8. net-R/max-drawdown at least `1.50`;
9. calendar-week block-bootstrap probability expectancy positive at least `95%`;
10. expectancy positive under `0.10` pip stress.

## Validation and holdout gates

All must pass independently:

1. at least 50 fills pooled;
2. pooled expectancy positive;
3. both pairs positive;
4. each year positive;
5. net-R/max-drawdown at least `1.00`;
6. expectancy positive under `0.10` pip stress;
7. largest winning trade no more than 20% of total net R;
8. no contract change.

## Required reporting

- fills, unfilled orders and invalid entries;
- net R, expectancy, median trade and win rate;
- target, stop, time and ambiguous exits;
- max drawdown and net-R/drawdown;
- pair, year, weekday, side and probability-quintile attribution;
- base, 0.10-pip and 0.25-pip stress;
- entry delay, initial risk and reward/risk distributions;
- bootstrap interval and probability expectancy positive;
- exact source/model/artifact hashes.

## Stop conditions

- If no entry variant passes discovery, stop before 2020–2025 P&L.
- If the frozen variant fails validation, stop before 2022–2025.
- If it fails the first holdout, stop before final holdout.
- No rescue through a new threshold, pair, weekday, direction, stop, target or management rule.

## Separate continuation programme

Low reversal probability is not automatically a continuation trade. The continuation/fake-rejection hypothesis remains isolated in `FINGERPRINT_CONTINUATION_TRIAGE_ROADMAP.md` and cannot borrow execution outcomes from this contract as a hidden rescue.
