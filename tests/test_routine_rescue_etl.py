from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from routine_rescue_etl import process_rows


def _row(patient: str, vaccine: str, strategy: str, dose: str, date: str = "2026-08-01") -> dict:
    return {
        "codigo_paciente": patient,
        "codigo_vacina": vaccine,
        "codigo_estrategia_vacinacao": strategy,
        "codigo_dose_vacina": dose,
        "data_vacina": date,
        "sigla_uf_paciente": "MT",
        "codigo_municipio_paciente": "510340",
    }


def test_menacwy_observed_and_known_booster_context() -> None:
    out = process_rows([
        _row("a", "74", "1", "38"),
        _row("b", "74", "1", "1"),
        _row("c", "74", "2", "38"),
    ])["menacwy"]
    assert out["total_doses"] == 3
    assert out["total_pessoas"] == 3
    assert out["known_routine_booster_records"] == 1


def test_yellow_fever_known_dose_mix() -> None:
    out = process_rows([
        _row("a", "14", "1", "1"),
        _row("b", "14", "1", "9"),
        _row("c", "14", "1", "36"),
        _row("d", "14", "1", "99"),
    ])["febre_amarela"]
    assert out["total_doses"] == 4
    assert out["known_dose_records"] == 3
    assert out["unknown_dose_records"] == 1


def test_mmr_contexts_require_valid_strategy_dose_pairs() -> None:
    out = process_rows([
        _row("a", "24", "3", "57"),
        _row("b", "24", "3", "1"),
        _row("c", "24", "3", "99"),
        _row("d", "24", "4", "2"),
        _row("e", "24", "4", "57"),
    ])["triplice_viral"]
    assert out["total_doses"] == 5
    assert out["blockade_records"] == 2
    assert out["intensification_records"] == 1


def test_hpv4_stays_blocked_without_code() -> None:
    result = process_rows([
        _row("a", "999", "1", "9"),
    ])
    assert result["hpv4_status"] == "blocked_pending_official_code"
    assert result["target_hits"] == 0


def test_people_are_deduplicated_but_doses_are_not() -> None:
    out = process_rows([
        _row("same", "74", "1", "38", "2026-07-01"),
        _row("same", "74", "1", "38", "2026-08-01"),
    ])["menacwy"]
    assert out["total_doses"] == 2
    assert out["total_pessoas"] == 1
    assert out["reference_period"] == "2026-08"
