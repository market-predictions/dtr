from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from dtr_lab.strategies.quarters_theory.stage1 import (
    HORIZONS_MINUTES,
    audit_year,
    bootstrap_phase_effect,
    detect_events,
    load_year,
    stratified_phase_effect,
    summarize_events,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Quarters Theory Stage-1 distinctiveness study."
    )
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2021)
    parser.add_argument("--reset-pips", type=int, default=25)
    parser.add_argument("--bootstrap", type=int, default=5000)
    args = parser.parse_args()

    years = range(args.start_year, args.end_year + 1)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    audits: list[dict] = []
    annual_events: list[pd.DataFrame] = []

    for year in years:
        print(f"Auditing and processing {year}...", flush=True)
        audits.append(audit_year(args.data_dir, year))
        events = detect_events(load_year(args.data_dir, year), reset_pips=args.reset_pips)
        events.to_csv(
            args.output_dir / f"events_{year}.csv.gz",
            index=False,
            compression="gzip",
        )
        annual_events.append(events)
        print(f"  {len(events)} eligible crossing events", flush=True)

    events = pd.concat(annual_events, ignore_index=True)
    events.to_csv(
        args.output_dir / f"events_all_{args.start_year}_{args.end_year}.csv.gz",
        index=False,
        compression="gzip",
    )
    pd.DataFrame(audits).to_csv(args.output_dir / "data_audit.csv", index=False)
    (args.output_dir / "data_audit.json").write_text(
        json.dumps(audits, indent=2), encoding="utf-8"
    )
    summarize_events(events).to_csv(args.output_dir / "group_summary.csv", index=False)

    periods = {
        "development_2015_2019": range(2015, 2020),
        "internal_validation_2020_2021": range(2020, 2022),
        f"all_{args.start_year}_{args.end_year}": years,
    }
    phase_rows: list[dict] = []
    bootstrap_rows: list[dict] = []
    for period, period_years in periods.items():
        valid_years = [year for year in period_years if year in years]
        if not valid_years:
            continue
        for horizon in HORIZONS_MINUTES:
            outcome = f"return_{horizon}m_pips"
            for phase in (0, 50, 100, 150, 200):
                row = stratified_phase_effect(events, outcome, phase, valid_years)
                row.update(period=period, reset_pips=args.reset_pips)
                phase_rows.append(row)
            if horizon == 60:
                row = bootstrap_phase_effect(
                    events,
                    outcome,
                    phase=0,
                    years=valid_years,
                    n_boot=args.bootstrap,
                )
                row.update(period=period, reset_pips=args.reset_pips)
                bootstrap_rows.append(row)

    phase_frame = pd.DataFrame(phase_rows)
    phase_frame.to_csv(args.output_dir / "phase_effects.csv", index=False)
    bootstrap_frame = pd.DataFrame(bootstrap_rows)
    bootstrap_frame.to_csv(args.output_dir / "canonical_60m_bootstrap.csv", index=False)

    rank_rows: list[dict] = []
    for (period, outcome), group in phase_frame.groupby(["period", "outcome"]):
        canonical = float(group.loc[group.phase == 0, "effect"].iloc[0])
        effects = group.effect.to_numpy(dtype=float)
        rank_rows.append(
            {
                "period": period,
                "outcome": outcome,
                "canonical_effect_pips": canonical,
                "canonical_rank_desc": int(1 + np.sum(effects > canonical)),
                "canonical_percentile": float(np.mean(effects <= canonical)),
                "best_phase": int(group.loc[group.effect.idxmax(), "phase"]),
                "best_effect_pips": float(group.effect.max()),
                "worst_phase": int(group.loc[group.effect.idxmin(), "phase"]),
                "worst_effect_pips": float(group.effect.min()),
            }
        )
    pd.DataFrame(rank_rows).to_csv(
        args.output_dir / "canonical_phase_rank.csv", index=False
    )

    key = {
        "configuration": {
            "pair": "GBPUSD",
            "years": [args.start_year, args.end_year],
            "reset_pips": args.reset_pips,
            "crossing": "mid-close crossing",
            "primary_horizon_minutes": 60,
            "primary_treated_phase_pips": 0,
            "control_phases_pips": [50, 100, 150, 200],
        },
        "events": int(len(events)),
        "lqp_events": int(events.is_lqp.sum()),
        "non_lqp_round_events": int((~events.is_lqp).sum()),
        "canonical_60m_bootstrap": bootstrap_frame.to_dict("records"),
    }
    (args.output_dir / "key_results.json").write_text(
        json.dumps(key, indent=2), encoding="utf-8"
    )
    print(json.dumps(key, indent=2), flush=True)


if __name__ == "__main__":
    main()
