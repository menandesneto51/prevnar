from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from release_guardian import SECRET_PATTERNS, _official_url_allowed, validate_cpf


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


def test_current_normative_governance_has_no_blocking_findings() -> None:
    from release_guardian import Finding, check_normative_governance

    findings: list[Finding] = []
    check_normative_governance(findings)
    assert [f for f in findings if f.severity == "error"] == []


def test_guardian_blocks_monitoring_with_pending_registration_mapping(monkeypatch) -> None:
    import release_guardian

    fake_matrix = {
        "summary": {"unresolved_legal_references": []},
        "immunobiologics": [
            {
                "immunobiologic_id": "covid19",
                "monitored": True,
                "pni_codes": ["87"],
                "code_mapping_status": (
                    "immunobiologic_code_confirmed_registration_details_pending"
                ),
                "onboarding_status": "operational_profile_structured_partial_data_mapping",
                "rules": [],
            }
        ],
    }
    monkeypatch.setattr(release_guardian, "build_matrix", lambda: fake_matrix)

    findings: list[release_guardian.Finding] = []
    release_guardian.check_normative_governance(findings)

    assert any(
        finding.code == "monitored_with_incomplete_registration_mapping"
        and finding.severity == "error"
        for finding in findings
    )


def test_current_regulatory_policy_has_no_blocking_findings() -> None:
    from release_guardian import Finding, check_regulatory_compliance_policy

    findings: list[Finding] = []
    check_regulatory_compliance_policy(findings)
    assert [f for f in findings if f.severity == "error"] == []


def test_current_regulatory_watch_contract_has_no_blocking_findings() -> None:
    from release_guardian import Finding, check_regulatory_watch_contract

    findings: list[Finding] = []
    check_regulatory_watch_contract(findings)
    assert [f for f in findings if f.severity == "error"] == []
