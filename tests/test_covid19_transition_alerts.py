from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from covid19_transition_alerts import evaluate_inventory_row


def _row(**overrides):
    row = {
        "reference_date": "2026-09-26",
        "territory_code": "5103403",
        "facility_cnes": "0000000",
        "product_variant_id": "comirnaty_lp81_refrigerated_12plus",
        "lot": "LOT-A",
        "expiry_date": "2026-12-31",
        "stock_available_doses": 300,
        "doses_administered_30d": 150,
        "physical_losses_30d": 0,
        "technical_losses_30d": 0,
        "storage_capacity_doses": 500,
        "requested_doses_next_cycle": 150,
    }
    row.update(overrides)
    return row


def _ids(result: dict) -> set[str]:
    return {x["alert_id"] for x in result["alerts"]}


def test_normal_inventory_has_no_alerts() -> None:
    result = evaluate_inventory_row(_row())
    assert result["alerts"] == []
    assert result["has_critical_alert"] is False


def test_expiry_within_30_days_is_critical() -> None:
    result = evaluate_inventory_row(
        _row(expiry_date="2026-10-15", stock_available_doses=100)
    )
    alert = next(x for x in result["alerts"] if x["alert_id"] == "lot_expiry_risk")
    assert alert["severity"] == "critical"
    assert result["has_critical_alert"] is True


def test_positive_stock_without_recent_consumption_alerts() -> None:
    result = evaluate_inventory_row(
        _row(stock_available_doses=200, doses_administered_30d=0)
    )
    assert "high_stock_low_consumption" in _ids(result)
    assert result["metrics"]["days_of_stock_at_recent_consumption"] is None


def test_high_days_of_stock_alerts() -> None:
    result = evaluate_inventory_row(
        _row(stock_available_doses=1000, doses_administered_30d=100)
    )
    assert "high_stock_low_consumption" in _ids(result)
    assert result["metrics"]["days_of_stock_at_recent_consumption"] == 300.0


def test_loss_rate_threshold_alerts() -> None:
    result = evaluate_inventory_row(
        _row(
            doses_administered_30d=90,
            physical_losses_30d=5,
            technical_losses_30d=5,
        )
    )
    assert "loss_rate_increase" in _ids(result)
    assert result["metrics"]["loss_rate_30d_pct"] == 10.0


def test_stock_above_cold_chain_capacity_is_critical() -> None:
    result = evaluate_inventory_row(
        _row(stock_available_doses=600, storage_capacity_doses=500)
    )
    assert "cold_chain_capacity_constraint" in _ids(result)
    assert result["has_critical_alert"] is True


def test_request_above_twice_recent_consumption_alerts() -> None:
    result = evaluate_inventory_row(
        _row(doses_administered_30d=100, requested_doses_next_cycle=250)
    )
    assert "request_above_consumption_capacity" in _ids(result)


def test_alert_interpretation_is_operational_not_clinical() -> None:
    result = evaluate_inventory_row(_row())
    text = result["interpretation"].lower()
    assert "operacionais" in text
    assert "não representam recomendação clínica" in text
