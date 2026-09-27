from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from vaccine_rules import active_rules, get_immunobiologic


def test_influenza_registry_matches_nt24_2026() -> None:
    item = get_immunobiologic("influenza")
    assert set(item["pni_codes"]) == {"33", "77", "110"}
    assert item["onboarding_status"] == "data_mapping_structured_rule_draft"

    contexts = item["pni_registration"]["confirmed_contexts"]
    assert contexts["public_routine"]["strategy_code"] == "1"
    assert contexts["public_special"]["strategy_code"] == "2"
    assert contexts["private_tetravalent"]["strategy_code"] == "8"
    assert contexts["private_high_dose"]["dose_codes"] == ["9"]


def test_influenza_school_strategy_remains_pending_code() -> None:
    item = get_immunobiologic("influenza")
    school = item["pni_registration"]["school_context"]
    assert school["documented"] is True
    assert school["strategy_code"] is None
    assert school["mapping_status"] == "pending_official_code_confirmation"


def test_influenza_clinical_rule_remains_draft() -> None:
    assert active_rules("influenza", on_date=date(2026, 9, 26)) == []


def test_influenza_data_plan_keeps_coverage_constraints() -> None:
    plan = json.loads(
        (ROOT / "data/reference/influenza_2026_data_plan.json").read_text(
            encoding="utf-8"
        )
    )
    text = " ".join(plan["indicator_constraints"]).lower()
    assert "crianças" in text
    assert "gestantes" in text
    assert "idosos" in text
    assert "serviço privado" in text
