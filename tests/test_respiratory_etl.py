from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from respiratory_etl import _decorate_nirsevimab, process_rows


def _row(
    *,
    patient: str,
    vaccine: str,
    strategy: str,
    dose: str,
    group: str,
    date: str = "2026-08-15",
    uf: str = "MT",
    mun: str = "510340",
) -> dict:
    return {
        "codigo_paciente": patient,
        "codigo_vacina": vaccine,
        "codigo_estrategia_vacinacao": strategy,
        "codigo_dose_vacina": dose,
        "codigo_vacina_grupo_atendimento": group,
        "data_vacina": date,
        "sigla_uf_paciente": uf,
        "codigo_municipio_paciente": mun,
    }


def test_vvsr_mapping_accepts_only_official_combination() -> None:
    rows = [
        _row(
            patient="a",
            vaccine="108",
            strategy="1",
            dose="9",
            group="001801",
        ),
        _row(
            patient="b",
            vaccine="108",
            strategy="2",
            dose="9",
            group="001801",
        ),
    ]
    out = process_rows(rows)["vvsr_materna"]

    assert out["total_doses"] == 1
    assert out["total_pessoas"] == 1
    assert out["invalid_mapping"]["code_hit_but_registration_mismatch"] == 1


def test_vvsr_deduplicates_people_but_counts_doses() -> None:
    rows = [
        _row(
            patient="same",
            vaccine="108",
            strategy="1",
            dose="9",
            group="001801",
            date="2026-07-01",
        ),
        _row(
            patient="same",
            vaccine="108",
            strategy="1",
            dose="9",
            group="001801",
            date="2026-08-01",
        ),
    ]
    out = process_rows(rows)["vvsr_materna"]

    assert out["total_doses"] == 2
    assert out["total_pessoas"] == 1
    assert out["reference_period"] == "2026-08"


def test_nirsevimab_accepts_sus_and_private_without_merging_strategy_counts() -> None:
    rows = [
        _row(
            patient="a",
            vaccine="115",
            strategy="2",
            dose="59",
            group="000120",
        ),
        _row(
            patient="b",
            vaccine="116",
            strategy="8",
            dose="60",
            group="000116",
        ),
    ]
    out = process_rows(rows)["nirsevimab"]
    _decorate_nirsevimab(out)

    assert out["total_doses"] == 2
    assert out["total_pessoas"] == 2
    assert out["estrategias"]["2"] == 1
    assert out["estrategias"]["8"] == 1
    assert out["sus_doses"] == 1
    assert out["private_doses"] == 1
    assert out["private_share_pct"] == 50.0
    assert out["pt1_doses"] == 1
    assert out["pt2_doses"] == 1


def test_nirsevimab_rejects_unknown_dose_code() -> None:
    rows = [
        _row(
            patient="a",
            vaccine="115",
            strategy="2",
            dose="9",
            group="000120",
        )
    ]
    out = process_rows(rows)["nirsevimab"]

    assert out["total_doses"] == 0
    assert out["invalid_mapping"]["code_hit_but_registration_mismatch"] == 1


def test_unrelated_vaccine_is_ignored() -> None:
    rows = [
        _row(
            patient="a",
            vaccine="107",
            strategy="2",
            dose="9",
            group="000120",
        )
    ]
    result = process_rows(rows)

    assert result["vvsr_materna"]["total_doses"] == 0
    assert result["nirsevimab"]["total_doses"] == 0
