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
    assert item["onboarding_status"] == "normative_discovery"


def test_nirsevimab_draft_rule_is_never_active() -> None:
    rules = active_rules("nirsevimab", on_date=date(2026, 9, 26))
    assert rules == []


def test_nirsevimab_does_not_generate_automatic_eligibility_before_onboarding() -> None:
    result = evaluate_operational(
        "nirsevimab",
        age_months=2,
        condition_ids=[],
        on_date=date(2026, 9, 26),
    )
    assert result["immunobiologic_type"] == "monoclonal_antibody"
    assert result["eligible_by_any_rule"] is False
    assert result["pathways"] == []
    assert result["requires_review"] is False
    assert "vaccine_id" not in result
