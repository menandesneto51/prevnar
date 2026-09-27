from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from influenza_etl import process_rows


def _row(
    *,
    patient: str,
    vaccine: str,
    strategy: str,
    dose: str,
    date: str = "2026-05-10",
    uf: str = "MT",
) -> dict:
    return {
        "codigo_paciente": patient,
        "codigo_vacina": vaccine,
        "codigo_estrategia_vacinacao": strategy,
        "codigo_dose_vacina": dose,
        "data_vacina": date,
        "sigla_uf_paciente": uf,
        "codigo_municipio_paciente": "510340",
    }


def test_public_trivalent_routine_and_special_are_confirmed() -> None:
    out = process_rows([
        _row(patient="a", vaccine="33", strategy="1", dose="1"),
        _row(patient="b", vaccine="33", strategy="1", dose="9"),
        _row(patient="c", vaccine="33", strategy="2", dose="2"),
    ])

    assert out["observed_code_hits"] == 3
    assert out["confirmed_context_doses"] == 3
    assert out["contextos_confirmados"]["public_routine"] == 2
    assert out["contextos_confirmados"]["public_special"] == 1
    assert out["sus_confirmed_doses"] == 3


def test_private_tetravalent_and_high_dose_remain_separate() -> None:
    out = process_rows([
        _row(patient="a", vaccine="77", strategy="8", dose="1"),
        _row(patient="b", vaccine="77", strategy="8", dose="9"),
        _row(patient="c", vaccine="110", strategy="8", dose="9"),
    ])

    assert out["confirmed_context_doses"] == 3
    assert out["private_confirmed_doses"] == 3
    assert out["contextos_confirmados"]["private_tetravalent"] == 2
    assert out["contextos_confirmados"]["private_high_dose"] == 1
    assert out["private_share_pct"] == 100.0


def test_unmapped_strategy_is_observed_but_not_confirmed() -> None:
    out = process_rows([
        _row(patient="a", vaccine="33", strategy="99", dose="9"),
    ])

    assert out["observed_code_hits"] == 1
    assert out["confirmed_context_doses"] == 0
    assert out["mismatches"]["code_hit_outside_confirmed_context"] == 1


def test_high_dose_only_accepts_single_dose_code() -> None:
    out = process_rows([
        _row(patient="a", vaccine="110", strategy="8", dose="1"),
        _row(patient="b", vaccine="110", strategy="8", dose="9"),
    ])

    assert out["observed_code_hits"] == 2
    assert out["confirmed_context_doses"] == 1
    assert out["contextos_confirmados"]["private_high_dose"] == 1
    assert out["mismatches"]["code_hit_outside_confirmed_context"] == 1


def test_people_are_deduplicated() -> None:
    out = process_rows([
        _row(patient="same", vaccine="33", strategy="1", dose="1", date="2026-04-01"),
        _row(patient="same", vaccine="33", strategy="1", dose="2", date="2026-05-01"),
    ])

    assert out["observed_code_hits"] == 2
    assert out["observed_people"] == 1
    assert out["confirmed_context_people"] == 1
    assert out["reference_period"] == "2026-05"


def test_school_context_remains_explicitly_pending() -> None:
    out = process_rows([])
    assert out["pending_contexts"][0]["id"] == "school_vaccination_le14"
    assert "código não validado" in out["pending_contexts"][0]["reason"].lower()
