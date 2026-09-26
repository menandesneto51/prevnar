from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from vaccine_rules import (
    active_rules,
    evaluate_operational,
    get_immunobiologic,
    immunobiologic_codes,
    validate_registry_integrity,
)


def test_immunobiologic_registry_integrity() -> None:
    assert validate_registry_integrity() == []


def test_vpc20_is_exposed_as_vaccine_immunobiologic() -> None:
    item = get_immunobiologic("vpc20")
    assert item["type"] == "vaccine"
    assert item["vaccine_id"] == "vpc20"
    assert immunobiologic_codes("vpc20") == {"107"}


def test_nirsevimab_is_monoclonal_antibody_entity() -> None:
    item = get_immunobiologic("nirsevimab")
    assert item["type"] == "monoclonal_antibody"
    assert item["onboarding_status"] == "rules_structured_data_mapping_pending"


def test_nirsevimab_has_active_structured_rule_after_respiratory_onboarding() -> None:
    rules = active_rules("nirsevimab", on_date=date(2026, 9, 26))
    assert {r["rule_id"] for r in rules} == {"nirsevimab_vsr_2026"}


def test_nirsevimab_missing_clinical_inputs_requires_review() -> None:
    result = evaluate_operational(
        "nirsevimab",
        age_months=2,
        condition_ids=[],
        on_date=date(2026, 9, 26),
    )
    assert result["immunobiologic_type"] == "monoclonal_antibody"
    assert result["eligible_by_any_rule"] is False
    assert result["requires_review"] is True
    assert result["pathways"][0]["recommendation"] == "verify_prematurity_or_comorbidity"
    assert "vaccine_id" not in result
