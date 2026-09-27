from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from extract_nacional import _agg_sies
from sies_transition_adapter import build_dashboard, load_rows, normalize_row


def _inventory_row(**overrides):
    row = {
        "reference_date": "2026-09-26",
        "territory_code": "5103403",
        "facility_cnes": "1234567",
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


def test_portuguese_aliases_are_normalized() -> None:
    row = normalize_row(
        {
            "data_referencia": "26/09/2026",
            "ibge": "5103403",
            "cnes": "1234567",
            "produto": "Comirnaty LP.8.1",
            "lote": "LOT-A",
            "validade": "31/12/2026",
            "saldo_estoque": "100",
            "aplicadas_30d": "50",
        }
    )
    assert row["reference_date"] == "2026-09-26"
    assert row["expiry_date"] == "2026-12-31"
    assert row["product_variant_id"] == "comirnaty_lp81_refrigerated_12plus"
    assert row["stock_available_doses"] == 100
    assert row["doses_administered_30d"] == 50


def test_personal_fields_are_rejected() -> None:
    with pytest.raises(ValueError, match="campos pessoais proibidos"):
        normalize_row({**_inventory_row(), "cpf": "00000000000"})


def test_missing_required_inventory_field_is_rejected() -> None:
    row = _inventory_row()
    row.pop("lot")
    with pytest.raises(ValueError, match="campos obrigatórios ausentes"):
        normalize_row(row)


def test_negative_logistics_values_are_rejected() -> None:
    with pytest.raises(ValueError, match="não pode ser negativo"):
        normalize_row(_inventory_row(stock_available_doses=-1))


def test_dashboard_aggregates_stock_and_alerts_without_raw_rows() -> None:
    payload = build_dashboard(
        [
            _inventory_row(
                lot="EXPIRING",
                expiry_date="2026-10-10",
                stock_available_doses=100,
                doses_administered_30d=10,
            ),
            _inventory_row(
                territory_code="5108402",
                facility_cnes="7654321",
                lot="NORMAL",
                stock_available_doses=200,
                doses_administered_30d=100,
            ),
        ]
    )
    assert payload["record_count"] == 2
    assert payload["totals"]["stock_available_doses"] == 300
    assert payload["totals"]["territories"] == 2
    assert payload["totals"]["critical_alerts"] >= 1
    assert "rows" not in payload
    assert "raw" not in payload


def test_semicolon_csv_is_supported(tmp_path: Path) -> None:
    path = tmp_path / "inventory.csv"
    path.write_text(
        "data_referencia;ibge;produto;lote;validade;saldo_estoque;aplicadas_30d\n"
        "26/09/2026;5103403;Comirnaty LP.8.1;LOT-A;31/12/2026;100;50\n",
        encoding="utf-8",
    )
    rows = load_rows(path)
    assert len(rows) == 1
    assert rows[0]["produto"] == "Comirnaty LP.8.1"


def test_public_sies_does_not_promote_generic_pneumo_to_vpc20() -> None:
    rows = [
        {
            "origem": "Distribuição",
            "ano": "2026",
            "qtde": "1000",
            "tx_sigla": "SES-MT",
            "tx_insumo": "PNEUMOCOCICA 13 VALENTE",
        }
    ]
    agg = _agg_sies(rows, ano_min=2024)
    assert agg["por_uf_pneumo"]["MT"] == 1000
    assert agg["por_uf_vpc20"] == {}
    assert agg["por_uf_distribuidas"] == {}


def test_public_sies_accepts_direct_vpc20_only() -> None:
    rows = [
        {
            "origem": "Distribuição",
            "ano": "2026",
            "qtde": "250",
            "tx_sigla": "SES-MT",
            "tx_insumo": "VACINA PNEUMOCOCICA 20 VALENTE VPC20",
        }
    ]
    agg = _agg_sies(rows, ano_min=2024)
    assert agg["por_uf_vpc20"]["MT"] == 250
    assert agg["por_uf_distribuidas"]["MT"] == 250
