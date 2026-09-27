from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from menacwy_cohort import (
    _sidra_url,
    aggregate_numerator,
    build_coverage,
    parse_sidra_response,
    row_matches_target_cohort,
)


def _row(patient: str, year: int, age: int, uf: str = "MT") -> dict:
    return {
        "codigo_paciente": patient,
        "codigo_vacina": "74",
        "data_vacina": f"{year}-06-01",
        "numero_idade_paciente": str(age),
        "sigla_uf_paciente": uf,
        "codigo_municipio_paciente": "510340",
    }


def test_cohort_year_alignment_for_age_14_in_2026() -> None:
    assert row_matches_target_cohort(vaccination_year=2023, observed_age=11, reference_year=2026, target_age=14)
    assert row_matches_target_cohort(vaccination_year=2024, observed_age=12, reference_year=2026, target_age=14)
    assert row_matches_target_cohort(vaccination_year=2025, observed_age=13, reference_year=2026, target_age=14)
    assert row_matches_target_cohort(vaccination_year=2026, observed_age=14, reference_year=2026, target_age=14)
    assert not row_matches_target_cohort(vaccination_year=2025, observed_age=12, reference_year=2026, target_age=14)


def test_numerator_deduplicates_same_person_across_cohort_years() -> None:
    rows = [
        _row("same", 2023, 11),
        _row("same", 2024, 12),
        _row("other", 2026, 14),
    ]
    buckets = aggregate_numerator(rows, reference_year=2026)
    assert len(buckets[("BR", "BR", 14)]) == 2
    assert len(buckets[("UF", "MT", 14)]) == 2


def test_coverage_requires_denominator() -> None:
    buckets = aggregate_numerator([_row("a", 2026, 11)], reference_year=2026)
    out = build_coverage(buckets, {}, reference_year=2026)
    br = next(x for x in out["rows"] if x["geography_type"] == "BR")
    assert br["coverage_11_14_pct"] is None
    assert br["decision_grade"] is False
    assert out["denominator_loaded"] is False


def test_age_specific_and_group_coverage_with_complete_denominator() -> None:
    rows = [
        _row("a", 2026, 11),
        _row("b", 2025, 11),
        _row("b", 2026, 12),
        _row("c", 2024, 11),
        _row("c", 2025, 12),
        _row("c", 2026, 13),
        _row("d", 2023, 11),
        _row("d", 2024, 12),
        _row("d", 2025, 13),
        _row("d", 2026, 14),
    ]
    buckets = aggregate_numerator(rows, reference_year=2026)
    denoms = {
        ("BR", "BR", 11): 10,
        ("BR", "BR", 12): 10,
        ("BR", "BR", 13): 10,
        ("BR", "BR", 14): 10,
    }
    out = build_coverage(buckets, denoms, reference_year=2026)
    br = next(x for x in out["rows"] if x["geography_type"] == "BR")
    ages = {x["age"]: x for x in br["ages"]}
    assert ages[11]["coverage_pct"] == 10.0
    assert ages[12]["coverage_pct"] == 10.0
    assert ages[13]["coverage_pct"] == 10.0
    assert ages[14]["coverage_pct"] == 10.0
    assert br["coverage_11_14_pct"] == 10.0
    assert br["decision_grade"] is True


def test_sidra_url_uses_official_age_categories() -> None:
    url = _sidra_url("n3")
    assert "/t/9606/" in url
    assert "/c287/6568,6569,6570,6571" in url
    assert "/c86/0/c2/0/" in url


def test_sidra_parser_normalizes_age_and_geography() -> None:
    payload = [
        {
            "V": "Valor",
            "D1C": "Unidade da Federação (Código)",
            "D1N": "Unidade da Federação",
            "D5C": "Idade (Código)",
            "D5N": "Idade",
        },
        {"V": "100", "D1C": "51", "D1N": "Mato Grosso", "D5C": "6568", "D5N": "11 anos"},
        {"V": "110", "D1C": "51", "D1N": "Mato Grosso", "D5C": "6569", "D5N": "12 anos"},
        {"V": "120", "D1C": "51", "D1N": "Mato Grosso", "D5C": "6570", "D5N": "13 anos"},
        {"V": "130", "D1C": "51", "D1N": "Mato Grosso", "D5C": "6571", "D5N": "14 anos"},
    ]
    rows = parse_sidra_response(payload, geography_type="UF")
    assert [r["age"] for r in rows] == [11, 12, 13, 14]
    assert [r["population"] for r in rows] == [100, 110, 120, 130]
    assert all(r["geography_code"] == "51" for r in rows)
    assert all(r["census_year"] == 2022 for r in rows)
