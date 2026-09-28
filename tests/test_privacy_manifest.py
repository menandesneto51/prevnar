from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from privacy_governance import validate_privacy_manifest


def test_privacy_manifest_covers_every_registered_source() -> None:
    source = json.loads((ROOT / "data/reference/source_registry.json").read_text(encoding="utf-8"))
    privacy = json.loads((ROOT / "data/reference/privacy_manifest.json").read_text(encoding="utf-8"))
    assert {x["source_id"] for x in privacy["sources"]} == {x["source_id"] for x in source["sources"]}


def test_privacy_manifest_default_is_valid() -> None:
    errors = [x for x in validate_privacy_manifest() if x["severity"] == "error"]
    assert errors == []


def test_sensitive_sources_are_not_processed_in_public_static() -> None:
    privacy = json.loads((ROOT / "data/reference/privacy_manifest.json").read_text(encoding="utf-8"))
    for row in privacy["sources"]:
        if row["data_classification"] in {"confidential", "sensitive_health"}:
            assert "public_static" not in row["allowed_environments"]


def test_sensitive_public_marts_require_disclosure_controls() -> None:
    privacy = json.loads((ROOT / "data/reference/privacy_manifest.json").read_text(encoding="utf-8"))
    for row in privacy["sources"]:
        if row["public_mart_allowed"] and row["data_classification"] in {"confidential", "sensitive_health"}:
            req = set(row["public_output_requirements"])
            assert {"aggregate_only", "disclosure_risk_review"}.issubset(req)
