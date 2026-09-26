from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from vaccine_rules import evaluate_operational

TODAY = date(2026, 9, 26)


def test_hpv_routine_unvaccinated_age_9_to_14_gets_one_dose() -> None:
    result = evaluate_operational(
        "hpv4",
        age_months=9 * 12,
        hpv_doses_received=0,
        pregnant=False,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is True
    assert pathway["requires_review"] is False
    assert pathway["recommendation"] == "one_hpv4_dose"


def test_hpv_routine_prior_dose_is_complete() -> None:
    result = evaluate_operational(
        "hpv4",
        age_months=13 * 12,
        hpv_doses_received=1,
        pregnant=False,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is False
    assert pathway["recommendation"] == "routine_schedule_complete"


def test_hpv_routine_unknown_history_requires_verification() -> None:
    result = evaluate_operational(
        "hpv4",
        age_months=12 * 12,
        hpv_doses_received=None,
        pregnant=False,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["requires_review"] is True
    assert pathway["recommendation"] == "verify_hpv_vaccination_history"


def test_hpv_routine_does_not_vaccinate_during_pregnancy() -> None:
    result = evaluate_operational(
        "hpv4",
        age_months=14 * 12,
        hpv_doses_received=0,
        pregnant=True,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is False
    assert pathway["recommendation"] == "do_not_vaccinate_during_pregnancy"


def test_hpv_rescue_age_is_not_silently_treated_as_routine() -> None:
    result = evaluate_operational(
        "hpv4",
        age_months=16 * 12,
        hpv_doses_received=0,
        pregnant=False,
        on_date=TODAY,
    )
    assert result["pathways"] == []
    assert result["eligible_by_any_rule"] is False


def test_mmr_age_12_months_needs_two_total_doses_if_unvaccinated() -> None:
    result = evaluate_operational(
        "triplice_viral",
        age_months=12,
        mmr_doses_received=0,
        is_healthcare_worker=False,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is True
    assert pathway["required_total_doses"] == 2
    assert pathway["remaining_doses"] == 2


def test_mmr_child_with_first_dose_waits_for_second_at_15_months() -> None:
    result = evaluate_operational(
        "triplice_viral",
        age_months=13,
        mmr_doses_received=1,
        is_healthcare_worker=False,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["recommendation"] == "second_mmr_component_dose_at_15_months"
    assert pathway["target_age_months"] == 15


def test_mmr_under_30_requires_two_total_doses() -> None:
    result = evaluate_operational(
        "triplice_viral",
        age_months=25 * 12,
        mmr_doses_received=1,
        is_healthcare_worker=False,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is True
    assert pathway["required_total_doses"] == 2
    assert pathway["remaining_doses"] == 1
    assert pathway["min_interval_days"] == 30


def test_mmr_age_30_to_59_requires_one_total_dose() -> None:
    result = evaluate_operational(
        "triplice_viral",
        age_months=40 * 12,
        mmr_doses_received=0,
        is_healthcare_worker=False,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is True
    assert pathway["recommendation"] == "one_mmr_dose"
    assert pathway["required_total_doses"] == 1


def test_mmr_healthcare_worker_requires_two_doses_regardless_age() -> None:
    result = evaluate_operational(
        "triplice_viral",
        age_months=62 * 12,
        mmr_doses_received=1,
        is_healthcare_worker=True,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is True
    assert pathway["required_total_doses"] == 2
    assert pathway["remaining_doses"] == 1


def test_mmr_non_healthcare_worker_age_60_plus_has_no_routine_path() -> None:
    result = evaluate_operational(
        "triplice_viral",
        age_months=62 * 12,
        mmr_doses_received=0,
        is_healthcare_worker=False,
        on_date=TODAY,
    )
    assert result["pathways"] == []


def test_mmr_is_not_recommended_during_pregnancy() -> None:
    result = evaluate_operational(
        "triplice_viral",
        age_months=25 * 12,
        mmr_doses_received=0,
        is_healthcare_worker=False,
        pregnant=True,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is False
    assert pathway["recommendation"] == "do_not_vaccinate_during_pregnancy"


def test_mmr_severe_immunosuppression_requires_specialist_review() -> None:
    result = evaluate_operational(
        "triplice_viral",
        age_months=25 * 12,
        mmr_doses_received=0,
        is_healthcare_worker=False,
        severe_immunosuppression=True,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is False
    assert pathway["requires_review"] is True
    assert pathway["recommendation"] == "specialist_review_live_vaccine_contraindication"


def test_hpv_completed_schedule_remains_complete_during_pregnancy() -> None:
    result = evaluate_operational(
        "hpv4",
        age_months=14 * 12,
        hpv_doses_received=1,
        pregnant=True,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is False
    assert pathway["recommendation"] == "routine_schedule_complete"


def test_mmr_completed_schedule_remains_complete_during_pregnancy() -> None:
    result = evaluate_operational(
        "triplice_viral",
        age_months=25 * 12,
        mmr_doses_received=2,
        is_healthcare_worker=False,
        pregnant=True,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is False
    assert pathway["recommendation"] == "routine_schedule_complete"


def test_mmr_completed_healthcare_schedule_not_overridden_by_immunosuppression() -> None:
    result = evaluate_operational(
        "triplice_viral",
        age_months=40 * 12,
        mmr_doses_received=2,
        is_healthcare_worker=True,
        severe_immunosuppression=True,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is False
    assert pathway["recommendation"] == "routine_schedule_complete"
