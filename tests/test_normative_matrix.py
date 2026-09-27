from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from build_normative_matrix import build_matrix


AS_OF = date(2026, 9, 26)


def _by_id(payload: dict) -> dict[str, dict]:
    return {
        row["immunobiologic_id"]: row
        for row in payload["immunobiologics"]
    }


def test_normative_matrix_has_no_unresolved_legal_references() -> None:
    payload = build_matrix(as_of=AS_OF)
    assert payload["summary"]["unresolved_legal_references"] == []


def test_vpc20_has_active_rules_and_resolved_official_acts() -> None:
    payload = build_matrix(as_of=AS_OF)
    item = _by_id(payload)["vpc20"]

    assert item["active_rule_count"] >= 2
    assert all(act["resolved"] for act in item["normative_acts"])
    assert any(act.get("official_url") for act in item["normative_acts"])


def test_influenza_remains_draft_in_matrix() -> None:
    payload = build_matrix(as_of=AS_OF)
    item = _by_id(payload)["influenza"]

    assert item["active_rule_count"] == 0
    assert item["draft_rule_count"] >= 1


def test_hpv_exposes_partial_data_mapping_separately_from_active_rule() -> None:
    payload = build_matrix(as_of=AS_OF)
    item = _by_id(payload)["hpv4"]

    assert item["active_rule_count"] >= 1
    assert item["onboarding_status"] == "partial_data_mapping"
    assert item["pni_codes"] == ["67"]


def test_all_rules_expose_geographic_scope_shape() -> None:
    payload = build_matrix(as_of=AS_OF)
    for item in payload["immunobiologics"]:
        for rule in item["rules"]:
            scope = rule["geographic_scope"]
            assert "type" in scope
            assert "codes" in scope
            assert isinstance(scope["codes"], list)


def test_active_rule_status_is_date_sensitive() -> None:
    before = build_matrix(as_of=date(2026, 1, 1))
    now = build_matrix(as_of=AS_OF)

    before_vvsr = _by_id(before)["vvsr_materna"]
    now_vvsr = _by_id(now)["vvsr_materna"]

    assert before_vvsr["active_rule_count"] == 0
    assert now_vvsr["active_rule_count"] >= 1
