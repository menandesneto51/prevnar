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


def test_menacwy_child_booster_after_valid_interval() -> None:
    result = evaluate_operational(
        "menacwy",
        age_months=12,
        menc_primary_complete=True,
        days_since_last_menc=60,
        menacwy_child_booster_received=False,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is True
    assert pathway["requires_review"] is False
    assert pathway["recommendation"] == "one_menacwy_booster"


def test_menacwy_child_booster_defers_before_60_days() -> None:
    result = evaluate_operational(
        "menacwy",
        age_months=14,
        menc_primary_complete=True,
        days_since_last_menc=30,
        menacwy_child_booster_received=False,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["recommendation"] == "defer_until_minimum_interval"
    assert pathway["min_interval_days"] == 60


def test_menacwy_adolescent_one_dose_when_not_received() -> None:
    result = evaluate_operational(
        "menacwy",
        age_months=11 * 12,
        menacwy_adolescent_dose_received=False,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is True
    assert pathway["recommendation"] == "one_menacwy_dose"


def test_menacwy_unknown_adolescent_history_requires_review() -> None:
    result = evaluate_operational(
        "menacwy",
        age_months=13 * 12,
        menacwy_adolescent_dose_received=None,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["requires_review"] is True
    assert pathway["recommendation"] == "verify_adolescent_menacwy_history"


def test_yellow_fever_age_5_to_59_unvaccinated_gets_one_standard_dose() -> None:
    result = evaluate_operational(
        "febre_amarela",
        age_months=20 * 12,
        yellow_fever_history="none",
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is True
    assert pathway["requires_review"] is False
    assert pathway["recommendation"] == "one_standard_dose"


def test_yellow_fever_one_dose_before_5_needs_booster_after_interval() -> None:
    result = evaluate_operational(
        "febre_amarela",
        age_months=10 * 12,
        yellow_fever_history="one_dose_before_5",
        days_since_last_yellow_fever_dose=100,
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is True
    assert pathway["recommendation"] == "one_booster"


def test_yellow_fever_one_dose_at_or_after_5_is_complete() -> None:
    result = evaluate_operational(
        "febre_amarela",
        age_months=30 * 12,
        yellow_fever_history="one_dose_at_or_after_5",
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is False
    assert pathway["recommendation"] == "complete_no_more_doses"


def test_yellow_fever_fractional_2018_only_gets_standard_booster() -> None:
    result = evaluate_operational(
        "febre_amarela",
        age_months=15 * 12,
        yellow_fever_history="fractional_2018_only",
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["eligible"] is True
    assert pathway["recommendation"] == "one_standard_booster"


def test_yellow_fever_age_60_plus_requires_risk_benefit_review() -> None:
    result = evaluate_operational(
        "febre_amarela",
        age_months=60 * 12,
        yellow_fever_history="none",
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["requires_review"] is True
    assert pathway["recommendation"] == "individual_risk_benefit_review"


def test_yellow_fever_6_to_8_months_is_exception_not_routine_auto_dose() -> None:
    result = evaluate_operational(
        "febre_amarela",
        age_months=7,
        yellow_fever_history="none",
        on_date=TODAY,
    )
    pathway = result["pathways"][0]
    assert pathway["requires_review"] is True
    assert pathway["recommendation"] == "risk_benefit_review_for_exceptional_dose_zero"
