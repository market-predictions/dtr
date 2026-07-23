from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from dtr_lab.research import engine
from dtr_lab.research.cross_market import (
    USA500_PROXY_SPEC,
    build_covered_session_table,
    classify_proxy_gaps,
)

BASE_PATH = Path(__file__).with_name("run_usa500_baseline_discovery.py")
spec = importlib.util.spec_from_file_location("usa500_base_program", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("unable to import base programme")
base = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = base
spec.loader.exec_module(base)


def gate_session(row: pd.Series, baseline: pd.Series) -> dict[str, bool]:
    return {
        "gate_cost": bool(row["one_tick_expectancy_r"] > 0 and row["two_tick_expectancy_r"] > 0),
        "gate_return_dd": bool(row["return_dd"] >= baseline["return_dd"] * 1.15),
        "gate_years": bool(row["positive_years"] >= 3 and row["net_2025"] >= 0),
        "gate_sample": bool(row["trades"] >= 180 or row["trades"] >= baseline["trades"] * 0.40),
        "gate_concentration": bool(row["single_year_positive_net_share"] <= 0.70),
        "gate_paired_mean": bool(row["observed_net_difference_r"] > 0),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--usa500", type=Path, required=True)
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=20260923)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    one = base.load_proxy(args.usa500)
    gaps = classify_proxy_gaps(one)
    bars = base.attach_gap_metadata(engine.resample_5m(one), gaps)
    sessions_raw = build_covered_session_table(
        one, bars, minimum_coverage=USA500_PROXY_SPEC.minimum_range_coverage
    )
    sessions = base.sanitize_sessions(sessions_raw, bars, gaps)
    eligible = (
        sessions.loc[~sessions["integrity_range_gap_rejected"]]
        .copy()
        .sort_values(["range_start", "session"])
    )
    cfg = replace(
        USA500_PROXY_SPEC.strategy_config(name="USA500_SESSION_DECOMPOSITION"),
        weekdays=(0, 1, 2, 3, 4),
        sessions=("LONDON_2AM", "NEW_YORK_9AM", "ASIA_7PM"),
    )
    signals, funnel = engine.generate_signals(bars, eligible, cfg)
    cached = base.simulate_all(one, bars, signals, cfg, gaps)
    features = pd.read_csv(
        args.prior / "signal_features.csv.gz", parse_dates=["session_date", "entry_time"]
    )
    if len(features) != len(signals) or not np.array_equal(
        features["signal_id"].to_numpy(int), np.arange(len(signals))
    ):
        raise RuntimeError("signal cache does not match frozen Stage 1 features")

    session_arms = {
        "S0_ALL": ("ASIA_7PM", "LONDON_2AM", "NEW_YORK_9AM"),
        "S1_LONDON_ONLY": ("LONDON_2AM",),
        "S2_NEW_YORK_ONLY": ("NEW_YORK_9AM",),
        "S3_ASIA_ONLY": ("ASIA_7PM",),
        "S4_LONDON_ASIA": ("LONDON_2AM", "ASIA_7PM"),
        "S5_ASIA_NEW_YORK": ("ASIA_7PM", "NEW_YORK_9AM"),
    }
    weekdays = (1, 2, 3, 4)
    trades_by_arm: dict[str, pd.DataFrame] = {}
    rows = []
    for index, (arm, allowed) in enumerate(session_arms.items()):
        mask = features["weekday"].isin(weekdays) & features["session"].isin(allowed)
        trades = base.sequence(features, cached, mask)
        trades_by_arm[arm] = trades
        summary = base.summarize(
            trades,
            arm,
            base.eligible_count(eligible, weekdays, allowed),
            int(mask.sum()),
            cfg.tick_size,
        )
        summary.update(
            base.block_bootstrap(trades, "date", args.iterations, args.seed + 10 + index)
        )
        rows.append(summary)
    table = pd.DataFrame(rows)
    baseline = table.loc[table["arm"] == "S0_ALL"].iloc[0]
    for index, row in table.iterrows():
        arm = row["arm"]
        if arm == "S0_ALL":
            paired = {
                "observed_net_difference_r": 0.0,
                "lo95_net_difference_r": 0.0,
                "hi95_net_difference_r": 0.0,
                "prob_net_difference_positive": np.nan,
            }
            flags = {
                key: True
                for key in (
                    "gate_cost",
                    "gate_return_dd",
                    "gate_years",
                    "gate_sample",
                    "gate_concentration",
                    "gate_paired_mean",
                )
            }
        else:
            paired = base.paired_date_bootstrap(
                trades_by_arm[arm],
                trades_by_arm["S0_ALL"],
                args.iterations,
                args.seed + 100 + index,
            )
            for key, value in paired.items():
                table.loc[index, key] = value
            combined = row.to_dict()
            combined.update(paired)
            flags = gate_session(pd.Series(combined), baseline)
        for key, value in paired.items():
            table.loc[index, key] = value
        for key, value in flags.items():
            table.loc[index, key] = value
        table.loc[index, "gate_all"] = all(flags.values())
        table.loc[index, "uncertainty_class"] = (
            "SUPPORTED"
            if paired["lo95_net_difference_r"] > 0
            else "EXPLORATORY"
            if paired["observed_net_difference_r"] > 0
            else "NOT_BETTER"
        )

    passing = table.loc[(table["arm"] != "S0_ALL") & table["gate_all"]]
    selected_session = (
        None
        if passing.empty
        else passing.sort_values(
            ["return_dd", "two_tick_expectancy_r", "net_r"], ascending=False
        ).iloc[0]["arm"]
    )

    context_table = pd.DataFrame()
    event_table = pd.DataFrame()
    selected_context = None
    selected_event = None
    if selected_session is not None:
        session_mask = features["weekday"].isin(weekdays) & features["session"].isin(
            session_arms[selected_session]
        )
        session_trades = trades_by_arm[selected_session]
        context_masks = {
            "C0_SESSION_BASELINE": session_mask,
            "C1_EXCLUDE_COMPRESSED_RANGE": session_mask
            & (features["range_percentile"].isna() | (features["range_percentile"] >= 1 / 3)),
            "C2_EXCLUDE_NEAR_PRIOR_DAY_EXTREME": session_mask
            & (
                features["directional_extreme_distance_atr"].isna()
                | (features["directional_extreme_distance_atr"] > 0.25)
            ),
            "C3_PATH_LE_12_BARS": session_mask & (features["sweep_to_entry_bars"] <= 12),
            "C4_ENTRY_EXTENSION_LE_0_35R": session_mask & (features["entry_extension_r"] <= 0.35),
            "C5_BOS_QUALITY_2_OF_3": session_mask & (features["bos_quality_score"] >= 2),
            "C6_CLEAR_TO_TP1": session_mask & (features["clearance_r"] >= cfg.tp1_rr),
        }
        context_trades: dict[str, pd.DataFrame] = {}
        context_rows = []
        for index, (arm, mask) in enumerate(context_masks.items()):
            trades = base.sequence(features, cached, mask)
            context_trades[arm] = trades
            summary = base.summarize(
                trades,
                arm,
                base.eligible_count(eligible, weekdays, session_arms[selected_session]),
                int(mask.sum()),
                cfg.tick_size,
            )
            paired = (
                {
                    "observed_net_difference_r": 0.0,
                    "lo95_net_difference_r": 0.0,
                    "hi95_net_difference_r": 0.0,
                    "prob_net_difference_positive": np.nan,
                }
                if arm == "C0_SESSION_BASELINE"
                else base.paired_date_bootstrap(
                    trades, session_trades, args.iterations, args.seed + 200 + index
                )
            )
            summary.update(paired)
            context_rows.append(summary)
        context_table = pd.DataFrame(context_rows)
        context_baseline = context_table.loc[context_table["arm"] == "C0_SESSION_BASELINE"].iloc[0]
        for index, row in context_table.iterrows():
            flags = (
                {
                    key: True
                    for key in (
                        "gate_retention",
                        "gate_cost",
                        "gate_return_dd",
                        "gate_years",
                        "gate_paired_mean",
                    )
                }
                if row["arm"] == "C0_SESSION_BASELINE"
                else base.gate_stage2(row, context_baseline)
            )
            for key, value in flags.items():
                context_table.loc[index, key] = value
            context_table.loc[index, "gate_all"] = all(flags.values())
            context_table.loc[index, "uncertainty_class"] = (
                "SUPPORTED"
                if row["lo95_net_difference_r"] > 0
                else "EXPLORATORY"
                if row["observed_net_difference_r"] > 0
                else "NOT_BETTER"
            )
        passing_context = context_table.loc[
            (context_table["arm"] != "C0_SESSION_BASELINE") & context_table["gate_all"]
        ]
        selected_context = (
            "C0_SESSION_BASELINE"
            if passing_context.empty
            else passing_context.sort_values(
                ["return_dd", "two_tick_expectancy_r", "net_r"], ascending=False
            ).iloc[0]["arm"]
        )
        selected_mask = context_masks[selected_context]
        selected_trades = context_trades[selected_context]

        event_rows = []
        event_trades: dict[str, pd.DataFrame] = {"E0_CONTEXT_BASELINE": selected_trades}
        base_summary = base.summarize(
            selected_trades,
            "E0_CONTEXT_BASELINE",
            base.eligible_count(eligible, weekdays, session_arms[selected_session]),
            int(selected_mask.sum()),
            cfg.tick_size,
        )
        base_summary.update(
            {
                "observed_net_difference_r": 0.0,
                "lo95_net_difference_r": 0.0,
                "hi95_net_difference_r": 0.0,
                "prob_net_difference_positive": np.nan,
            }
        )
        event_rows.append(base_summary)
        for index, (event_name, event_mask) in enumerate(base.event_masks(features).items()):
            arm = f"E_{event_name}"
            trades = base.sequence(features, cached, selected_mask & event_mask)
            event_trades[arm] = trades
            summary = base.summarize(
                trades,
                arm,
                base.eligible_count(eligible, weekdays, session_arms[selected_session]),
                int((selected_mask & event_mask).sum()),
                cfg.tick_size,
            )
            summary.update(
                base.paired_date_bootstrap(
                    trades, selected_trades, args.iterations, args.seed + 300 + index
                )
            )
            changed = base.changed_attribution(
                selected_trades, trades, f"{selected_context}->{arm}"
            )
            flags = base.event_gate(
                selected_trades, trades, pd.Series(summary), pd.Series(base_summary), changed
            )
            summary.update(flags)
            summary["gate_all"] = (
                all(flags.values())
                and summary["one_tick_expectancy_r"] > 0
                and summary["two_tick_expectancy_r"] > 0
            )
            event_rows.append(summary)
        event_table = pd.DataFrame(event_rows)
        passing_events = event_table.loc[
            (event_table["arm"] != "E0_CONTEXT_BASELINE") & event_table["gate_all"].fillna(False)
        ]
        selected_event = (
            "E0_CONTEXT_BASELINE"
            if passing_events.empty
            else passing_events.sort_values(
                ["return_dd", "two_tick_expectancy_r", "net_r"], ascending=False
            ).iloc[0]["arm"]
        )

        for arm, trades in {**context_trades, **event_trades}.items():
            trades.to_csv(args.out / f"{arm}__trades.csv", index=False)

    all_cached = []
    for signal_id, trade in cached.items():
        all_cached.append({"signal_id": signal_id, **base.asdict(trade)})
    pd.DataFrame(all_cached).to_csv(
        args.out / "all_signal_trades.csv.gz", index=False, compression="gzip"
    )
    for arm, trades in trades_by_arm.items():
        trades.to_csv(args.out / f"{arm}__trades.csv", index=False)
    table.to_csv(args.out / "stage1b_session_decomposition.csv", index=False)
    if not context_table.empty:
        context_table.to_csv(args.out / "stage2_session_context_candidates.csv", index=False)
    if not event_table.empty:
        event_table.to_csv(args.out / "stage3_session_event_candidates.csv", index=False)

    decision = {
        "study_id": "DTR-USA500-WP-20260723-20-STAGE1B",
        "preregistration_commit": "27fd484702c15b745e3471e1fd9e0991f76a4329",
        "funnel": funnel.as_dict(),
        "selected_session": selected_session,
        "selected_context": selected_context,
        "selected_event": selected_event,
        "decision": "NO_VIABLE_USA500_CORE_BASELINE"
        if selected_session is None
        else "EXPLORATORY_USA500_SESSION_CANDIDATE",
        "no_deployment_authorization": True,
    }
    (args.out / "stage1b_decision.json").write_text(
        json.dumps(decision, indent=2), encoding="utf-8"
    )
    print(json.dumps(decision, indent=2))
    print(
        table[
            [
                "arm",
                "trades",
                "net_r",
                "expectancy_r",
                "two_tick_expectancy_r",
                "max_drawdown_r",
                "return_dd",
                "net_2022",
                "net_2023",
                "net_2024",
                "net_2025",
                "gate_all",
                "uncertainty_class",
            ]
        ].to_string(index=False)
    )
    if not context_table.empty:
        print(
            "\nCONTEXT\n",
            context_table[
                [
                    "arm",
                    "trades",
                    "net_r",
                    "expectancy_r",
                    "two_tick_expectancy_r",
                    "max_drawdown_r",
                    "return_dd",
                    "gate_all",
                    "uncertainty_class",
                ]
            ].to_string(index=False),
        )
    if not event_table.empty:
        print(
            "\nEVENTS\n",
            event_table[
                [
                    "arm",
                    "trades",
                    "net_r",
                    "expectancy_r",
                    "two_tick_expectancy_r",
                    "max_drawdown_r",
                    "return_dd",
                    "gate_all",
                ]
            ].to_string(index=False),
        )


if __name__ == "__main__":
    main()
