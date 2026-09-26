from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_vvsr_official_registration_mapping() -> None:
    reg = _load("data/reference/immunobiologic_registry.json")
    item = next(
        x for x in reg["immunobiologics"]
        if x["immunobiologic_id"] == "vvsr_materna"
    )
    assert item["pni_codes"] == ["108"]
    assert item["pni_registration"]["strategy_codes"] == ["1"]
    assert item["pni_registration"]["dose_codes"]["9"] == "Única"
    assert item["pni_registration"]["attendance_groups"]["001801"] == "Gestante"


def test_nirsevimab_official_registration_mapping() -> None:
    reg = _load("data/reference/immunobiologic_registry.json")
    item = next(
        x for x in reg["immunobiologics"]
        if x["immunobiologic_id"] == "nirsevimab"
    )
    assert set(item["pni_codes"]) == {"115", "116"}
    assert set(item["pni_registration"]["strategy_codes"]) == {"2", "8"}
    assert item["pni_registration"]["dose_codes"]["59"].startswith("Profilaxia")
    assert item["pni_registration"]["dose_codes"]["60"].startswith("Profilaxia")
    assert item["pni_registration"]["manufacturer_codes"]["44329"].startswith("PATHEON")
    assert item["pni_registration"]["attendance_groups"]["000120"] == "Prematuridade"


def test_respiratory_data_plan_does_not_treat_gestational_age_as_pni_guaranteed_field() -> None:
    plan = _load("data/reference/respiratory_data_plan.json")
    vvsr = next(x for x in plan["sources"] if x["source_id"] == "pni_vvsr_maternal")
    assert "gestational_age_weeks" in vvsr["desired_fields"]
    assert "gestational_age_weeks" not in vvsr["required_fields"]


def test_resp_indicators_block_unvalidated_coverage() -> None:
    cat = _load("data/reference/respiratory_indicators.json")
    by_id = {x["id"]: x for x in cat["indicators"]}
    assert by_id["nirsevimab_eligibility_coverage"]["decision_grade"] is False
    assert by_id["vvsr_opportunity_28w"]["decision_grade"] is False
    assert by_id["vvsr_doses_administered"]["decision_grade"] is True
