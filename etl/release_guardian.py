"""Release Guardian do PREVNAR.

Executa gates estáticos e de qualidade antes de uma publicação.

Modos:
- ci: valida estrutura e segurança; ausência de metadados runtime gera warning.
- release: exige metadados runtime e bloqueia fontes críticas desatualizadas.

O Guardian não substitui revisão epidemiológica, jurídica ou institucional.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from paths import MART, REF, ROOT
from vaccine_rules import validate_registry_integrity


ALLOWED_EVIDENCE = {"E1", "E2", "E3", "E4", "E5"}
TEXT_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".txt",
    ".yml", ".yaml", ".toml", ".ini", ".env", ".csv",
}
SKIP_PARTS = {
    ".git", ".next", "node_modules", ".venv", "venv", "__pycache__",
}
MAX_SCAN_BYTES = 2_000_000

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("github_pat", re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("bearer_token", re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]{24,}", re.IGNORECASE)),
]

CPF_PATTERN = re.compile(r"(?<!\d)(\d{3})[.\s-]?(\d{3})[.\s-]?(\d{3})[-\s]?(\d{2})(?!\d)")
CNS_CONTEXT_PATTERN = re.compile(
    r"(?:\bcns\b|cart[aã]o\s+(?:nacional\s+de\s+)?sa[uú]de)"
    r"[^\n\d]{0,30}(\d{15})(?!\d)",
    re.IGNORECASE,
)


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    path: str | None = None


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _finding(
    findings: list[Finding],
    severity: str,
    code: str,
    message: str,
    path: Path | str | None = None,
) -> None:
    findings.append(
        Finding(
            severity=severity,
            code=code,
            message=message,
            path=str(path) if path else None,
        )
    )


def validate_cpf(value: str) -> bool:
    digits = re.sub(r"\D", "", value)
    if len(digits) != 11 or len(set(digits)) == 1:
        return False

    nums = [int(x) for x in digits]
    first = sum(nums[i] * (10 - i) for i in range(9))
    d1 = (first * 10 % 11) % 10
    if d1 != nums[9]:
        return False
    second = sum(nums[i] * (11 - i) for i in range(10))
    d2 = (second * 10 % 11) % 10
    return d2 == nums[10]


def iter_text_files(root: Path = ROOT) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if any(part in SKIP_PARTS for part in rel.parts):
            continue
        if len(rel.parts) >= 2 and rel.parts[0] == "data" and rel.parts[1] == "raw":
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            if path.stat().st_size > MAX_SCAN_BYTES:
                continue
        except OSError:
            continue
        yield path


def _official_url_allowed(url: str, allowed_domains: set[str]) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    host = parsed.hostname.lower().rstrip(".")
    return any(
        host == domain or host.endswith("." + domain)
        for domain in allowed_domains
    )


def check_legal_register(findings: list[Finding]) -> None:
    path = ROOT / "docs" / "legal_register.json"
    if not path.exists():
        _finding(findings, "error", "legal_register_missing", "Registro legal ausente.", path)
        return

    try:
        payload = _load_json(path)
    except Exception as exc:  # noqa: BLE001
        _finding(findings, "error", "legal_register_invalid", f"JSON inválido: {exc}", path)
        return

    acts = payload.get("acts") or []
    if not acts:
        _finding(findings, "error", "legal_register_empty", "Registro legal sem atos.", path)
        return

    allowed_domains = {
        str(x).lower().strip()
        for x in (payload.get("official_source_domains") or [])
        if str(x).strip()
    }
    if not allowed_domains:
        _finding(
            findings,
            "error",
            "official_domains_missing",
            "Registro legal sem lista de domínios oficiais autorizados.",
            path,
        )

    seen: set[str] = set()
    required = {"id", "type", "number", "scope", "official_url"}
    for idx, act in enumerate(acts):
        missing = sorted(required - set(act))
        if missing:
            _finding(
                findings,
                "error",
                "legal_act_incomplete",
                f"Ato #{idx} sem campos: {', '.join(missing)}.",
                path,
            )
            continue
        act_id = str(act["id"])
        if act_id in seen:
            _finding(findings, "error", "legal_act_duplicate", f"ID duplicado: {act_id}.", path)
        seen.add(act_id)
        url = str(act.get("official_url") or "")
        if not url.startswith("https://"):
            _finding(
                findings,
                "error",
                "legal_url_not_https",
                f"URL oficial inválida para {act_id}: {url}",
                path,
            )
        elif allowed_domains and not _official_url_allowed(url, allowed_domains):
            _finding(
                findings,
                "error",
                "legal_url_untrusted_domain",
                f"URL de {act_id} não pertence a domínio oficial autorizado: {url}",
                path,
            )


def check_source_registry(findings: list[Finding]) -> None:
    path = REF / "source_registry.json"
    if not path.exists():
        _finding(findings, "error", "source_registry_missing", "Source registry ausente.", path)
        return
    try:
        payload = _load_json(path)
    except Exception as exc:  # noqa: BLE001
        _finding(findings, "error", "source_registry_invalid", f"JSON inválido: {exc}", path)
        return

    rows = payload.get("sources") or []
    seen: set[str] = set()
    for row in rows:
        sid = str(row.get("source_id") or "")
        if not sid:
            _finding(findings, "error", "source_id_missing", "Fonte sem source_id.", path)
            continue
        if sid in seen:
            _finding(findings, "error", "source_id_duplicate", f"source_id duplicado: {sid}.", path)
        seen.add(sid)
        try:
            attention = int(row["attention_after_days"])
            stale = int(row["stale_after_days"])
        except (KeyError, TypeError, ValueError):
            _finding(
                findings,
                "error",
                "freshness_threshold_invalid",
                f"Limites de freshness inválidos para {sid}.",
                path,
            )
            continue
        if attention < 0 or stale <= attention:
            _finding(
                findings,
                "error",
                "freshness_threshold_order",
                f"Esperado 0 <= attention < stale para {sid}.",
                path,
            )


def check_vaccine_registry(findings: list[Finding]) -> None:
    try:
        errors = validate_registry_integrity()
    except Exception as exc:  # noqa: BLE001
        _finding(
            findings,
            "error",
            "vaccine_registry_invalid",
            f"Falha ao validar vaccine/normative registry: {exc}",
        )
        return
    for message in errors:
        _finding(
            findings,
            "error",
            "vaccine_registry_reference_error",
            message,
            REF / "normative_rules.json",
        )


def check_indicator_catalog(findings: list[Finding]) -> None:
    path = REF / "indicadores_nacionais.json"
    if not path.exists():
        _finding(findings, "error", "indicator_catalog_missing", "Catálogo de indicadores ausente.", path)
        return
    payload = _load_json(path)
    if not payload.get("versao"):
        _finding(findings, "error", "method_version_missing", "Catálogo sem versão metodológica.", path)

    seen: set[str] = set()
    for ind in payload.get("indicadores") or []:
        iid = str(ind.get("id") or "")
        if not iid:
            _finding(findings, "error", "indicator_id_missing", "Indicador sem id.", path)
            continue
        if iid in seen:
            _finding(findings, "error", "indicator_id_duplicate", f"Indicador duplicado: {iid}.", path)
        seen.add(iid)

        decision_grade = ind.get("decision_grade")
        if not isinstance(decision_grade, bool):
            _finding(
                findings,
                "error",
                "decision_grade_missing",
                f"Indicador {iid} sem decision_grade booleano.",
                path,
            )
        evidence = ind.get("evidence_level")
        if evidence is not None and evidence not in ALLOWED_EVIDENCE:
            _finding(
                findings,
                "error",
                "evidence_level_invalid",
                f"Indicador {iid} com evidence_level inválido: {evidence}.",
                path,
            )
        if decision_grade and evidence in (None, "E5"):
            _finding(
                findings,
                "error",
                "decision_grade_unsafe",
                f"Indicador {iid} é decision-grade sem evidência válida.",
                path,
            )


def check_dashboard_runtime(findings: list[Finding], mode: str) -> None:
    path = MART / "dashboard.json"
    if not path.exists():
        sev = "error" if mode == "release" else "warning"
        _finding(findings, sev, "dashboard_missing", "Mart dashboard.json ausente.", path)
        return

    payload = _load_json(path)
    nacional = payload.get("nacional") or {}
    if nacional.get("fixture"):
        sev = "error" if mode == "release" else "warning"
        _finding(findings, sev, "fixture_active", "Numerador demonstrativo ativo no dashboard.", path)

    quality = payload.get("qualidade") or {}
    freshness = quality.get("freshness")
    if not freshness:
        sev = "error" if mode == "release" else "warning"
        _finding(
            findings,
            sev,
            "freshness_missing",
            "Mart ainda não possui metadados de freshness; executar rebuild v2.",
            path,
        )
    else:
        for source_id, item in freshness.items():
            if not isinstance(item, dict):
                continue
            status = item.get("status")
            critical = bool(item.get("critical_for_decision"))
            if critical and status == "desatualizado":
                _finding(
                    findings,
                    "error",
                    "critical_source_stale",
                    f"Fonte crítica {source_id} está desatualizada (ref. {item.get('reference_period')}).",
                    path,
                )
            elif critical and status in ("desconhecido", None):
                sev = "error" if mode == "release" else "warning"
                _finding(
                    findings,
                    sev,
                    "critical_source_freshness_unknown",
                    f"Freshness desconhecida para fonte crítica {source_id}.",
                    path,
                )

    for row in payload.get("por_condicao") or []:
        if row.get("gap_decision_grade") and row.get("gap_evidence_level") == "E5":
            _finding(
                findings,
                "error",
                "e5_decision_metric",
                f"Condição {row.get('condicao_id')} marcada como decisória com E5.",
                path,
            )


def check_coverage_marts(findings: list[Finding], mode: str) -> None:
    path = MART / "mart_menacwy_cohort_coverage.json"
    if not path.exists():
        return

    try:
        payload = _load_json(path)
    except Exception as exc:  # noqa: BLE001
        _finding(
            findings,
            "error",
            "coverage_mart_invalid",
            f"Mart de cobertura MenACWY inválido: {exc}",
            path,
        )
        return

    denominator_loaded = bool(payload.get("denominator_loaded"))
    for row in payload.get("rows") or []:
        geo = f"{row.get('geography_type')}:{row.get('geography_code')}"
        if row.get("decision_grade") and not denominator_loaded:
            _finding(
                findings,
                "error",
                "coverage_without_denominator",
                f"{geo} marcado decision-grade sem denominador carregado.",
                path,
            )
        coverage = row.get("coverage_11_14_pct")
        if coverage is not None and float(coverage) > 100:
            _finding(
                findings,
                "warning",
                "coverage_above_100",
                (
                    f"{geo} possui cobertura 11–14 >100% ({coverage}%). "
                    "Preservar o valor e investigar denominador, migração, duplicidade ou registro."
                ),
                path,
            )
        for age in row.get("ages") or []:
            if age.get("decision_grade") and age.get("denominator_censo2022") in (None, 0):
                _finding(
                    findings,
                    "error",
                    "age_coverage_without_denominator",
                    f"{geo} idade {age.get('age')} decision-grade sem denominador válido.",
                    path,
                )
            age_coverage = age.get("coverage_pct")
            if age_coverage is not None and float(age_coverage) > 100:
                _finding(
                    findings,
                    "warning",
                    "age_coverage_above_100",
                    f"{geo} idade {age.get('age')} cobertura >100% ({age_coverage}%).",
                    path,
                )


def check_secrets_and_personal_data(findings: list[Finding]) -> None:
    for path in iter_text_files():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = path.relative_to(ROOT)

        for code, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                _finding(
                    findings,
                    "error",
                    f"secret_{code}",
                    f"Possível segredo detectado em {rel}.",
                    rel,
                )

        for match in CPF_PATTERN.finditer(text):
            candidate = "".join(match.groups())
            if validate_cpf(candidate):
                _finding(
                    findings,
                    "error",
                    "cpf_detected",
                    f"Possível CPF válido versionado em {rel}.",
                    rel,
                )
                break

        if CNS_CONTEXT_PATTERN.search(text):
            _finding(
                findings,
                "error",
                "cns_detected",
                f"Possível CNS versionado em {rel}.",
                rel,
            )


def check_mutable_api_routes(findings: list[Finding], mode: str) -> None:
    api_root = ROOT / "web" / "src" / "app" / "api"
    if not api_root.exists():
        return
    server_side = os.environ.get("PREVNAR_SERVER_SIDE_DEPLOY") == "1"
    auth_markers = (
        "authorization",
        "x-api-key",
        "requireauth",
        "getserversession",
        "auth(",
        "authorizemutablerequest",
    )
    mutating = re.compile(r"export\s+async\s+function\s+(POST|PUT|PATCH|DELETE)\b")

    for path in api_root.rglob("route.ts"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if not mutating.search(text):
            continue
        lower = text.lower()
        if any(marker in lower for marker in auth_markers):
            continue
        severity = "error" if server_side and mode == "release" else "warning"
        _finding(
            findings,
            severity,
            "mutable_route_without_auth",
            (
                "Rota mutável sem autenticação detectável. "
                "No GitHub Pages as APIs são removidas; deploy server-side exige proteção."
            ),
            path.relative_to(ROOT),
        )


def run_guardian(mode: str = "ci") -> tuple[list[Finding], dict]:
    findings: list[Finding] = []
    check_legal_register(findings)
    check_source_registry(findings)
    check_vaccine_registry(findings)
    check_indicator_catalog(findings)
    check_dashboard_runtime(findings, mode)
    check_coverage_marts(findings, mode)
    check_secrets_and_personal_data(findings)
    check_mutable_api_routes(findings, mode)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "errors": sum(1 for f in findings if f.severity == "error"),
        "warnings": sum(1 for f in findings if f.severity == "warning"),
        "findings": [asdict(f) for f in findings],
        "approved": not any(f.severity == "error" for f in findings),
    }

    out = MART / "_meta" / "release_guardian.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return findings, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="PREVNAR Release Guardian")
    parser.add_argument("--mode", choices=["ci", "release"], default="ci")
    args = parser.parse_args()

    findings, summary = run_guardian(args.mode)
    for finding in findings:
        loc = f" [{finding.path}]" if finding.path else ""
        print(f"{finding.severity.upper()} {finding.code}{loc}: {finding.message}")
    print(
        f"Release Guardian: approved={summary['approved']} "
        f"errors={summary['errors']} warnings={summary['warnings']} mode={args.mode}"
    )
    return 0 if summary["approved"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
