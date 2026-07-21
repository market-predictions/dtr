# ruff: noqa: E402, I001

from . import engine as _engine
from .engine import StrategyConfig, load_zip, metrics
from .integrity import (
    IntegrityFunnel,
    build_session_table,
    prepare_market_arrays,
    resample_5m,
    run_backtest,
)

# Standard package and direct engine imports must resolve to the integrity-safe entry points.
# integrity.py captured the original implementations before these assignments. The patch must
# occur before optimize imports its engine references.
_engine.build_session_table = build_session_table
_engine.prepare_market_arrays = prepare_market_arrays
_engine.resample_5m = resample_5m
_engine.run_backtest = run_backtest

from .continuation import (
    ContinuationConfig,
    ContinuationFunnel,
    ContinuationSignal,
    ContinuationTrade,
    baseline_configs as continuation_baseline_configs,
    evaluate_continuation_baselines,
    generate_continuation_signals,
    run_continuation_backtest,
)
from .continuation_manifest import (
    ContinuationManifest,
    load_continuation_manifest,
    verify_continuation_dataset,
)
from .ifvg import (
    IFVGAnnotation,
    IFVGEvent,
    IFVGFunnel,
    IFVGVariant,
    PreparedIFVG,
    baseline_variants as ifvg_baseline_variants,
    compare_ifvg_portfolios,
    detect_ifvg_events,
    prepare_ifvg_context,
    run_ifvg_backtest,
    simulate_ifvg_variant,
)
from .ifvg_manifest import IFVGManifest, load_ifvg_manifest, verify_ifvg_dataset
from .manifest import (
    ResearchManifest,
    file_sha256,
    load_manifest,
    resolve_dataset_path,
    verify_dataset,
)
from .optimize import candidate_grid, evaluate_configs

__all__ = [
    "ContinuationConfig",
    "ContinuationFunnel",
    "ContinuationManifest",
    "ContinuationSignal",
    "ContinuationTrade",
    "IFVGAnnotation",
    "IFVGEvent",
    "IFVGFunnel",
    "IFVGManifest",
    "IFVGVariant",
    "IntegrityFunnel",
    "PreparedIFVG",
    "ResearchManifest",
    "StrategyConfig",
    "build_session_table",
    "candidate_grid",
    "compare_ifvg_portfolios",
    "continuation_baseline_configs",
    "detect_ifvg_events",
    "evaluate_configs",
    "evaluate_continuation_baselines",
    "file_sha256",
    "generate_continuation_signals",
    "ifvg_baseline_variants",
    "load_continuation_manifest",
    "load_ifvg_manifest",
    "load_manifest",
    "load_zip",
    "metrics",
    "prepare_ifvg_context",
    "prepare_market_arrays",
    "resample_5m",
    "resolve_dataset_path",
    "run_backtest",
    "run_continuation_backtest",
    "run_ifvg_backtest",
    "simulate_ifvg_variant",
    "verify_continuation_dataset",
    "verify_dataset",
    "verify_ifvg_dataset",
]
