from __future__ import annotations

import json
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
    validate_registry_integrity,
)


TODAY = date(2026, 9, 26)


def _pathway(result: dict, name: str) -> dict:
    return next(x for x in result["pathways"] if x["pathway"] == name)


def test_covid_registry_integrity() -> None:
    assert validate_registry_integrity() == []


def test_comirnaty_lp81_operational_profile_is_structured() -> None:
    item = get_immunobiologic("covid19")
    assert item["pni_codes"] == []
    assert item["monitored"] is False
    assert item["code_mapping_status"] == "product_registration_codes_pending"

    product = next(
        x for x in item["product_variants"]
        if x["product_variant_id"] == "comirnaty_lp81_refrigerated_12plus"
    )
    assert product["min_age_years"] == 12
    assert product["dose_ml"] == 0.3
    assert product["dose_mcg"] == 30
    assert product["doses_per_vial"] == 6
    assert product["storage_celsius_min"] == 2
    assert product["storage_celsius_max"] == 8
    assert product["must_not_freeze"] is True


def test_covid_active_rules_include_clinical_and_operational_layers() -> None:
    rules = active_rules("covid19", on_date=TODAY)
    ids = {x["rule_id"] for x in rules}
    assert "covid19_maternal_2026" in ids
    assert "covid19_elderly_2026" in ids
    assert "covid19_comirnaty_lp81_operational_2026" in ids
    assert "covid19_transition_management_2026" in ids


def test_pregnant_without_prior_dose_gets_one_dose_this_pregnancy() -> None:
    result = evaluate_operational(
        "covid19",
        age_months=30 * 12,
        pregnant=True,
        covid_dose_received_this_pregnancy=False,
        covid_has_prior_dose=False,
        on_date=TODAY,
    )
    maternal = _pathway(result, "maternal_covid")
    assert maternal["eligible"] is True
    assert maternal["requires_review"] is False
    assert maternal["recommendation"] == "one_covid_dose_this_pregnancy"


def test_pregnant_dose_already_given_this_pregnancy_is_not_repeated() -> None:
    result = evaluate_operational(
        "covid19",
        age_months=28 * 12,
        pregnant=True,
        covid_dose_received_this_pregnancy=True,
        covid_has_prior_dose=True,
        months_since_last_covid_dose=2,
        on_date=TODAY,
    )
    maternal = _pathway(result, "maternal_covid")
    assert maternal["eligible"] is False
    assert maternal["recommendation"] == "dose_this_pregnancy_already_received"


def test_pregnant_prior_dose_under_six_months_is_deferred() -> None:
    result = evaluate_operational(
        "covid19",
        age_months=32 * 12,
        pregnant=True,
        covid_dose_received_this_pregnancy=False,
        covid_has_prior_dose=True,
        months_since_last_covid_dose=5.9,
        on_date=TODAY,
    )
    maternal = _pathway(result, "maternal_covid")
    assert maternal["recommendation"] == "defer_until_minimum_interval"
    assert maternal["min_interval_months"] == 6


def test_pregnant_prior_dose_at_six_months_is_eligible() -> None:
    result = evaluate_operational(
        "covid19",
        age_months=32 * 12,
        pregnant=True,
        covid_dose_received_this_pregnancy=False,
        covid_has_prior_dose=True,
        months_since_last_covid_dose=6,
        on_date=TODAY,
    )
    maternal = _pathway(result, "maternal_covid")
    assert maternal["recommendation"] == "one_covid_dose_this_pregnancy"


def test_elderly_rule_starts_at_60_years() -> None:
    below = evaluate_operational(
        "covid19",
        age_months=(60 * 12) - 1,
        pregnant=False,
        covid_has_prior_dose=False,
        on_date=TODAY,
    )
    assert all(x["pathway"] != "elderly_covid" for x in below["pathways"])

    at_60 = evaluate_operational(
        "covid19",
        age_months=60 * 12,
        pregnant=False,
        covid_has_prior_dose=False,
        on_date=TODAY,
    )
    elderly = _pathway(at_60, "elderly_covid")
    assert elderly["eligible"] is True
    assert elderly["recommendation"] == "one_covid_dose"


def test_elderly_semester_interval_is_enforced() -> None:
    early = evaluate_operational(
        "covid19",
        age_months=70 * 12,
        pregnant=False,
        covid_has_prior_dose=True,
        months_since_last_covid_dose=4,
        on_date=TODAY,
    )
    assert _pathway(early, "elderly_covid")["recommendation"] == "defer_until_semester_interval"

    due = evaluate_operational(
        "covid19",
        age_months=70 * 12,
        pregnant=False,
        covid_has_prior_dose=True,
        months_since_last_covid_dose=6,
        on_date=TODAY,
    )
    assert _pathway(due, "elderly_covid")["recommendation"] == "one_covid_dose"


def test_operational_rules_do_not_create_clinical_pathways() -> None:
    result = evaluate_operational(
        "covid19",
        age_months=20 * 12,
        pregnant=False,
        covid_has_prior_dose=False,
        on_date=TODAY,
    )
    assert result["pathways"] == []
    assert result["eligible_by_any_rule"] is False


def test_operational_plan_keeps_pni_mapping_blocked() -> None:
    plan = json.loads(
        (ROOT / "data/reference/covid19_2026_operational_plan.json").read_text(
            encoding="utf-8"
        )
    )
    assert plan["data_mapping"]["pni_product_codes_status"] == "pending"
    assert "do not activate" in plan["data_mapping"]["rule"].lower()
