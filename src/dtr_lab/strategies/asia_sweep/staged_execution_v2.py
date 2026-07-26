from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from dtr_lab.strategies.asia_sweep.execution_contract import PIP_SIZE, amsterdam_1000
from dtr_lab.strategies.asia_sweep.execution_simulator import load_bid_ask_minutes

LANDMARKS = ("T0", "T1", "T2", "T3")
STAGED_POLICIES = (
    "T0_QUARTERS",
    "T1_QUARTERS",
    "T0_CONCENTRATED",
    "T0_LATE_WEIGHTED",
)
REFERENCE_POLICIES = (
    "T0_STATIC_025",
    "T1_STATIC_025",
    "T0_STATIC_100",
)
DIAGNOSTIC_POLICIES = (
    "T0_STATIC_025_UNCONDITIONAL",
    "T0_STATIC_100_UNCONDITIONAL",
)
POLICIES = STAGED_POLICIES + REFERENCE_POLICIES + DIAGNOSTIC_POLICIES
SLIPPAGE_PIPS = 0.10
ADD_THRESHOLDS = {"T1": 0.19, "T2": 0.21, "T3": 0.23}


@dataclass(frozen=True)
class Tranche:
    allocation_r: float
    entry_price: float
    entry_timestamp: pd.Timestamp
    risk_price: float


@dataclass(frozen=True)
class Resolution:
    reason: str
    timestamp: pd.Timestamp
    price: float
    ambiguous: bool = False


def load_hgb_triage_predictions(directory: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for landmark in LANDMARKS:
        path = directory / f"triage_predictions_{landmark}_hgb.csv"
        frame = pd.read_csv(path)
        if not frame["landmark"].eq(landmark).all() or not frame["family"].eq("hgb").all():
            raise ValueError(f"{path.name}: prediction identity mismatch")
        frames.append(frame)
    predictions = pd.concat(frames, ignore_index=True)
    if predictions.duplicated(["event_id", "landmark"]).any():
        raise ValueError("duplicate triage prediction keys")
    return predictions


def prepare_staged_population(
    ledger: pd.DataFrame,
    predictions: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    required = {
        "event_id",
        "instrument",
        "trade_date",
        "week_key",
        "year",
        "weekday",
        "side",
        "sweep_timestamp_utc",
        "asian_midpoint",
        "stop_price",
        "landmark",
        "entry_price",
        "entry_timestamp_utc",
    }
    missing = sorted(required - set(ledger.columns))
    if missing:
        raise ValueError(f"missing staged columns: {missing}")
    frame = ledger.loc[ledger["landmark"].isin(LANDMARKS)].copy()
    frame["sweep_timestamp_utc"] = pd.to_datetime(
        frame["sweep_timestamp_utc"], utc=True, errors="coerce"
    )
    frame["entry_timestamp_utc"] = pd.to_datetime(
        frame["entry_timestamp_utc"], utc=True, errors="coerce"
    )
    joined = frame.merge(
        predictions[
            [
                "event_id",
                "landmark",
                "p_reversal",
                "p_continuation",
                "p_unresolved",
                "outer_year",
            ]
        ],
        on=["event_id", "landmark"],
        how="inner",
        validate="one_to_one",
    )
    t0 = joined.loc[joined["landmark"].eq("T0")].sort_values(
        ["instrument", "trade_date", "sweep_timestamp_utc", "event_id"],
        kind="mergesort",
    )
    selected_ids: list[str] = []
    same_minute_ambiguous = 0
    ignored_later = 0
    for _, day in t0.groupby(["instrument", "trade_date"], sort=True):
        first_time = day["sweep_timestamp_utc"].min()
        first = day.loc[day["sweep_timestamp_utc"].eq(first_time)]
        if len(first) > 1 and first["side"].nunique() > 1:
            same_minute_ambiguous += 1
            ignored_later += len(day)
            continue
        selected_ids.append(str(first.iloc[0]["event_id"]))
        ignored_later += max(0, len(day) - 1)
    selected = joined.loc[joined["event_id"].isin(selected_ids)].copy()
    selected = selected.sort_values(
        ["instrument", "trade_date", "landmark"], kind="mergesort"
    ).reset_index(drop=True)
    return selected, {
        "candidate_t0_events": int(len(t0)),
        "selected_pair_days": int(len(selected_ids)),
        "same_minute_side_ambiguous_days": int(same_minute_ambiguous),
        "ignored_later_events": int(ignored_later),
    }


def _t0_eligible(row: pd.Series) -> bool:
    return bool(row["p_continuation"] < 0.72 and row["p_unresolved"] < 0.30)


def _add_eligible(row: pd.Series) -> bool:
    landmark = str(row["landmark"])
    return bool(
        landmark in ADD_THRESHOLDS
        and row["p_reversal"] >= ADD_THRESHOLDS[landmark]
        and row["p_continuation"] < 0.72
        and row["p_unresolved"] < 0.35
    )


def _cancel_active(row: pd.Series) -> bool:
    landmark = str(row["landmark"])
    threshold = 0.80 if landmark == "T3" else 0.75
    return bool(
        landmark in ("T1", "T2", "T3")
        and row["p_continuation"] >= threshold
        and row["p_continuation"] - row["p_reversal"] >= 0.40
    )


def _initial_allocation(policy: str, landmark: str, row: pd.Series) -> float:
    if landmark == "T0":
        if policy in DIAGNOSTIC_POLICIES:
            return 1.0 if "100" in policy else 0.25
        if policy.startswith("T0_") and _t0_eligible(row):
            return 1.0 if policy == "T0_STATIC_100" else 0.25
    if landmark == "T1" and policy in ("T1_QUARTERS", "T1_STATIC_025"):
        return 0.25 if _add_eligible(row) and not _cancel_active(row) else 0.0
    return 0.0


def _additional_allocation(
    policy: str,
    landmark: str,
    row: pd.Series,
    current_allocation: float,
    concentrated_add_done: bool,
) -> float:
    if current_allocation <= 0 or not _add_eligible(row):
        return 0.0
    if policy == "T0_QUARTERS" and landmark in ("T1", "T2", "T3"):
        return min(0.25, 1.0 - current_allocation)
    if policy == "T1_QUARTERS" and landmark in ("T2", "T3"):
        return min(0.25, 0.75 - current_allocation)
    if policy == "T0_LATE_WEIGHTED" and landmark in ("T2", "T3"):
        return min(0.375, 1.0 - current_allocation)
    if policy == "T0_CONCENTRATED" and landmark in ("T2", "T3"):
        if concentrated_add_done:
            return min(0.25, 1.0 - current_allocation) if landmark == "T3" else 0.0
        desired = 0.75 if landmark == "T3" else 0.50
        return min(desired, 1.0 - current_allocation)
    return 0.0


def _active_path(bars: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return bars.loc[
        (bars.index >= start) & (bars.index < end) & bars["active"].astype(bool)
    ]


def _resolution_in_path(
    path: pd.DataFrame,
    *,
    is_long: bool,
    stop: float,
    target: float,
) -> Resolution | None:
    for timestamp, bar in path.iterrows():
        stop_hit = (
            float(bar["low_bid"]) <= stop
            if is_long
            else float(bar["high_ask"]) >= stop
        )
        target_hit = (
            float(bar["high_bid"]) >= target
            if is_long
            else float(bar["low_ask"]) <= target
        )
        if stop_hit:
            return Resolution(
                "AMBIGUOUS_STOP_FIRST" if target_hit else "STOP",
                pd.Timestamp(timestamp),
                stop,
                bool(target_hit),
            )
        if target_hit:
            return Resolution("TARGET", pd.Timestamp(timestamp), target)
    return None


def _market_price(
    bars: pd.DataFrame,
    timestamp: pd.Timestamp,
    *,
    is_long: bool,
    use_close: bool,
) -> float:
    if timestamp not in bars.index or not bool(bars.at[timestamp, "active"]):
        raise ValueError(f"inactive executable timestamp: {timestamp}")
    field = "close" if use_close else "open"
    side = "bid" if is_long else "ask"
    return float(bars.at[timestamp, f"{field}_{side}"])


def _trade_pnl(
    tranches: list[Tranche],
    *,
    exit_price: float,
    exit_reason: str,
    is_long: bool,
    pip: float,
) -> float:
    direction = 1.0 if is_long else -1.0
    slippage = SLIPPAGE_PIPS * pip
    total = 0.0
    for tranche in tranches:
        stressed_entry = (
            tranche.entry_price + slippage
            if is_long
            else tranche.entry_price - slippage
        )
        stressed_exit = exit_price
        if exit_reason != "TARGET":
            stressed_exit = exit_price - slippage if is_long else exit_price + slippage
        units = tranche.allocation_r / tranche.risk_price
        total += units * direction * (stressed_exit - stressed_entry)
    return float(total)


def _base_result(row: pd.Series, policy: str) -> dict[str, Any]:
    return {
        "event_id": str(row["event_id"]),
        "instrument": str(row["instrument"]),
        "trade_date": str(row["trade_date"]),
        "week_key": str(row["week_key"]),
        "year": int(row["year"]),
        "weekday": int(row["weekday"]),
        "side": str(row["side"]),
        "policy": policy,
    }


def _filled_result(
    base: dict[str, Any],
    tranches: list[Tranche],
    *,
    allocation: float,
    actions: list[str],
    resolution: Resolution,
    is_long: bool,
    pip: float,
) -> dict[str, Any]:
    return {
        **base,
        "status": "FILLED",
        "exit_reason": resolution.reason,
        "exit_timestamp_utc": resolution.timestamp.isoformat(),
        "net_r": _trade_pnl(
            tranches,
            exit_price=resolution.price,
            exit_reason=resolution.reason,
            is_long=is_long,
            pip=pip,
        ),
        "allocated_r": allocation,
        "tranche_count": len(tranches),
        "actions": ";".join(actions),
        "ambiguous_stop_first": resolution.ambiguous,
    }


def simulate_staged_event(
    event_rows: pd.DataFrame,
    bars: pd.DataFrame,
    *,
    policy: str,
) -> dict[str, Any]:
    if policy not in POLICIES:
        raise ValueError(policy)
    rows = {str(row["landmark"]): row for _, row in event_rows.iterrows()}
    t0 = rows.get("T0")
    if t0 is None:
        raise ValueError("staged event has no T0 row")
    base = _base_result(t0, policy)
    is_long = str(t0["side"]) == "DOWN"
    pip = PIP_SIZE[str(t0["instrument"])]
    stop = float(t0["stop_price"])
    target = float(t0["asian_midpoint"])
    end = amsterdam_1000(str(t0["trade_date"]))
    tranches: list[Tranche] = []
    allocation = 0.0
    concentrated_add_done = False
    actions: list[str] = []
    previous_time: pd.Timestamp | None = None

    for landmark in LANDMARKS:
        row = rows.get(landmark)
        if row is None:
            continue
        decision_time = pd.Timestamp(row["entry_timestamp_utc"])
        if previous_time is not None and tranches:
            resolution = _resolution_in_path(
                _active_path(bars, previous_time, decision_time),
                is_long=is_long,
                stop=stop,
                target=target,
            )
            if resolution is not None:
                return _filled_result(
                    base,
                    tranches,
                    allocation=allocation,
                    actions=actions,
                    resolution=resolution,
                    is_long=is_long,
                    pip=pip,
                )
        if tranches and _cancel_active(row):
            actions.append(f"{landmark}:CANCEL")
            resolution = Resolution(
                "CONTINUATION_CANCEL",
                decision_time,
                _market_price(bars, decision_time, is_long=is_long, use_close=False),
            )
            return _filled_result(
                base,
                tranches,
                allocation=allocation,
                actions=actions,
                resolution=resolution,
                is_long=is_long,
                pip=pip,
            )
        add = (
            _initial_allocation(policy, landmark, row)
            if not tranches
            else _additional_allocation(
                policy, landmark, row, allocation, concentrated_add_done
            )
        )
        if add > 0:
            entry = float(row["entry_price"])
            risk = entry - stop if is_long else stop - entry
            if risk > 0 and allocation + add <= 1.0 + 1e-12:
                tranches.append(Tranche(add, entry, decision_time, float(risk)))
                allocation += add
                actions.append(f"{landmark}:ADD_{add:.3f}")
                if policy == "T0_CONCENTRATED" and landmark in ("T2", "T3"):
                    concentrated_add_done = True
        previous_time = decision_time

    if not tranches:
        return {
            **base,
            "status": "NO_TRADE",
            "exit_reason": None,
            "net_r": 0.0,
            "allocated_r": 0.0,
            "tranche_count": 0,
            "actions": ";".join(actions),
            "ambiguous_stop_first": False,
        }
    if previous_time is None:
        raise RuntimeError("filled event has no decision timestamp")
    resolution = _resolution_in_path(
        _active_path(bars, previous_time, end),
        is_long=is_long,
        stop=stop,
        target=target,
    )
    if resolution is None:
        path = _active_path(bars, previous_time, end)
        if path.empty:
            return {
                **base,
                "status": "NO_ACTIVE_EXIT_PATH",
                "exit_reason": None,
                "net_r": math.nan,
                "allocated_r": allocation,
                "tranche_count": len(tranches),
                "actions": ";".join(actions),
                "ambiguous_stop_first": False,
            }
        exit_time = pd.Timestamp(path.index[-1])
        resolution = Resolution(
            "TIME_1000",
            exit_time,
            _market_price(bars, exit_time, is_long=is_long, use_close=True),
        )
    return _filled_result(
        base,
        tranches,
        allocation=allocation,
        actions=actions,
        resolution=resolution,
        is_long=is_long,
        pip=pip,
    )


def simulate_staged_development(
    population: pd.DataFrame,
    source_root: Path,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (symbol, year), group in population.groupby(["instrument", "year"], sort=True):
        bars = load_bid_ask_minutes(source_root / str(symbol), str(symbol), int(year))
        for _, event_rows in group.groupby("event_id", sort=True):
            for policy in POLICIES:
                rows.append(simulate_staged_event(event_rows, bars, policy=policy))
    return pd.DataFrame(rows)


def _max_drawdown(values: pd.Series) -> float:
    equity = values.fillna(0.0).cumsum()
    return float((equity.cummax() - equity).max()) if len(equity) else 0.0


def _positive_concentration(frame: pd.DataFrame, column: str) -> float:
    contribution = frame.groupby(column)["net_r"].sum().clip(lower=0.0)
    total = float(contribution.sum())
    return float(contribution.max() / total) if total > 0 else 1.0


def summarize_staged(results: pd.DataFrame) -> pd.DataFrame:
    filled = results.loc[results["status"].eq("FILLED")].copy()
    rows: list[dict[str, Any]] = []
    for policy, group in filled.groupby("policy", sort=True):
        ordered = group.sort_values(
            ["trade_date", "instrument", "event_id"], kind="mergesort"
        )
        pair_expectancy = ordered.groupby("instrument")["net_r"].mean()
        year_expectancy = ordered.groupby("year")["net_r"].mean()
        trades_per_pair = ordered.groupby("instrument").size()
        net = float(ordered["net_r"].sum())
        drawdown = _max_drawdown(ordered["net_r"])
        concentration = max(
            _positive_concentration(ordered, "instrument"),
            _positive_concentration(ordered, "year"),
            _positive_concentration(ordered, "side"),
            _positive_concentration(ordered, "weekday"),
        )
        rows.append(
            {
                "policy": policy,
                "trades": int(len(ordered)),
                "minimum_pair_trades": int(trades_per_pair.min()),
                "net_r": net,
                "expectancy_r": float(ordered["net_r"].mean()),
                "median_r": float(ordered["net_r"].median()),
                "win_rate": float(ordered["net_r"].gt(0).mean()),
                "max_drawdown_r": drawdown,
                "return_drawdown": net / drawdown if drawdown > 0 else math.nan,
                "positive_pair_count": int(pair_expectancy.gt(0).sum()),
                "positive_year_count": int(year_expectancy.gt(0).sum()),
                "max_positive_contribution_share": concentration,
                "mean_allocated_r": float(ordered["allocated_r"].mean()),
                "mean_tranche_count": float(ordered["tranche_count"].mean()),
                "cancel_rate": float(
                    ordered["exit_reason"].eq("CONTINUATION_CANCEL").mean()
                ),
                "ambiguous_rate": float(
                    ordered["ambiguous_stop_first"].astype(bool).mean()
                ),
            }
        )
    return pd.DataFrame(rows)


def decide_staged(summary: pd.DataFrame) -> dict[str, Any]:
    reference = {
        "T0_QUARTERS": "T0_STATIC_025",
        "T0_CONCENTRATED": "T0_STATIC_025",
        "T0_LATE_WEIGHTED": "T0_STATIC_025",
        "T1_QUARTERS": "T1_STATIC_025",
    }
    rows: list[dict[str, Any]] = []
    indexed = summary.set_index("policy")
    for policy in STAGED_POLICIES:
        candidate = indexed.loc[policy]
        baseline = indexed.loc[reference[policy]]
        gates = {
            "trades": candidate["trades"] >= 300,
            "trades_per_pair": candidate["minimum_pair_trades"] >= 120,
            "expectancy": candidate["expectancy_r"] > 0,
            "pair_breadth": candidate["positive_pair_count"] == 2,
            "year_breadth": candidate["positive_year_count"] >= 4,
            "return_drawdown": candidate["return_drawdown"] >= 1.50,
            "drawdown": candidate["max_drawdown_r"] <= 20.0,
            "concentration": candidate["max_positive_contribution_share"] <= 0.65,
            "expectancy_improvement": (
                candidate["expectancy_r"] - baseline["expectancy_r"] >= 0.05
            ),
            "return_drawdown_improvement": (
                candidate["return_drawdown"]
                >= 1.25 * baseline["return_drawdown"]
            ),
        }
        rows.append(
            {
                "policy": policy,
                "reference_policy": reference[policy],
                "expectancy_improvement": float(
                    candidate["expectancy_r"] - baseline["expectancy_r"]
                ),
                "return_drawdown_improvement_ratio": float(
                    candidate["return_drawdown"] / baseline["return_drawdown"]
                )
                if baseline["return_drawdown"] != 0
                else math.nan,
                "passes": bool(all(gates.values())),
                "failed_gates": ";".join(
                    key for key, passed in gates.items() if not passed
                ),
            }
        )
    candidates = pd.DataFrame(rows).merge(summary, on="policy", how="left")
    passing = candidates.loc[candidates["passes"]].copy()
    if passing.empty:
        return {
            "decision": "FAIL_STAGED_ENTRY_FEASIBILITY_STOP_BEFORE_VALIDATION",
            "selected_policy": None,
            "candidate_rows": candidates,
        }
    selected = passing.sort_values(
        ["return_drawdown", "expectancy_r", "mean_tranche_count", "mean_allocated_r"],
        ascending=[False, False, True, True],
        kind="mergesort",
    ).iloc[0]
    return {
        "decision": "PASS_STAGED_ENTRY_FEASIBILITY_FREEZE_POLICY",
        "selected_policy": str(selected["policy"]),
        "candidate_rows": candidates,
    }


def write_staged_outputs(
    output_directory: Path,
    *,
    results: pd.DataFrame,
    population_counts: dict[str, int],
) -> dict[str, Any]:
    output_directory.mkdir(parents=True, exist_ok=True)
    summary = summarize_staged(results)
    decision = decide_staged(summary)
    results.to_csv(output_directory / "staged_trade_ledger.csv", index=False)
    summary.to_csv(output_directory / "staged_policy_summary.csv", index=False)
    decision["candidate_rows"].to_csv(
        output_directory / "staged_candidate_gate.csv", index=False
    )
    payload = {
        "programme": "ASIAN_SWEEP_STAGED_FEASIBILITY_V6_3",
        "decision": decision["decision"],
        "selected_policy": decision["selected_policy"],
        "development_years": [2015, 2016, 2017, 2018, 2019],
        "protected_years": [2020, 2021, 2022, 2023, 2024, 2025],
        "protected_validation_opened": False,
        **population_counts,
    }
    (output_directory / "staged_feasibility_decision.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload
