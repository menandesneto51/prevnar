from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_routine_rescue_data_plan_has_four_sources() -> None:
    plan = _load("data/reference/routine_rescue_data_plan.json")
    ids = {x["source_id"] for x in plan["sources"]}
    assert ids == {
        "pni_hpv4",
        "pni_menacwy",
        "pni_febre_amarela",
        "pni_triplice_viral",
    }


def test_hpv_mapping_is_partial_not_falsely_complete() -> None:
    plan = _load("data/reference/routine_rescue_data_plan.json")
    hpv = next(x for x in plan["sources"] if x["source_id"] == "pni_hpv4")
    assert hpv["immunobiologic_codes"] == ["67"]
    assert hpv["mapping_status"] == "partial"
    assert hpv["confirmed"]["strategy_codes"] is False
    assert hpv["confirmed"]["dose_codes"] is False


def test_menacwy_and_yellow_fever_codes_match_registry() -> None:
    plan = _load("data/reference/routine_rescue_data_plan.json")
    by_id = {x["source_id"]: x for x in plan["sources"]}
    assert by_id["pni_menacwy"]["immunobiologic_codes"] == ["74"]
    assert by_id["pni_febre_amarela"]["immunobiologic_codes"] == ["14"]


def test_mmr_contexts_remain_specific() -> None:
    plan = _load("data/reference/routine_rescue_data_plan.json")
    mmr = next(x for x in plan["sources"] if x["source_id"] == "pni_triplice_viral")
    assert mmr["confirmed"]["blockade_strategy_code"] == "3"
    assert mmr["confirmed"]["intensification_strategy_code"] == "4"
    assert "não usar" in mmr["guardrail"].lower()
