"""Independent Stoic Edge 1-2-3 research framework."""

from .backtest import simulate
from .config import (
    ES_PROXY_SPEC,
    GBPUSD_SPEC,
    NQ_PROXY_SPEC,
    NQ_SPEC,
    InstrumentSpec,
    SequenceConfig,
    load_config_family,
)
from .data import (
    data_audit,
    load_es_proxy,
    load_gbpusd,
    load_nq,
    load_nq_proxy,
    resample_ohlcv,
)
from .detector import DetectionResult, SequenceEvent, detect_sequences, validate_event_chronology
from .reporting import classify, date_block_bootstrap, summarize, validate_no_pooling
from .review import independent_trade_review

__all__ = [
    "DetectionResult",
    "ES_PROXY_SPEC",
    "GBPUSD_SPEC",
    "InstrumentSpec",
    "NQ_PROXY_SPEC",
    "NQ_SPEC",
    "SequenceConfig",
    "SequenceEvent",
    "classify",
    "data_audit",
    "date_block_bootstrap",
    "detect_sequences",
    "independent_trade_review",
    "load_config_family",
    "load_es_proxy",
    "load_gbpusd",
    "load_nq",
    "load_nq_proxy",
    "resample_ohlcv",
    "simulate",
    "summarize",
    "validate_event_chronology",
    "validate_no_pooling",
]
