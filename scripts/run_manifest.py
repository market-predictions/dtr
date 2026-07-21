from __future__ import annotations

import argparse
from pathlib import Path

from dtr_lab.research.artifacts import write_run_artifacts

from dtr_lab.research import (
    build_session_table,
    load_manifest,
    load_zip,
    resample_5m,
    run_backtest,
    verify_dataset,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a deterministic DTR research manifest"
    )
    parser.add_argument("manifest", help="Path to the YAML research manifest")
    parser.add_argument(
        "--out",
        default=None,
        help="Artifact directory; defaults to reports/<run_id>",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    manifest = load_manifest(manifest_path)
    dataset_path = verify_dataset(manifest, manifest_path)
    config = manifest.strategy_config()
    output = Path(args.out) if args.out else Path("reports") / manifest.run_id

    one_minute = load_zip(dataset_path)
    five_minute = resample_5m(one_minute)
    sessions = build_session_table(one_minute, five_minute)
    trades, funnel = run_backtest(
        one_minute,
        five_minute,
        sessions,
        config,
        gap_policy=manifest.execution.gap_policy,
    )

    summary = write_run_artifacts(
        output,
        manifest_path,
        dataset_path,
        manifest,
        config,
        trades,
        funnel,
    )
    print(
        f"run={summary['run_id']} trades={summary['metrics']['trades']} "
        f"net_r={summary['metrics']['net_r']:.6f} "
        f"max_dd_r={summary['metrics']['max_drawdown_r']:.6f} "
        f"status={summary['regression_status']} output={output}"
    )


if __name__ == "__main__":
    main()
