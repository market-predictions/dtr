from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from stacey_burke_lab.fx_source import INSTRUMENTS, write_json

REQUIRED_SYMBOLS = tuple(item.symbol for item in INSTRUMENTS)
REQUIRED_FACTOR_BLOCKS = tuple(sorted({item.factor_block for item in INSTRUMENTS}))
BOOTSTRAP_ITERATIONS = 10_000
PERMUTATION_ITERATIONS = 10_000
BOOTSTRAP_SEED = 20260725
PERMUTATION_SEED = 20260726


def date_block_bootstrap(
    events: pd.DataFrame,
    *,
    iterations: int = BOOTSTRAP_ITERATIONS,
    seed: int = BOOTSTRAP_SEED,
    batch_size: int = 1_024,
) -> dict[str, float | int]:
    if events.empty:
        raise ValueError("cannot bootstrap an empty controlled-study ledger")
    if iterations <= 0 or batch_size <= 0:
        raise ValueError("bootstrap iterations and batch size must be positive")
    grouped = events.groupby("london_date", sort=True, observed=True)["effect_atr"]
    block_sums = grouped.sum().to_numpy(dtype="float64")
    block_counts = grouped.size().to_numpy(dtype="int64")
    rng = np.random.default_rng(seed)
    means = np.empty(iterations, dtype="float64")
    blocks = len(block_sums)
    for start in range(0, iterations, batch_size):
        end = min(start + batch_size, iterations)
        selected = rng.integers(0, blocks, size=(end - start, blocks))
        means[start:end] = block_sums[selected].sum(axis=1) / block_counts[
            selected
        ].sum(axis=1)
    return {
        "iterations": iterations,
        "blocks": blocks,
        "observed_mean_effect_atr": float(events["effect_atr"].mean()),
        "lo95_mean_effect_atr": float(np.quantile(means, 0.025)),
        "hi95_mean_effect_atr": float(np.quantile(means, 0.975)),
        "probability_mean_positive": float(np.mean(means > 0)),
    }


def clustered_matched_set_permutation(
    *,
    events: pd.DataFrame,
    controls: pd.DataFrame,
    iterations: int = PERMUTATION_ITERATIONS,
    seed: int = PERMUTATION_SEED,
    batch_size: int = 256,
) -> dict[str, float | int]:
    if events.empty:
        raise ValueError("cannot permute an empty controlled-study ledger")
    ordered_controls = controls.sort_values(
        ["event_id", "control_rank"],
        kind="mergesort",
    )
    control_matrix = ordered_controls.pivot(
        index="event_id",
        columns="control_rank",
        values="control_outcome_atr",
    )
    expected_ranks = [1, 2, 3, 4, 5]
    if control_matrix.columns.tolist() != expected_ranks:
        raise ValueError("every event must retain exactly five ranked controls")
    ordered_events = events.sort_values("event_id", kind="mergesort").set_index("event_id")
    control_matrix = control_matrix.reindex(ordered_events.index)
    if control_matrix.isna().any().any():
        raise ValueError("control matrix contains missing matched outcomes")

    values = np.column_stack(
        [
            ordered_events["event_outcome_atr"].to_numpy(dtype="float64"),
            control_matrix.to_numpy(dtype="float64"),
        ]
    )
    observed = float(
        (
            ordered_events["event_outcome_atr"]
            - control_matrix.mean(axis=1)
        ).mean()
    )
    unique_dates, date_inverse = np.unique(
        ordered_events["london_date"].astype(str).to_numpy(),
        return_inverse=True,
    )
    value_sums = values.sum(axis=1)
    rng = np.random.default_rng(seed)
    permuted = np.empty(iterations, dtype="float64")
    for start in range(0, iterations, batch_size):
        end = min(start + batch_size, iterations)
        date_choices = rng.integers(
            0,
            values.shape[1],
            size=(end - start, len(unique_dates)),
        )
        row_choices = date_choices[:, date_inverse]
        broadcast_values = np.broadcast_to(values, (end - start, *values.shape))
        selected = np.take_along_axis(
            broadcast_values,
            row_choices[..., None],
            axis=2,
        ).squeeze(axis=2)
        pseudo_effect = 1.2 * selected - 0.2 * value_sums[None, :]
        permuted[start:end] = pseudo_effect.mean(axis=1)
    p_value = float((1 + np.sum(permuted >= observed)) / (iterations + 1))
    return {
        "iterations": iterations,
        "date_blocks": int(len(unique_dates)),
        "observed_mean_effect_atr": observed,
        "one_sided_p_value": p_value,
        "permuted_p95_mean_effect_atr": float(np.quantile(permuted, 0.95)),
    }


def _load_inputs(inputs: Path) -> tuple[list[dict[str, Any]], pd.DataFrame, pd.DataFrame]:
    summaries = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(inputs.rglob("*_controlled_event_study_summary.json"))
    ]
    event_paths = sorted(inputs.rglob("*_controlled_event_study_events.csv"))
    control_paths = sorted(inputs.rglob("*_controlled_event_study_controls.csv"))
    events = pd.concat((pd.read_csv(path) for path in event_paths), ignore_index=True)
    controls = pd.concat((pd.read_csv(path) for path in control_paths), ignore_index=True)
    return summaries, events, controls


def build_gate_b_decision(
    *,
    summaries: list[dict[str, Any]],
    events: pd.DataFrame,
    controls: pd.DataFrame,
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    symbols = [str(summary.get("symbol", "")) for summary in summaries]
    observed_symbols = set(symbols)
    missing_symbols = sorted(set(REQUIRED_SYMBOLS) - observed_symbols)
    unexpected_symbols = sorted(observed_symbols - set(REQUIRED_SYMBOLS))
    duplicate_symbols = sorted(
        symbol for symbol in observed_symbols if symbols.count(symbol) > 1
    )
    definitions = {
        json.dumps(summary.get("definition"), sort_keys=True)
        for summary in summaries
    }
    definition_consistent = len(definitions) == 1 and len(summaries) == len(REQUIRED_SYMBOLS)
    no_strategy_execution = all(
        summary.get("performance_execution") is False
        and summary.get("strategy_pnl_calculated") is False
        for summary in summaries
    )

    event_ids = set(events["event_id"].astype(str))
    control_counts = controls.groupby("event_id", observed=True).size()
    controls_complete = (
        set(control_counts.index.astype(str)) == event_ids
        and bool((control_counts == 5).all())
        and len(controls) == 5 * len(events)
    )
    distinct_control_dates = (
        controls.groupby("event_id", observed=True)["control_london_date"].nunique()
    )
    controls_use_distinct_dates = bool((distinct_control_dates == 5).all())

    bootstrap = date_block_bootstrap(events)
    permutation = clustered_matched_set_permutation(events=events, controls=controls)

    pair_summary = (
        events.groupby(["symbol", "factor_block"], sort=True, observed=True)
        .agg(
            matched_events=("event_id", "size"),
            mean_event_outcome_atr=("event_outcome_atr", "mean"),
            mean_control_outcome_atr=("control_mean_outcome_atr", "mean"),
            mean_effect_atr=("effect_atr", "mean"),
        )
        .reset_index()
    )
    factor_summary = (
        events.groupby("factor_block", sort=True, observed=True)
        .agg(
            matched_events=("event_id", "size"),
            mean_effect_atr=("effect_atr", "mean"),
        )
        .reset_index()
    )
    positive_pairs = int((pair_summary["mean_effect_atr"] > 0).sum())
    positive_factor_blocks = int((factor_summary["mean_effect_atr"] > 0).sum())
    mean_effect = float(events["effect_atr"].mean())

    integrity_gates = {
        "all_ten_pairs_present": (
            not missing_symbols
            and not unexpected_symbols
            and not duplicate_symbols
            and len(summaries) == len(REQUIRED_SYMBOLS)
        ),
        "definition_consistent": definition_consistent,
        "no_strategy_execution": no_strategy_execution,
        "five_controls_per_event": controls_complete,
        "distinct_control_dates_per_event": controls_use_distinct_dates,
        "finite_effects": bool(
            np.isfinite(events["event_outcome_atr"]).all()
            and np.isfinite(events["control_mean_outcome_atr"]).all()
            and np.isfinite(events["effect_atr"]).all()
        ),
    }
    scientific_gates = {
        "minimum_400_matched_events": len(events) >= 400,
        "minimum_mean_effect_0_02_atr": mean_effect >= 0.02,
        "date_block_ci_lower_above_zero": bootstrap["lo95_mean_effect_atr"] > 0,
        "date_clustered_permutation_p_le_0_05": permutation["one_sided_p_value"] <= 0.05,
        "positive_pair_breadth_7_of_10": positive_pairs >= 7,
        "positive_factor_breadth_3_of_4": positive_factor_blocks >= 3,
    }
    qualified = all(integrity_gates.values()) and all(scientific_gates.values())
    decision: dict[str, Any] = {
        "programme": "stacey_burke_controlled_event_study_v1",
        "decision": (
            "PASS_GATE_B_AUTHORIZE_2022_2023_VALIDATION"
            if qualified
            else "FAIL_GATE_B_STOP_STACEY_BURKE_REVERSAL_PROGRAMME"
        ),
        "qualified": qualified,
        "performance_execution": False,
        "strategy_pnl_calculated": False,
        "definition": json.loads(next(iter(definitions))) if definition_consistent else None,
        "required_symbols": list(REQUIRED_SYMBOLS),
        "required_factor_blocks": list(REQUIRED_FACTOR_BLOCKS),
        "missing_symbols": missing_symbols,
        "unexpected_symbols": unexpected_symbols,
        "duplicate_symbols": duplicate_symbols,
        "matched_events": int(len(events)),
        "controls": int(len(controls)),
        "mean_event_outcome_atr": float(events["event_outcome_atr"].mean()),
        "mean_control_outcome_atr": float(events["control_mean_outcome_atr"].mean()),
        "mean_effect_atr": mean_effect,
        "positive_pairs": positive_pairs,
        "positive_factor_blocks": positive_factor_blocks,
        "bootstrap": bootstrap,
        "permutation": permutation,
        "integrity_gates": integrity_gates,
        "scientific_gates": scientific_gates,
    }
    return decision, pair_summary, factor_summary


def summarize_and_enforce(*, inputs: Path, output: Path) -> dict[str, Any]:
    summaries, events, controls = _load_inputs(inputs)
    decision, pair_summary, factor_summary = build_gate_b_decision(
        summaries=summaries,
        events=events,
        controls=controls,
    )
    output.mkdir(parents=True, exist_ok=True)
    write_json(decision, output / "controlled_event_study_gate_b_decision.json")
    pair_summary.to_csv(output / "controlled_event_study_pair_summary.csv", index=False)
    factor_summary.to_csv(output / "controlled_event_study_factor_summary.csv", index=False)
    events.to_csv(output / "controlled_event_study_events.csv", index=False)
    controls.to_csv(output / "controlled_event_study_controls.csv", index=False)
    return decision


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aggregate and enforce Stacey Burke controlled event-study Gate B"
    )
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    decision = summarize_and_enforce(inputs=args.inputs, output=args.out)
    print(
        f"{decision['decision']}: {decision['matched_events']} matched events, "
        f"effect {decision['mean_effect_atr']:.6f} ATR, "
        f"p={decision['permutation']['one_sided_p_value']:.6f}"
    )
    if not decision["qualified"]:
        raise SystemExit(decision["decision"])


if __name__ == "__main__":
    main()
