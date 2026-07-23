from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from stoic_123_lab import (
    ES_PROXY_SPEC,
    GBPUSD_SPEC,
    NQ_PROXY_SPEC,
    NQ_SPEC,
    classify,
    data_audit,
    date_block_bootstrap,
    detect_sequences,
    independent_trade_review,
    load_config_family,
    load_es_proxy,
    load_gbpusd,
    load_nq,
    load_nq_proxy,
    resample_ohlcv,
    simulate,
    summarize,
    validate_event_chronology,
    validate_no_pooling,
)
from stoic_123_lab.config import InstrumentSpec, SequenceConfig
from stoic_123_lab.data import file_sha256


def run_arm(
    *,
    one_minute: pd.DataFrame,
    bars_by_minutes: dict[int, pd.DataFrame],
    spec: InstrumentSpec,
    config: SequenceConfig,
    out: Path,
    iterations: int,
    seed: int,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    execution_bars = bars_by_minutes[config.execution_minutes]
    management_bars = bars_by_minutes[config.management_minutes]
    map_bars = bars_by_minutes[config.map_minutes]

    entries = detect_sequences(execution_bars, map_bars, config)
    management = detect_sequences(management_bars, map_bars, config.management_config())
    validate_event_chronology(entries.events)
    validate_event_chronology(management.events)

    trades = simulate(one_minute, entries.events, management.events, spec, config)
    summary = summarize(trades, instrument=spec.name, arm_id=config.arm_id)
    inference = date_block_bootstrap(trades, iterations=iterations, seed=seed)
    summary["classification"] = classify(summary, inference)
    summary["entry_step1"] = entries.funnel["step1"]
    summary["entry_retests"] = entries.funnel["retests"]
    summary["entry_bases_locked"] = entries.funnel["bases_locked"]
    summary["entry_step3"] = entries.funnel["step3"]
    summary["management_step3"] = management.funnel["step3"]

    prefix = f"{spec.name}__{config.arm_id}"
    entries.events.to_csv(out / f"{prefix}__events.csv", index=False)
    management.events.to_csv(out / f"{prefix}__management_events.csv", index=False)
    trades.to_csv(out / f"{prefix}__trades.csv", index=False)
    (out / f"{prefix}__funnel.json").write_text(
        json.dumps(
            {"entry": entries.funnel, "management": management.funnel},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    review = independent_trade_review(
        trades, summary, instrument=spec.name, arm_id=config.arm_id
    )
    return summary, {"instrument": spec.name, "arm_id": config.arm_id, **inference}, review


def _sources_from_args(args: argparse.Namespace) -> list[tuple[InstrumentSpec, Path, pd.DataFrame]]:
    sources: list[tuple[InstrumentSpec, Path, pd.DataFrame]] = []
    if args.nq is not None:
        sources.append((NQ_SPEC, args.nq.resolve(), load_nq(args.nq)))
    if args.nq_proxy is not None:
        sources.append((NQ_PROXY_SPEC, args.nq_proxy.resolve(), load_nq_proxy(args.nq_proxy)))
    if args.es_proxy is not None:
        sources.append((ES_PROXY_SPEC, args.es_proxy.resolve(), load_es_proxy(args.es_proxy)))
    if args.gbpusd is not None:
        sources.append((GBPUSD_SPEC, args.gbpusd.resolve(), load_gbpusd(args.gbpusd)))
    if not sources:
        raise ValueError("Provide at least one of --nq, --nq-proxy, --es-proxy, or --gbpusd")
    names = [spec.name for spec, _, _ in sources]
    if len(names) != len(set(names)):
        raise ValueError("Each instrument may be supplied only once")
    return sources


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run the independent Stoic Edge 1-2-3 sequence study on one or more "
            "explicitly labelled instrument streams"
        )
    )
    parser.add_argument("--nq", type=Path)
    parser.add_argument("--nq-proxy", type=Path)
    parser.add_argument("--es-proxy", type=Path)
    parser.add_argument("--gbpusd", type=Path)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=10_000)
    args = parser.parse_args()
    if args.iterations < 1:
        raise ValueError("iterations must be positive")
    args.out.mkdir(parents=True, exist_ok=True)

    configs = load_config_family(args.config)
    sources = _sources_from_args(args)
    summary_rows: list[dict[str, object]] = []
    inference_rows: list[dict[str, object]] = []
    audits: list[dict[str, object]] = []
    review_rows: list[dict[str, object]] = []

    required_minutes = sorted(
        {
            minutes
            for config in configs
            for minutes in (
                config.execution_minutes,
                config.management_minutes,
                config.map_minutes,
            )
        }
    )

    for instrument_index, (spec, path, one_minute) in enumerate(sources):
        audits.append(
            {
                **data_audit(one_minute, spec),
                "path": str(path),
                "sha256": file_sha256(path),
            }
        )
        bars_by_minutes = {
            minutes: resample_ohlcv(one_minute, minutes) for minutes in required_minutes
        }
        for arm_index, config in enumerate(configs):
            summary, inference, review = run_arm(
                one_minute=one_minute,
                bars_by_minutes=bars_by_minutes,
                spec=spec,
                config=config,
                out=args.out,
                iterations=args.iterations,
                seed=20260723 + instrument_index * 100 + arm_index,
            )
            summary_rows.append(summary)
            inference_rows.append(inference)
            review_rows.append(review)

    summary_frame = pd.DataFrame(summary_rows)
    validate_no_pooling(summary_frame)
    summary_frame.to_csv(args.out / "summary.csv", index=False)
    pd.DataFrame(inference_rows).to_csv(args.out / "inference.csv", index=False)
    pd.DataFrame(audits).to_csv(args.out / "data_audit.csv", index=False)
    review_frame = pd.DataFrame(review_rows)
    review_frame.to_csv(args.out / "independent_review.csv", index=False)
    if not bool((review_frame["status"] == "PASS").all()):
        raise RuntimeError("Independent trade-ledger review failed")

    instruments = [spec.name for spec, _, _ in sources]
    decision = {
        "study_id": "STOIC123-WP-20260723-01",
        "strategy_family": "Stoic Edge 1-2-3 Sequence",
        "scientific_status": "RESEARCH_ONLY",
        "candidate_family_size": len(configs),
        "instruments": instruments,
        "proxy_labels_are_not_cme_futures": any(name.endswith("PROXY") for name in instruments),
        "gbpusd_uses_midpoint_signals_and_side_correct_bid_ask_execution": (
            "GBPUSD" in instruments
        ),
        "pooling_prohibited": True,
        "selection_rule": (
            "No arm may be promoted from full-sample profitability alone; require chronological "
            "stability, cost robustness, date-block uncertainty, and cross-instrument relevance."
        ),
        "restrictions": [
            "no tuning on pooled instrument returns",
            "no relabelling index proxies as CME futures",
            "no live deployment or Pine port from this run",
            "no boundary changes after Step 2 locks",
            "no broker-neutral GBPUSD claim from one Dukascopy quote stream",
        ],
    }
    (args.out / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "study_id": decision["study_id"],
        "config_path": str(args.config.resolve()),
        "config_sha256": file_sha256(args.config),
        "arms": [asdict(config) for config in configs],
        "sources": [
            {
                "instrument": spec.name,
                "path": str(path),
                "sha256": file_sha256(path),
                "classification": spec.source_classification,
                "execution_model": spec.execution_model,
            }
            for spec, path, _ in sources
        ],
    }
    (args.out / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(summary_frame.to_string(index=False))
    print(json.dumps(decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
