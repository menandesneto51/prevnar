from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from vaccine_rules import geographic_scope_applies


def test_national_rule_applies_without_geographic_context() -> None:
    rule = {"geographic_scope": {"type": "national", "codes": ["BR"]}}
    assert geographic_scope_applies(rule, None) is True


def test_municipal_rule_never_applies_without_context() -> None:
    rule = {"geographic_scope": {"type": "municipality", "codes": ["5103403"]}}
    assert geographic_scope_applies(rule, None) is False


def test_municipal_rule_applies_only_to_matching_ibge_code() -> None:
    rule = {"geographic_scope": {"type": "municipality", "codes": ["5103403"]}}
    assert geographic_scope_applies(
        rule, {"municipality_code": "5103403"}
    ) is True
    assert geographic_scope_applies(
        rule, {"municipality_code": "5108402"}
    ) is False


def test_state_rule_supports_uf_context() -> None:
    rule = {"geographic_scope": {"type": "state", "codes": ["MT"]}}
    assert geographic_scope_applies(rule, {"uf": "MT"}) is True
    assert geographic_scope_applies(rule, {"uf": "GO"}) is False


def test_facility_rule_requires_matching_cnes() -> None:
    rule = {"geographic_scope": {"type": "facility", "codes": ["1234567"]}}
    assert geographic_scope_applies(rule, {"cnes": "1234567"}) is True
    assert geographic_scope_applies(rule, {"cnes": "7654321"}) is False


def test_polygon_rule_requires_resolved_polygon_id() -> None:
    rule = {"geographic_scope": {"type": "polygon", "codes": ["measles-ring-001"]}}
    assert geographic_scope_applies(
        rule, {"polygon_ids": ["measles-ring-001"]}
    ) is True
    assert geographic_scope_applies(
        rule, {"polygon_ids": ["other-ring"]}
    ) is False
