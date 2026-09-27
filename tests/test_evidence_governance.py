from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from evidence_governance import validate_evidence_registry


def test_current_evidence_registry_has_no_errors() -> None:
    findings = validate_evidence_registry()
    assert [x for x in findings if x["severity"] == "error"] == []


def test_supplementary_source_cannot_define_national_rule() -> None:
    payload = {
        "evidence": [
            {
                "evidence_id": "state_doc",
                "evidence_class": "supplementary_official",
                "authority_level": "state",
                "authority_scope": "ES",
                "official": True,
                "canonical": False,
                "can_define_national_rule": True,
                "official_url": "https://saude.es.gov.br/documento",
            }
        ]
    }
    findings = validate_evidence_registry(payload)
    assert any(
        x["code"] == "noncanonical_source_defines_national_rule"
        for x in findings
    )


def test_institutional_source_requires_access_policy() -> None:
    payload = {
        "evidence": [
            {
                "evidence_id": "dw",
                "evidence_class": "institutional_authorized",
                "authority_level": "institutional",
                "authority_scope": "SES-MT",
                "official": True,
                "canonical": False,
                "can_define_national_rule": False,
            }
        ]
    }
    findings = validate_evidence_registry(payload)
    assert any(
        x["code"] == "institutional_evidence_access_missing"
        for x in findings
    )
