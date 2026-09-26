from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from build_mart import build_gap, summarize


def _condition(*, situacao: int = 2, cobertura: bool = False) -> dict:
    return {
        "condicao_id": 1,
        "condicao_nt52": "Condição teste",
        "situacao_denominador": situacao,
        "exibe_cobertura": cobertura,
        "ativo_v1": True,
    }


def test_proxy_breakdown_is_not_decision_grade() -> None:
    denoms = [
        {
            "condicao_id": 1,
            "uf": "MT",
            "elegiveis": 100,
            "situacao_denominador": 2,
            "carga_pendente": False,
            "fonte": "estimativa",
        }
    ]
    numerador = {
        "linhas": [
            {
                "condicao_id": 1,
                "uf": "MT",
                "pessoas_vacinadas": 10,
                "evidence_level": "E2",
                "clinical_match_confirmed": False,
            }
        ],
        "sem_cid_na_fonte": True,
        "fixture": False,
    }

    row = build_gap(denoms, numerador, [_condition()])[0]

    assert row["gap"] == 90
    assert row["gap_evidence_level"] == "E2"
    assert row["gap_decision_grade"] is False
    assert row["gap_interpretation"] == "estimativa_nao_decisoria"


def test_confirmed_clinical_match_allows_situacao1_coverage() -> None:
    denoms = [
        {
            "condicao_id": 1,
            "uf": "MT",
            "elegiveis": 100,
            "situacao_denominador": 1,
            "carga_pendente": False,
            "fonte": "cadastro_validado",
        }
    ]
    numerador = {
        "linhas": [
            {
                "condicao_id": 1,
                "uf": "MT",
                "pessoas_vacinadas": 10,
                "evidence_level": "E1",
                "clinical_match_confirmed": True,
            }
        ],
        "sem_cid_na_fonte": False,
        "fixture": False,
    }

    row = build_gap(denoms, numerador, [_condition(situacao=1, cobertura=True)])[0]

    assert row["gap"] == 90
    assert row["gap_evidence_level"] == "E4"
    assert row["gap_decision_grade"] is True
    assert row["exibe_cobertura"] is True
    assert row["cobertura_pct"] == 10.0


def test_fixture_is_never_decision_grade() -> None:
    denoms = [
        {
            "condicao_id": 1,
            "uf": "MT",
            "elegiveis": 100,
            "situacao_denominador": 1,
            "carga_pendente": False,
            "fonte": "cadastro_validado",
        }
    ]
    numerador = {
        "linhas": [
            {
                "condicao_id": 1,
                "uf": "MT",
                "pessoas_vacinadas": 10,
                "evidence_level": "E5",
                "clinical_match_confirmed": False,
            }
        ],
        "fixture": True,
    }

    row = build_gap(denoms, numerador, [_condition(situacao=1, cobertura=True)])[0]

    assert row["gap_evidence_level"] == "E5"
    assert row["gap_decision_grade"] is False
    assert row["exibe_cobertura"] is False
    assert row["cobertura_pct"] is None


def test_national_summary_does_not_publish_unique_person_gap_from_condition_sum() -> None:
    gap_rows = [
        {
            "condicao_id": 1,
            "uf": "MT",
            "elegiveis": 100,
            "pessoas_vacinadas": 10,
            "gap": 90,
            "carga_pendente": False,
            "gap_decision_grade": True,
            "gap_evidence_level": "E3",
        },
        {
            "condicao_id": 2,
            "uf": "MT",
            "elegiveis": 80,
            "pessoas_vacinadas": 5,
            "gap": 75,
            "carga_pendente": False,
            "gap_decision_grade": True,
            "gap_evidence_level": "E3",
        },
    ]
    condicoes = [
        {
            "condicao_id": 1,
            "condicao_nt52": "A",
            "situacao_denominador": 2,
            "exibe_cobertura": False,
            "ativo_v1": True,
        },
        {
            "condicao_id": 2,
            "condicao_nt52": "B",
            "situacao_denominador": 2,
            "exibe_cobertura": False,
            "ativo_v1": True,
        },
    ]
    numerador = {
        "total_pessoas": 12,
        "total_doses": 12,
        "pessoas_por_uf": {"MT": 12},
        "evidence_level_total": "E1",
        "evidence_level_clinical_breakdown": "E1",
        "decision_grade_clinical_breakdown": True,
    }

    summary = summarize(gap_rows, numerador, condicoes)
    nacional = summary["nacional"]

    assert nacional["oportunidades_estimadas"] == 180
    assert nacional["pessoas_vacinadas"] == 12
    assert nacional["gap"] is None
    assert nacional["gap_pessoas"] is None
    assert nacional["gap_pessoas_disponivel"] is False
    assert nacional["gap_aproximado_legado"] == 168
