from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

import release_guardian
from release_guardian import (
    SECRET_PATTERNS,
    _official_url_allowed,
    check_coverage_marts,
    validate_cpf,
)


def test_cpf_checksum_accepts_valid_constructed_value() -> None:
    # Montado em partes para não versionar o número completo como dado literal escaneável.
    value = "".join(["529", "982", "247", "25"])
    assert validate_cpf(value) is True


def test_cpf_checksum_rejects_repeated_digits() -> None:
    assert validate_cpf("1" * 11) is False


def test_secret_patterns_detect_constructed_github_token() -> None:
    value = "ghp" + "_" + ("A" * 24)
    assert any(pattern.search(value) for _, pattern in SECRET_PATTERNS)


def test_secret_patterns_do_not_flag_normal_configuration_text() -> None:
    value = "NEXT_PUBLIC_BASE_PATH=/prevnar"
    assert not any(pattern.search(value) for _, pattern in SECRET_PATTERNS)


def test_official_url_allows_government_subdomains() -> None:
    allowed = {"gov.br"}
    assert _official_url_allowed(
        "https://www.gov.br/saude/pt-br/vacinacao",
        allowed,
    )
    assert _official_url_allowed(
        "https://bvsms.saude.gov.br/bvs/saudelegis/teste.html",
        allowed,
    )
    assert _official_url_allowed(
        "https://iomat.mt.gov.br/documento",
        allowed,
    )


def test_official_url_rejects_external_https_domain() -> None:
    assert not _official_url_allowed(
        "https://example.com/nota-tecnica.pdf",
        {"gov.br"},
    )


def test_official_url_rejects_insecure_scheme() -> None:
    assert not _official_url_allowed(
        "http://www.gov.br/saude",
        {"gov.br"},
    )



def test_guardian_blocks_decision_grade_coverage_without_denominator(tmp_path, monkeypatch) -> None:
    mart = tmp_path / "mart"
    mart.mkdir()
    payload = {
        "denominator_loaded": False,
        "rows": [
            {
                "geography_type": "BR",
                "geography_code": "BR",
                "decision_grade": True,
                "coverage_11_14_pct": 50.0,
                "ages": [],
            }
        ],
    }
    (mart / "mart_menacwy_cohort_coverage.json").write_text(
        __import__("json").dumps(payload),
        encoding="utf-8",
    )
    monkeypatch.setattr(release_guardian, "MART", mart)
    findings = []
    check_coverage_marts(findings, "ci")
    assert any(f.code == "coverage_without_denominator" and f.severity == "error" for f in findings)


def test_guardian_warns_but_does_not_rewrite_coverage_above_100(tmp_path, monkeypatch) -> None:
    mart = tmp_path / "mart"
    mart.mkdir()
    payload = {
        "denominator_loaded": True,
        "rows": [
            {
                "geography_type": "UF",
                "geography_code": "MT",
                "decision_grade": True,
                "coverage_11_14_pct": 104.2,
                "ages": [
                    {
                        "age": 14,
                        "decision_grade": True,
                        "denominator_censo2022": 100,
                        "coverage_pct": 104.2,
                    }
                ],
            }
        ],
    }
    path = mart / "mart_menacwy_cohort_coverage.json"
    path.write_text(__import__("json").dumps(payload), encoding="utf-8")
    monkeypatch.setattr(release_guardian, "MART", mart)
    findings = []
    check_coverage_marts(findings, "release")
    assert any(f.code == "coverage_above_100" and f.severity == "warning" for f in findings)
    assert __import__("json").loads(path.read_text(encoding="utf-8"))["rows"][0]["coverage_11_14_pct"] == 104.2
