from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from vaccine_rules import active_rules, get_immunobiologic, validate_registry_integrity


TODAY = date(2026, 9, 26)


def test_routine_rescue_registry_integrity() -> None:
    assert validate_registry_integrity() == []


def test_hpv_has_active_routine_rule_but_data_mapping_remains_pending() -> None:
    item = get_immunobiologic("hpv4")
    assert item["type"] == "vaccine"
    assert item["onboarding_status"] == "rules_structured_data_mapping_pending"
    assert item["pni_codes"] == []
    ids = {r["rule_id"] for r in active_rules("hpv4", on_date=TODAY)}
    assert "hpv4_routine_2026" in ids


def test_menacwy_has_active_national_routine_rule() -> None:
    item = get_immunobiologic("menacwy")
    assert item["type"] == "vaccine"
    ids = {r["rule_id"] for r in active_rules("menacwy", on_date=TODAY)}
    assert "menacwy_routine_2026" in ids


def test_yellow_fever_has_active_national_routine_rule() -> None:
    item = get_immunobiologic("febre_amarela")
    assert item["type"] == "vaccine"
    ids = {r["rule_id"] for r in active_rules("febre_amarela", on_date=TODAY)}
    assert "febre_amarela_routine_2026" in ids


def test_mmr_has_active_national_routine_rule() -> None:
    item = get_immunobiologic("triplice_viral")
    assert item["type"] == "vaccine"
    ids = {r["rule_id"] for r in active_rules("triplice_viral", on_date=TODAY)}
    assert "triplice_viral_routine_2026" in ids


def test_mmr_note_requires_context_specific_rules() -> None:
    item = get_immunobiologic("triplice_viral")
    note = item["note"].lower()
    assert "dose zero" in note
    assert "territori" in note
    assert "bloqueio" in note or "intensificação" in note
