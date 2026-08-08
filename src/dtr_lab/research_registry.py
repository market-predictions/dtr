"""Validation and rendering helpers for the Dukascopy FX Cash research registry."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DATASET_NAME = "Dukascopy FX Cash"
DATASET_ID = "dukascopy_fx_cash_m1_bid_ask_v1"
CANONICAL_PAIRS = frozenset(
    {
        "EURUSD",
        "GBPUSD",
        "USDCHF",
        "AUDUSD",
        "NZDUSD",
        "USDCAD",
        "USDJPY",
        "EURJPY",
        "GBPJPY",
        "EURGBP",
    }
)
STUDY_ID_RE = re.compile(r"^DFXC-\d{8}-\d{3}-[a-z0-9-]+$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
LIFECYCLE = {
    "DESIGN",
    "PREREGISTERED",
    "RUN_COMPLETE",
    "INTERNAL_ASSURANCE_PASS",
    "HOLDOUT_CONFIRMED",
    "REJECTED",
    "SUPERSEDED",
    "ABANDONED",
}
PRE_RESULT_LIFECYCLE = {"DESIGN", "PREREGISTERED"}
DISPOSITIONS = {
    "SUPPORTED_INTERNAL",
    "PROMOTE_TO_HOLDOUT_CONFIRMATION",
    "REJECT_NO_INCREMENTAL_VALUE",
    "REJECT_MECHANISM",
    "DESCRIPTIVE_ONLY",
    "HOLD_FOR_FRESH_DATA",
    "INDETERMINATE",
    "INVALIDATED_DATA",
    "SUPERSEDED",
    "ABANDONED",
}
HOLDOUT_STATES = {
    "UNOPENED",
    "PARTIALLY_OPENED",
    "OPENED",
    "NOT_APPLICABLE",
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_study(study: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    sid = study.get("study_id", "<missing-study-id>")
    if not STUDY_ID_RE.fullmatch(str(sid)):
        errors.append(f"{sid}: invalid study_id")
    if study.get("schema_version") != "1.0.0":
        errors.append(f"{sid}: unsupported schema_version")
    if study.get("lifecycle_status") not in LIFECYCLE:
        errors.append(f"{sid}: invalid lifecycle_status")

    dataset = study.get("dataset", {})
    if dataset.get("canonical_name") != DATASET_NAME:
        errors.append(f"{sid}: canonical dataset name must be {DATASET_NAME!r}")
    if dataset.get("dataset_id") != DATASET_ID:
        errors.append(f"{sid}: dataset_id must be {DATASET_ID!r}")
    pairs = dataset.get("pairs", [])
    if not pairs or not set(pairs).issubset(CANONICAL_PAIRS):
        errors.append(f"{sid}: pairs must be a non-empty subset of the canonical ten pairs")
    if len(pairs) != len(set(pairs)):
        errors.append(f"{sid}: duplicate pairs are not allowed")
    if dataset.get("base_timeframe") != "M1":
        errors.append(f"{sid}: Dukascopy FX Cash base_timeframe must be M1")
    if set(dataset.get("quote_sides", [])) != {"BID", "ASK"}:
        errors.append(f"{sid}: quote_sides must explicitly contain BID and ASK")
    if dataset.get("timezone") != "UTC":
        errors.append(f"{sid}: source timezone must be UTC")
    if not dataset.get("price_basis"):
        errors.append(f"{sid}: price_basis is required")
    windows = dataset.get("windows", {})
    for name in ("development", "internal_validation", "protected_holdout"):
        if name not in windows:
            errors.append(f"{sid}: missing dataset window {name}")

    source = study.get("source", {})
    if source.get("repository") != "market-predictions/dtr":
        errors.append(f"{sid}: source repository must be market-predictions/dtr")
    if not source.get("ref"):
        errors.append(f"{sid}: source ref is required")
    if not SHA_RE.fullmatch(str(source.get("commit_sha", ""))):
        errors.append(f"{sid}: source commit_sha must be an exact 40-character SHA")
    if not source.get("paths"):
        errors.append(f"{sid}: source paths are required")

    holdout = study.get("holdout", {})
    if holdout.get("state") not in HOLDOUT_STATES:
        errors.append(f"{sid}: invalid holdout state")
    opened = bool(holdout.get("opened_in_this_study"))
    if opened and not holdout.get("authorization_record"):
        errors.append(f"{sid}: opened holdout requires authorization_record")
    if holdout.get("protected_window") != windows.get("protected_holdout"):
        errors.append(f"{sid}: holdout protected_window must match dataset protected_holdout")

    hypotheses = study.get("hypotheses", {})
    if not hypotheses.get("market_question"):
        errors.append(f"{sid}: market_question is required")
    if not hypotheses.get("null"):
        errors.append(f"{sid}: null hypothesis is required")
    if not hypotheses.get("alternative"):
        errors.append(f"{sid}: alternative hypothesis is required")

    method = study.get("method", {})
    if not method.get("primary_endpoint"):
        errors.append(f"{sid}: primary_endpoint is required")
    if not method.get("controls"):
        message = f"{sid}: baseline/control or explicit no-control rationale is required"
        errors.append(message)
    if not isinstance(study.get("tags"), list) or not study.get("tags"):
        errors.append(f"{sid}: at least one search tag is required")
    return errors


def validate_result(result: dict[str, Any], study: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    sid = study["study_id"]
    if result.get("study_id") != sid:
        errors.append(f"{sid}: result study_id mismatch")
    if result.get("schema_version") != "1.0.0":
        errors.append(f"{sid}: result schema_version mismatch")
    if result.get("scientific_disposition") not in DISPOSITIONS:
        errors.append(f"{sid}: invalid scientific_disposition")
    if not result.get("decision"):
        errors.append(f"{sid}: exact decision string is required")
    if not result.get("summary"):
        errors.append(f"{sid}: result summary is required")
    if not result.get("primary_findings"):
        errors.append(f"{sid}: primary_findings cannot be empty")
    if not result.get("evidence"):
        errors.append(f"{sid}: result evidence cannot be empty")

    holdout = result.get("holdout", {})
    if holdout.get("state_after") not in HOLDOUT_STATES:
        errors.append(f"{sid}: invalid result holdout state")
    result_opened = bool(holdout.get("opened_in_this_study"))
    study_opened = bool(study.get("holdout", {}).get("opened_in_this_study"))
    if result_opened != study_opened:
        errors.append(f"{sid}: result/study holdout-open state mismatch")

    for evidence in result.get("evidence", []):
        if evidence.get("repository") != "market-predictions/dtr":
            errors.append(f"{sid}: evidence repository mismatch")
        if not SHA_RE.fullmatch(str(evidence.get("commit_sha", ""))):
            errors.append(f"{sid}: evidence commit must be exact SHA")
        if not evidence.get("ref"):
            errors.append(f"{sid}: evidence ref missing")
        if not evidence.get("path"):
            errors.append(f"{sid}: evidence path missing")
    return errors


def render_registry_markdown(index: dict[str, Any]) -> str:
    studies = sorted(
        index["studies"],
        key=lambda entry: (entry["date"], entry["study_id"]),
    )
    lines = [
        "# Dukascopy FX Cash — Research Index",
        "",
        "Canonical machine source: `research_registry/dukascopy_fx_cash/index.json`.",
        "",
        f"Registered studies: **{len(studies)}**.",
        "",
        (
            "| Study ID | Date | Family | Question / title | Disposition | "
            "Holdout | Assurance | Source |"
        ),
        "|---|---|---|---|---|---|---|---|",
    ]
    for entry in studies:
        source = f"`{entry['source_ref']}` @ `{entry['source_commit'][:8]}`"
        disposition = entry.get("scientific_disposition") or "PENDING"
        row = (
            f"| `{entry['study_id']}` | {entry['date']} | {entry['family']} | "
            f"{entry['title']} | `{disposition}` | `{entry['holdout_state']}` | "
            f"`{entry['assurance_status']}` | {source} |"
        )
        lines.append(row)
    lines.extend(
        [
            "",
            "## Reading rule",
            "",
            (
                "The row is a locator, not the evidence. Open the study's `study.json` and "
                "`result.json` when present, then follow the frozen source commit and "
                "artifact paths for the complete preregistration, run outputs, report, "
                "code and review evidence."
            ),
            "",
            "## Current recovered conclusions",
            "",
            (
                "- **Quarters Theory:** the canonical 250-pip continuation mechanism was "
                "demoted on GBPUSD and then failed unchanged across the ten-pair universe "
                "(`0/10` positive-and-stable pairs)."
            ),
            (
                "- **Classic pivots — broad mechanism:** high absolute reach rates do not "
                "establish magnetism; exact pivot coordinates did not beat nearby "
                "deterministic placebos on the preregistered target/stall/reversal "
                "mechanisms."
            ),
            (
                "- **Classic pivots — spatial follow-up:** broad magnet/stall/reversal "
                "claims remained rejected, but a narrower daily/weekly pivot-proximity "
                "terminal-hazard effect survived internal falsification and is eligible "
                "only for one unchanged protected-holdout confirmation."
            ),
            "",
            "## Search tags",
            "",
            (
                "Use repository search against `index.json`, `INDEX.md` or per-study "
                "`tags` for concepts such as `pivots`, `zones`, `quarters-theory`, "
                "`placebo`, `terminal-hazard`, `reversal`, `round-numbers`, or pair "
                "symbols."
            ),
            "",
            "## Historical migration",
            "",
            (
                "The registry starts with the recently recovered Quarters and pivot "
                "research because these studies exposed the memory failure this framework "
                "fixes. Other historical Dukascopy FX Cash branches are listed in "
                "`migration_candidates.json` and must be reconstructed without altering "
                "their historical decisions."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def validate_registry(repo_root: Path | None = None) -> list[str]:
    repo_root = repo_root or Path.cwd()
    root = repo_root / "research_registry" / "dukascopy_fx_cash"
    index = _load(root / "index.json")
    errors: list[str] = []

    if index.get("schema_version") != "1.0.0":
        errors.append("index: unsupported schema_version")
    dataset = index.get("dataset", {})
    identity_ok = (
        dataset.get("canonical_name") == DATASET_NAME
        and dataset.get("dataset_id") == DATASET_ID
    )
    if not identity_ok:
        errors.append("index: canonical dataset identity mismatch")
    if dataset.get("pair_count") != len(CANONICAL_PAIRS):
        errors.append("index: pair_count must equal canonical ten-pair universe")

    entries = index.get("studies", [])
    expected_order = sorted(
        entries,
        key=lambda entry: (entry.get("date", ""), entry.get("study_id", "")),
    )
    if entries != expected_order:
        errors.append("index: studies must be sorted by date then study_id")

    seen: set[str] = set()
    known_ids = {entry.get("study_id") for entry in entries}
    for entry in entries:
        sid = entry.get("study_id")
        if sid in seen:
            errors.append(f"index: duplicate study_id {sid}")
            continue
        seen.add(sid)
        if not STUDY_ID_RE.fullmatch(str(sid)):
            errors.append(f"index: invalid study_id {sid}")
            continue

        study_path_value = entry.get("study_path")
        if not study_path_value:
            errors.append(f"{sid}: missing study_path")
            continue
        study_path = repo_root / study_path_value
        if not study_path.exists():
            errors.append(f"{sid}: missing study file {study_path_value}")
            continue
        study = _load(study_path)
        errors.extend(validate_study(study))
        if study.get("study_id") != sid:
            errors.append(f"{sid}: index/study ID mismatch")
        if study.get("lifecycle_status") != entry.get("lifecycle_status"):
            errors.append(f"{sid}: lifecycle differs between index and study")
        if entry.get("pairs") != study.get("dataset", {}).get("pairs"):
            errors.append(f"{sid}: index pair universe differs from study")
        source = study.get("source", {})
        if entry.get("source_ref") != source.get("ref"):
            errors.append(f"{sid}: index source_ref differs from study")
        if entry.get("source_commit") != source.get("commit_sha"):
            errors.append(f"{sid}: index source_commit differs from study")

        result_path_value = entry.get("result_path")
        lifecycle = study.get("lifecycle_status")
        if not result_path_value:
            if lifecycle not in PRE_RESULT_LIFECYCLE:
                errors.append(f"{sid}: completed/running study requires result_path")
        else:
            result_path = repo_root / result_path_value
            if not result_path.exists():
                errors.append(f"{sid}: missing result file {result_path_value}")
            else:
                result = _load(result_path)
                errors.extend(validate_result(result, study))
                if result.get("scientific_disposition") != entry.get(
                    "scientific_disposition"
                ):
                    errors.append(f"{sid}: disposition differs between index and result")
                if result.get("decision") != entry.get("decision"):
                    errors.append(f"{sid}: decision differs between index and result")
                if result.get("holdout", {}).get("state_after") != entry.get(
                    "holdout_state"
                ):
                    errors.append(f"{sid}: holdout state differs between index and result")
                if result.get("assurance", {}).get("status") != entry.get(
                    "assurance_status"
                ):
                    errors.append(f"{sid}: assurance status differs between index and result")

        for related in study.get("related_studies", []):
            if related not in known_ids:
                errors.append(f"{sid}: related study {related} is not registered")

    study_root = root / "studies"
    directory_ids = {path.name for path in study_root.iterdir() if path.is_dir()}
    if directory_ids != known_ids:
        missing_from_index = sorted(directory_ids - known_ids)
        missing_from_disk = sorted(known_ids - directory_ids)
        if missing_from_index:
            joined = ", ".join(missing_from_index)
            errors.append(f"index: unregistered study directories: {joined}")
        if missing_from_disk:
            joined = ", ".join(missing_from_disk)
            errors.append(f"index: indexed study directories missing: {joined}")

    rendered = render_registry_markdown(index)
    current = (root / "INDEX.md").read_text(encoding="utf-8")
    if rendered != current:
        errors.append("INDEX.md is out of sync with index.json")
    return errors
