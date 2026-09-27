from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from vaccine_rules import active_rules, evaluate_operational, validate_registry_integrity


TODAY = date(2026, 9, 26)


def test_respiratory_registry_integrity() -> None:
    assert validate_registry_integrity() == []


def test_maternal_rsv_below_28_weeks_is_not_eligible() -> None:
    result = evaluate_operational(
        "vvsr_materna",
        age_months=0,
        gestational_age_weeks=27.9,
        already_administered_this_pregnancy=False,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is False
    assert pathway["reason"] == "below_minimum_gestational_age"


def test_maternal_rsv_at_28_weeks_recommends_one_dose() -> None:
    result = evaluate_operational(
        "vvsr_materna",
        age_months=0,
        gestational_age_weeks=28,
        already_administered_this_pregnancy=False,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is True
    assert pathway["requires_review"] is False
    assert pathway["recommendation"] == "one_dose_vvsr_this_pregnancy"
    assert pathway["schedule"]["doses_per_pregnancy"] == 1


def test_maternal_rsv_does_not_repeat_routine_dose_same_pregnancy() -> None:
    result = evaluate_operational(
        "vvsr_materna",
        age_months=0,
        gestational_age_weeks=35,
        already_administered_this_pregnancy=True,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is False
    assert pathway["recommendation"] == "do_not_repeat_routine_dose"


def test_maternal_rsv_early_administered_is_not_repeated() -> None:
    result = evaluate_operational(
        "vvsr_materna",
        age_months=0,
        gestational_age_weeks=26,
        already_administered_this_pregnancy=True,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is False
    assert pathway["recommendation"] == "do_not_repeat_routine_dose"
    assert pathway["reason"] == "early_dose_already_administered_monitor_no_repeat"


def test_maternal_rsv_unknown_history_requires_review() -> None:
    result = evaluate_operational(
        "vvsr_materna",
        age_months=0,
        gestational_age_weeks=32,
        already_administered_this_pregnancy=None,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is True
    assert pathway["requires_review"] is True


def test_nirsevimab_first_season_under_5kg_uses_50mg() -> None:
    result = evaluate_operational(
        "nirsevimab",
        age_months=3,
        birth_gestational_age_days=36 * 7 + 6,
        eligible_comorbidity=False,
        weight_kg=4.9,
        vsr_season_number=1,
        in_vsr_season=True,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is True
    assert pathway["requires_review"] is False
    assert pathway["dose"]["dose_mg"] == 50
    assert pathway["dose"]["volume_ml"] == 0.5


def test_nirsevimab_first_season_5kg_or_more_uses_100mg() -> None:
    result = evaluate_operational(
        "nirsevimab",
        age_months=5,
        birth_gestational_age_days=35 * 7,
        eligible_comorbidity=False,
        weight_kg=5.0,
        vsr_season_number=1,
        in_vsr_season=True,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["dose"]["dose_mg"] == 100
    assert pathway["dose"]["volume_ml"] == 1.0


def test_nirsevimab_comorbidity_second_season_uses_200mg_two_injections() -> None:
    result = evaluate_operational(
        "nirsevimab",
        age_months=18,
        birth_gestational_age_days=40 * 7,
        eligible_comorbidity=True,
        weight_kg=10.0,
        vsr_season_number=2,
        in_vsr_season=True,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is True
    assert pathway["dose"]["dose_mg"] == 200
    assert pathway["dose"]["injections"] == 2
    assert pathway["dose"]["injection_volume_ml"] == 1.0


def test_prematurity_only_no_longer_qualifies_at_six_months() -> None:
    result = evaluate_operational(
        "nirsevimab",
        age_months=6,
        birth_gestational_age_days=32 * 7,
        eligible_comorbidity=False,
        weight_kg=6,
        vsr_season_number=1,
        in_vsr_season=True,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is False
    assert pathway["reason"] == "eligibility_criteria_not_met"


def test_premature_nirsevimab_is_year_round() -> None:
    result = evaluate_operational(
        "nirsevimab",
        age_months=3,
        birth_gestational_age_days=35 * 7,
        eligible_comorbidity=False,
        weight_kg=4,
        vsr_season_number=1,
        in_vsr_season=False,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is True
    assert pathway["requires_review"] is False
    assert pathway["dose"]["dose_mg"] == 50


def test_comorbidity_only_outside_season_requires_review() -> None:
    result = evaluate_operational(
        "nirsevimab",
        age_months=18,
        birth_gestational_age_days=40 * 7,
        eligible_comorbidity=True,
        weight_kg=10,
        vsr_season_number=2,
        in_vsr_season=False,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is True
    assert pathway["requires_review"] is True
    assert pathway["recommendation"] == "review_outside_or_unknown_vsr_season"


def test_influenza_remains_draft_but_covid_has_selected_active_rules() -> None:
    assert active_rules("influenza", on_date=TODAY) == []
    covid_ids = {rule["rule_id"] for rule in active_rules("covid19", on_date=TODAY)}
    assert "covid19_maternal_2026" in covid_ids
    assert "covid19_elderly_2026" in covid_ids
    assert "covid19_comirnaty_lp81_operational_2026" in covid_ids
    assert "covid19_transition_management_2026" in covid_ids
