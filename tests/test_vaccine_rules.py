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
    special_strategy_codes,
    validate_registry_integrity,
    vaccine_codes,
)


def test_registry_cross_references_are_valid() -> None:
    assert validate_registry_integrity() == []


def test_vpc20_codes_come_from_registry() -> None:
    assert vaccine_codes("vpc20") == {"107"}
    assert "2" in special_strategy_codes(
        "vpc20", include_observed_compatibility=False
    )
    assert "8" in special_strategy_codes(
        "vpc20", include_observed_compatibility=True
    )


def test_rie_rule_is_active_after_nt52_start() -> None:
    rules = active_rules("vpc20", on_date=date(2026, 6, 1))
    ids = {row["rule_id"] for row in rules}
    assert "vpc20_rie_2026" in ids
    assert "vpc20_elderly_85_2026" not in ids


def test_rie_age_5_plus_single_dose_path() -> None:
    result = evaluate_operational(
        "vpc20",
        age_months=60,
        condition_ids=[19],
        pneumococcal_history="none",
        on_date=date(2026, 9, 26),
    )
    rie = next(p for p in result["pathways"] if p["pathway"] == "rie_special")
    assert rie["eligible"] is True
    assert rie["requires_review"] is False
    assert rie["recommendation"] == "vpc20_schedule"
    assert rie["schedule"]["primary_doses"] == 1


def test_tcth_uses_three_dose_special_schedule_from_12_months() -> None:
    result = evaluate_operational(
        "vpc20",
        age_months=120,
        condition_ids=[4],
        pneumococcal_history="none",
        on_date=date(2026, 9, 26),
    )
    rie = next(p for p in result["pathways"] if p["pathway"] == "rie_special")
    assert rie["requires_review"] is False
    assert rie["schedule"]["primary_doses"] == 3
    assert rie["schedule"]["interval_months"] == [2, 2]


def test_car_t_is_not_auto_scheduled() -> None:
    result = evaluate_operational(
        "vpc20",
        age_months=300,
        condition_ids=[5],
        pneumococcal_history="none",
        on_date=date(2026, 9, 26),
    )
    rie = next(p for p in result["pathways"] if p["pathway"] == "rie_special")
    assert rie["eligible"] is True
    assert rie["requires_review"] is True
    assert rie["recommendation"] == "clinical_protocol_review"


def test_elderly_rule_does_not_apply_before_85_years() -> None:
    result = evaluate_operational(
        "vpc20",
        age_months=(85 * 12) - 1,
        pneumococcal_history="none",
        on_date=date(2026, 9, 26),
    )
    assert all(p["pathway"] != "elderly_85_plus" for p in result["pathways"])


def test_elderly_85_no_history_recommends_single_dose() -> None:
    result = evaluate_operational(
        "vpc20",
        age_months=85 * 12,
        pneumococcal_history="none",
        on_date=date(2026, 9, 26),
    )
    elderly = next(p for p in result["pathways"] if p["pathway"] == "elderly_85_plus")
    assert elderly["eligible"] is True
    assert elderly["requires_review"] is False
    assert elderly["recommendation"] == "one_vpc20"
    assert elderly["prescription_required"] is False


def test_elderly_85_one_vpp23_uses_one_year_minimum_interval() -> None:
    result = evaluate_operational(
        "vpc20",
        age_months=90 * 12,
        pneumococcal_history="one_vpp23",
        on_date=date(2026, 9, 26),
    )
    elderly = next(p for p in result["pathways"] if p["pathway"] == "elderly_85_plus")
    assert elderly["recommendation"] == "one_vpc20"
    assert elderly["history_rule"]["min_interval_days"] == 365


def test_elderly_85_two_vpp23_does_not_recommend_vpc20() -> None:
    result = evaluate_operational(
        "vpc20",
        age_months=90 * 12,
        pneumococcal_history="two_vpp23",
        on_date=date(2026, 9, 26),
    )
    elderly = next(p for p in result["pathways"] if p["pathway"] == "elderly_85_plus")
    assert elderly["recommendation"] == "do_not_apply_vpc20"


def test_unknown_history_requires_review_in_elderly_path() -> None:
    result = evaluate_operational(
        "vpc20",
        age_months=90 * 12,
        pneumococcal_history="unknown",
        on_date=date(2026, 9, 26),
    )
    elderly = next(p for p in result["pathways"] if p["pathway"] == "elderly_85_plus")
    assert elderly["requires_review"] is True
    assert result["requires_review"] is True
