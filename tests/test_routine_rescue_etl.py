from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from routine_rescue_etl import process_rows


def _row(
    *,
    patient: str,
    vaccine: str,
    strategy: str,
    dose: str,
    date: str = "2026-08-15",
    uf: str = "MT",
    mun: str = "510340",
) -> dict:
    return {
        "codigo_paciente": patient,
        "codigo_vacina": vaccine,
        "codigo_estrategia_vacinacao": strategy,
        "codigo_dose_vacina": dose,
        "codigo_vacina_grupo_atendimento": "",
        "data_vacina": date,
        "sigla_uf_paciente": uf,
        "codigo_municipio_paciente": mun,
    }


def test_menacwy_confirms_only_known_routine_booster_context() -> None:
    out = process_rows(
        [
            _row(patient="a", vaccine="74", strategy="1", dose="38"),
            _row(patient="b", vaccine="74", strategy="2", dose="38"),
        ]
    )["menacwy"]

    assert out["observed_code_hits"] == 2
    assert out["confirmed_context_doses"] == 1
    assert out["contextos_confirmados"]["routine_booster_confirmed"] == 1
    assert out["mismatches"]["code_hit_outside_confirmed_context"] == 1


def test_yellow_fever_accepts_only_known_coverage_dose_codes() -> None:
    out = process_rows(
        [
            _row(patient="a", vaccine="14", strategy="1", dose="1"),
            _row(patient="b", vaccine="14", strategy="1", dose="9"),
            _row(patient="c", vaccine="14", strategy="1", dose="36"),
            _row(patient="d", vaccine="14", strategy="1", dose="99"),
        ]
    )["febre_amarela"]

    assert out["observed_code_hits"] == 4
    assert out["confirmed_context_doses"] == 3
    assert out["mismatches"]["code_hit_outside_confirmed_context"] == 1


def test_mmr_separates_blockade_and_intensification() -> None:
    out = process_rows(
        [
            _row(patient="a", vaccine="24", strategy="3", dose="57"),
            _row(patient="b", vaccine="24", strategy="3", dose="1"),
            _row(patient="c", vaccine="24", strategy="4", dose="2"),
            _row(patient="d", vaccine="24", strategy="1", dose="1"),
        ]
    )["triplice_viral"]

    assert out["observed_code_hits"] == 4
    assert out["confirmed_context_doses"] == 3
    assert out["contextos_confirmados"]["blockade_dose_57"] == 1
    assert out["contextos_confirmados"]["blockade_dose_1"] == 1
    assert out["contextos_confirmados"]["intensification_dose_2"] == 1
    assert out["mismatches"]["code_hit_outside_confirmed_context"] == 1


def test_people_are_deduplicated_within_observed_and_confirmed_contexts() -> None:
    out = process_rows(
        [
            _row(
                patient="same",
                vaccine="74",
                strategy="1",
                dose="38",
                date="2026-07-01",
            ),
            _row(
                patient="same",
                vaccine="74",
                strategy="1",
                dose="38",
                date="2026-08-01",
            ),
        ]
    )["menacwy"]

    assert out["observed_code_hits"] == 2
    assert out["observed_people"] == 1
    assert out["confirmed_context_doses"] == 2
    assert out["confirmed_context_people"] == 1
    assert out["reference_period"] == "2026-08"


def test_hpv_is_explicitly_not_collected_until_mapping_is_complete() -> None:
    result = process_rows(
        [_row(patient="a", vaccine="67", strategy="1", dose="9")]
    )
    assert result["hpv4"]["status"] == "not_collected"
    assert result["hpv4"]["immunobiologic_codes"] == ["67"]


def test_unrelated_vaccine_is_ignored() -> None:
    result = process_rows(
        [_row(patient="a", vaccine="107", strategy="2", dose="9")]
    )
    assert result["menacwy"]["observed_code_hits"] == 0
    assert result["febre_amarela"]["observed_code_hits"] == 0
    assert result["triplice_viral"]["observed_code_hits"] == 0
