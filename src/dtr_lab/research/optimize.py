from __future__ import annotations

from dataclasses import asdict, replace
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

from .engine import StrategyConfig, metrics
from .integrity import GapPolicy, prepare_market_arrays, run_backtest


def candidate_grid(base: StrategyConfig, pack: str) -> list[StrategyConfig]:
    configs: list[StrategyConfig] = []
    if pack == "bos":
        values = product(
            [1, 2],
            ["wick", "close", "close_buffer"],
            [0.60, 0.90],
            [False, True],
            [1, 2],
            ["break_close", "retest"],
        )
        for (
            pivot_len,
            break_mode,
            impulse_mult,
            require_impulse,
            accept,
            entry_mode,
        ) in values:
            # close_buffer is meaningful only with a nonzero buffer.
            buf = 0.02 if break_mode == "close_buffer" else 0.0
            name = f"BOS_p{pivot_len}_{break_mode}_im{impulse_mult:.2f}_{'req' if require_impulse else 'score'}_a{accept}_{entry_mode}"
            configs.append(
                replace(
                    base,
                    name=name,
                    pivot_len=pivot_len,
                    break_mode=break_mode,
                    break_buffer_pct=buf,
                    impulse_mult=impulse_mult,
                    require_impulse=require_impulse,
                    acceptance_bars=accept,
                    entry_mode=entry_mode,
                )
            )
    elif pack == "sweep":
        values = product(
            [0.00, 0.01, 0.02, 0.04, 0.06],
            [0, 1, 2, 3],
            [0.40, 0.60, 0.80],
            [0.8, 1.0],
        )
        for pct, threshold, ideal, expand in values:
            name = f"SW_pct{pct:.2f}_q{threshold}_ideal{ideal:.2f}_exp{expand:.1f}"
            configs.append(
                replace(
                    base,
                    name=name,
                    min_sweep_range_pct=pct,
                    valid_sweep_threshold=threshold,
                    ideal_sweep_max_pct=ideal,
                    volume_expand_mult=expand,
                    atr_expand_mult=expand,
                )
            )
    elif pack == "regime":
        session_sets = [
            ("LONDON_2AM", "NEW_YORK_9AM", "ASIA_7PM"),
            ("LONDON_2AM", "NEW_YORK_9AM"),
            ("LONDON_2AM",),
            ("NEW_YORK_9AM",),
            ("ASIA_7PM",),
        ]
        weekday_sets = [
            (0, 1, 2, 3, 4),
            (0, 1, 2, 3),
            (1, 2, 3),
            (1, 2, 3, 4),
            (0, 1, 2, 3, 4, 5, 6),
        ]
        trends = [
            ("none", 0.35, 22.0),
            ("nontrend_er", 0.25, 22.0),
            ("nontrend_er", 0.35, 22.0),
            ("nontrend_er", 0.45, 22.0),
            ("adx_nontrend", 0.35, 18.0),
            ("adx_nontrend", 0.35, 22.0),
            ("adx_nontrend", 0.35, 28.0),
            ("vwap_reclaim", 0.35, 22.0),
        ]
        for sess, wd, (trend, er, adx) in product(session_sets, weekday_sets, trends):
            name = f"REG_{'+'.join(x.split('_')[0] for x in sess)}_wd{''.join(map(str, wd))}_{trend}_er{er:.2f}_adx{adx:.0f}"
            configs.append(
                replace(
                    base,
                    name=name,
                    sessions=sess,
                    weekdays=wd,
                    trend_filter=trend,
                    er_max=er,
                    adx_max=adx,
                )
            )
    elif pack == "timing":
        values = product(
            [5, 10, 15, 20],
            [30, 40, 60, 90],
            [0.01, 0.02, 0.04, 0.06],
            [1, 2, 3],
        )
        for reaction, max_bars, pivot_pct, accept in values:
            name = f"TIME_react{reaction}_max{max_bars}_piv{pivot_pct:.2f}_a{accept}"
            configs.append(
                replace(
                    base,
                    name=name,
                    reaction_bars=reaction,
                    max_bars_from_sweep=max_bars,
                    pivot_min_pct=pivot_pct,
                    acceptance_bars=accept,
                )
            )
    elif pack == "risk":
        values = product(
            [0.00, 0.05, 0.10, 0.20, 0.30],
            [1, 2, 4, 8],
            [0.5, 1.0, 2.0, 4.0],
        )
        for atr_frac, ticks, slip in values:
            name = f"RISK_atr{atr_frac:.2f}_ticks{ticks}_slip{slip:.1f}"
            configs.append(
                replace(
                    base,
                    name=name,
                    stop_atr_frac=atr_frac,
                    stop_buffer_ticks=ticks,
                    slippage_ticks_each_side=slip,
                )
            )
    elif pack == "exit":
        values = product(
            [1.0, 1.25, 1.5],
            [2.0, 2.5, 3.0, 4.0],
            [0.50],
            [True, False],
            [("everyday", 16, 0), ("everyday", 23, 45), ("none", 16, 0)],
            [96, 192, 288],
        )
        for tp1, tp2, frac, be, tc, hold in values:
            if tp2 <= tp1:
                continue
            mode, hour, minute = tc
            name = f"EXIT_t1{tp1:.2f}_t2{tp2:.2f}_f{frac:.2f}_be{int(be)}_{mode}{hour:02d}{minute:02d}_h{hold}"
            configs.append(
                replace(
                    base,
                    name=name,
                    tp1_rr=tp1,
                    runner_rr=tp2,
                    tp1_fraction=frac,
                    move_runner_to_be=be,
                    time_close_mode=mode,
                    time_close_hour=hour,
                    time_close_minute=minute,
                    max_hold_bars=hold,
                )
            )
    else:
        raise ValueError(pack)
    return configs


def robust_score(row: pd.Series) -> float:
    # Deliberately rewards OOS expectancy and drawdown efficiency while penalizing tiny samples.
    trades = max(float(row.get("val_trades", 0)), 0.0)
    sample = min(1.0, np.sqrt(trades / 80.0))
    exp = float(row.get("val_expectancy_r", -9.0))
    dd = max(float(row.get("val_max_drawdown_r", 99.0)), 0.5)
    pf = min(float(row.get("val_profit_factor", 0.0)), 3.0)
    train_exp = float(row.get("train_expectancy_r", -9.0))
    stability = max(0.0, 1.0 - abs(train_exp - exp) / max(0.15, abs(train_exp) + 0.05))
    return (
        sample
        * (exp * 5.0 + pf * 0.25 + float(row.get("val_net_r", -99.0)) / dd * 0.15)
        * (0.5 + 0.5 * stability)
    )


def evaluate_configs(
    one: pd.DataFrame,
    bars: pd.DataFrame,
    sessions: pd.DataFrame,
    configs: list[StrategyConfig],
    train_end: pd.Timestamp,
    validation_end: pd.Timestamp,
    progress_every: int = 25,
    *,
    gap_policy: GapPolicy = "liquidate_unsafe",
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    market_arrays = prepare_market_arrays(one)
    for n, cfg in enumerate(configs, 1):
        trades, funnel = run_backtest(
            one,
            bars,
            sessions,
            cfg,
            market_arrays=market_arrays,
            gap_policy=gap_policy,
        )
        train = trades[trades["entry_time"] < train_end] if not trades.empty else trades
        val = (
            trades[
                (trades["entry_time"] >= train_end)
                & (trades["entry_time"] < validation_end)
            ]
            if not trades.empty
            else trades
        )
        row: dict[str, object] = {
            "name": cfg.name,
            **asdict(cfg),
            "gap_policy": gap_policy,
            **{f"funnel_{k}": v for k, v in funnel.as_dict().items()},
        }
        row.update({f"train_{k}": v for k, v in metrics(train).items()})
        row.update({f"val_{k}": v for k, v in metrics(val).items()})
        rows.append(row)
        if progress_every and n % progress_every == 0:
            print(f"evaluated {n}/{len(configs)}")
    result = pd.DataFrame(rows)
    result["robust_score"] = result.apply(robust_score, axis=1)
    return result.sort_values("robust_score", ascending=False).reset_index(drop=True)


def save_leaderboard(frame: pd.DataFrame, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
