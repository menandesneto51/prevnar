from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_all_rules_have_context_and_geographic_scope() -> None:
    payload = _load("data/reference/normative_rules.json")
    allowed_contexts = set(payload["allowed_rule_contexts"])
    allowed_scope_types = set(payload["allowed_geographic_scope_types"])

    for rule in payload["rules"]:
        assert rule["rule_context"] in allowed_contexts
        scope = rule["geographic_scope"]
        assert scope["type"] in allowed_scope_types
        if scope["type"] == "national":
            assert scope["codes"] == ["BR"]
        else:
            assert scope["codes"]


def test_menacwy_partial_mapping_is_officially_scoped() -> None:
    payload = _load("data/reference/immunobiologic_registry.json")
    item = next(x for x in payload["immunobiologics"] if x["immunobiologic_id"] == "menacwy")
    assert item["pni_codes"] == ["74"]
    assert item["onboarding_status"] == "partial_data_mapping"
    booster = item["pni_registration"]["known_routine_booster"]
    assert booster["strategy_code"] == "1"
    assert booster["dose_code"] == "38"


def test_yellow_fever_partial_mapping_uses_national_registration_code() -> None:
    payload = _load("data/reference/immunobiologic_registry.json")
    item = next(x for x in payload["immunobiologics"] if x["immunobiologic_id"] == "febre_amarela")
    assert item["pni_codes"] == ["14"]
    assert set(item["pni_registration"]["known_coverage_dose_codes"]) == {"1", "9", "36"}


def test_hpv_code_remains_unset_until_confirmed_in_national_registration_system() -> None:
    payload = _load("data/reference/immunobiologic_registry.json")
    item = next(x for x in payload["immunobiologics"] if x["immunobiologic_id"] == "hpv4")
    assert item["pni_codes"] == []
    assert item["code_mapping_status"] == "pending_official_pni_code_confirmation"
