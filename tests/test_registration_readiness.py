from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from registration_readiness import build_registration_readiness, evaluate_mapping


def _by_id(payload: dict) -> dict[str, dict]:
    return {row["immunobiologic_id"]: row for row in payload["items"]}


def test_current_monitored_immunobiologics_are_registration_ready() -> None:
    payload = build_registration_readiness()
    assert payload["summary"]["monitored_not_ready"] == []


def test_expected_ready_immunobiologics() -> None:
    rows = _by_id(build_registration_readiness())
    for iid in ("vpc20", "vvsr_materna", "nirsevimab", "influenza"):
        assert rows[iid]["etl_ready"] is True
        assert rows[iid]["blocking_dimensions"] == []
        assert rows[iid]["readiness_pct"] == 100.0


def test_covid_code_is_confirmed_but_registration_is_not_ready() -> None:
    row = _by_id(build_registration_readiness())["covid19"]
    assert row["etl_ready"] is False
    assert row["readiness_pct"] == 25.0
    assert set(row["blocking_dimensions"]) == {
        "strategy",
        "dose",
        "attendance_group",
    }


def test_hpv4_code_confirmation_does_not_unlock_etl() -> None:
    row = _by_id(build_registration_readiness())["hpv4"]
    assert row["etl_ready"] is False
    assert row["readiness_pct"] == 25.0
    assert "strategy" in row["blocking_dimensions"]
    assert "dose" in row["blocking_dimensions"]
    assert "attendance_group" in row["blocking_dimensions"]


def test_partial_mapping_blocks_menacwy_yellow_fever_and_mmr() -> None:
    rows = _by_id(build_registration_readiness())
    assert rows["menacwy"]["etl_ready"] is False
    assert rows["febre_amarela"]["etl_ready"] is False
    assert rows["triplice_viral"]["etl_ready"] is False


def test_required_dimension_missing_from_registry_blocks_readiness() -> None:
    row = evaluate_mapping(
        {
            "immunobiologic_id": "demo",
            "required_dimensions": ["immunobiologic_code", "strategy"],
            "dimensions": {
                "immunobiologic_code": {
                    "status": "confirmed",
                    "values": ["1"],
                    "evidence_type": "official_terminology",
                }
            },
        }
    )
    assert row["etl_ready"] is False
    assert row["blocking_dimensions"] == ["strategy"]


def test_invalid_mapping_status_fails_closed() -> None:
    try:
        evaluate_mapping(
            {
                "immunobiologic_id": "demo",
                "required_dimensions": ["strategy"],
                "dimensions": {
                    "strategy": {
                        "status": "assumed",
                        "values": ["1"],
                        "evidence_type": "secondary",
                    }
                },
            }
        )
    except ValueError as exc:
        assert "status inválido" in str(exc)
    else:
        raise AssertionError("invalid status must fail closed")
