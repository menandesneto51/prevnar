from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from release_guardian import Finding, check_privacy_manifest


def test_privacy_manifest_covers_every_registered_source() -> None:
    source = json.loads(
        (ROOT / "data/reference/source_registry.json").read_text(encoding="utf-8")
    )
    privacy = json.loads(
        (ROOT / "data/reference/privacy_manifest.json").read_text(encoding="utf-8")
    )
    source_ids = {x["source_id"] for x in source["sources"]}
    privacy_ids = {x["source_id"] for x in privacy["sources"]}
    assert privacy_ids == source_ids


def test_repo_linkage_is_disabled_for_all_sources() -> None:
    privacy = json.loads(
        (ROOT / "data/reference/privacy_manifest.json").read_text(encoding="utf-8")
    )
    assert all(x["linkage_allowed_in_repo"] is False for x in privacy["sources"])


def test_sensitive_public_marts_require_aggregation() -> None:
    privacy = json.loads(
        (ROOT / "data/reference/privacy_manifest.json").read_text(encoding="utf-8")
    )
    for row in privacy["sources"]:
        if row["data_classification"] in {"sensitive_health", "confidential"} and row["public_mart_allowed"]:
            assert "aggregate_only" in row["public_output_requirements"]


def test_privacy_manifest_passes_guardian_structure() -> None:
    findings: list[Finding] = []
    check_privacy_manifest(findings)
    errors = [f for f in findings if f.severity == "error"]
    assert errors == []
