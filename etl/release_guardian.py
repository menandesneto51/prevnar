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
from build_normative_matrix import build_matrix


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


def check_sies_logistics_contract(findings: list[Finding]) -> None:
    contract_path = REF / "sies_transition_source_contract.json"
    if not contract_path.exists():
        _finding(
            findings,
            "error",
            "sies_contract_missing",
            "Contrato SIES distribuição/estoque ausente.",
            contract_path,
        )
        return

    try:
        contract = _load_json(contract_path)
    except Exception as exc:  # noqa: BLE001
        _finding(
            findings,
            "error",
            "sies_contract_invalid",
            f"Contrato SIES inválido: {exc}",
            contract_path,
        )
        return

    sources = contract.get("sources") or {}
    public = sources.get("sies_public_distribution") or {}
    institutional = sources.get("sies_institutional_inventory") or {}

    prohibited = set(public.get("prohibited_inferences") or [])
    if "current_stock_balance" not in prohibited:
        _finding(
            findings,
            "error",
            "sies_public_stock_inference_not_blocked",
            "Contrato público SIES deve proibir inferência de saldo de estoque.",
            contract_path,
        )
    if public.get("decision_grade_for_current_inventory") is not False:
        _finding(
            findings,
            "error",
            "sies_public_inventory_decision_grade",
            "SIES público não pode ser decision-grade para saldo de estoque atual.",
            contract_path,
        )

    forbidden = {str(x).lower() for x in institutional.get("forbidden_personal_fields") or []}
    if not {"cpf", "cns"}.issubset(forbidden):
        _finding(
            findings,
            "error",
            "sies_personal_fields_guard_missing",
            "Contrato institucional deve proibir ao menos CPF e CNS.",
            contract_path,
        )

    legacy = ROOT / "etl" / "extract_nacional.py"
    if legacy.exists():
        text = legacy.read_text(encoding="utf-8", errors="ignore")
        if "_create_unverified_context" in text:
            _finding(
                findings,
                "error",
                "unverified_tls_context",
                "Extrator legado contém TLS sem verificação.",
                legacy,
            )
        if "por_uf_seed" in text or "Fallback seed distribuídas" in text:
            _finding(
                findings,
                "error",
                "sies_seed_fallback_present",
                "Extrator SIES não pode publicar seed como dado observado.",
                legacy,
            )


def check_regulatory_compliance_policy(findings: list[Finding]) -> None:
    policy_path = REF / "regulatory_compliance_policy.json"
    legal_path = ROOT / "docs" / "legal_register.json"

    if not policy_path.exists():
        _finding(
            findings,
            "error",
            "regulatory_policy_missing",
            "Política de benchmark regulatório ausente.",
            policy_path,
        )
        return

    try:
        policy = _load_json(policy_path)
        legal = _load_json(legal_path)
    except Exception as exc:  # noqa: BLE001
        _finding(
            findings,
            "error",
            "regulatory_policy_invalid",
            f"Falha ao carregar política/registro legal: {exc}",
            policy_path,
        )
        return

    benchmark = (
        policy.get("benchmarks", {})
        .get("technical_revision_adaptation_days")
    )
    if benchmark != 15:
        _finding(
            findings,
            "error",
            "regulatory_benchmark_changed",
            "Benchmark de revisão técnica deve permanecer em 15 dias enquanto baseado na Portaria 5.663/2024.",
            policy_path,
        )

    applicability = policy.get("applicability") or {}
    if applicability.get("prevnar_current_role") != "analytical_monitoring":
        _finding(
            findings,
            "error",
            "regulatory_applicability_ambiguous",
            "Papel atual do PREVNAR deve permanecer explicitamente analytical_monitoring.",
            policy_path,
        )
    if applicability.get("prevnar_treatment") != "internal_regulatory_benchmark":
        _finding(
            findings,
            "error",
            "regulatory_benchmark_not_internal",
            "Prazo regulatório deve ser tratado como benchmark interno no PREVNAR analítico.",
            policy_path,
        )

    portaria = next(
        (
            act
            for act in legal.get("acts", [])
            if act.get("id") == "portaria_5663_2024_rnds_vacinacao"
        ),
        None,
    )
    if not portaria:
        _finding(
            findings,
            "error",
            "portaria_5663_missing",
            "Portaria GM/MS 5.663/2024 ausente do registro legal.",
            legal_path,
        )
        return

    if portaria.get("effective_from") != "2025-03-04":
        _finding(
            findings,
            "error",
            "portaria_5663_effective_date_invalid",
            "Vigência registrada da Portaria 5.663/2024 deve refletir os 120 dias do art. 4º.",
            legal_path,
        )

    provisions = portaria.get("provisions") or {}
    expected = {
        "rnds_online_submission_hours": 24,
        "rnds_offline_submission_days": 15,
        "system_adaptation_after_technical_revision_days": 15,
        "dpni_new_immunobiologic_registration_rules_days": 15,
    }
    for key, value in expected.items():
        if provisions.get(key) != value:
            _finding(
                findings,
                "error",
                "portaria_5663_provision_mismatch",
                f"Provisão {key} deve ser {value}.",
                legal_path,
            )


def check_regulatory_watch_contract(findings: list[Finding]) -> None:
    baseline_path = REF / "regulatory_watch_baseline.json"
    workflow_path = ROOT / ".github" / "workflows" / "regulatory-watch.yml"

    if not baseline_path.exists():
        _finding(
            findings,
            "error",
            "regulatory_watch_baseline_missing",
            "Baseline do Regulatory Watch ausente.",
            baseline_path,
        )
        return

    try:
        baseline = _load_json(baseline_path)
    except Exception as exc:  # noqa: BLE001
        _finding(
            findings,
            "error",
            "regulatory_watch_baseline_invalid",
            f"Baseline regulatório inválido: {exc}",
            baseline_path,
        )
        return

    targets = {
        str(row.get("target_id")): row
        for row in baseline.get("targets") or []
    }
    required_targets = {
        "rules_entry",
        "br_immunobiologic",
        "br_vaccination_strategy",
    }
    missing = sorted(required_targets - set(targets))
    if missing:
        _finding(
            findings,
            "error",
            "regulatory_watch_targets_missing",
            "Alvos obrigatórios ausentes: " + ", ".join(missing),
            baseline_path,
        )

    rules_expected = (targets.get("rules_entry") or {}).get("expected") or {}
    if rules_expected.get("latest_version") != 4:
        _finding(
            findings,
            "error",
            "regulatory_watch_rules_baseline_changed",
            "Baseline de Regras de Entrada deve permanecer na versão 4 até revisão humana.",
            baseline_path,
        )

    immuno_expected = (targets.get("br_immunobiologic") or {}).get("expected") or {}
    immuno_codes = immuno_expected.get("required_code_displays") or {}
    if immuno_codes.get("87") != "COVID-19 PFIZER - COMIRNATY":
        _finding(
            findings,
            "error",
            "regulatory_watch_code87_missing",
            "Baseline deve acompanhar código 87 da Comirnaty.",
            baseline_path,
        )

    strategy_expected = (targets.get("br_vaccination_strategy") or {}).get("expected") or {}
    absent = strategy_expected.get("tracked_absent_code_displays") or {}
    if absent.get("14") != "Vacinação Escolar":
        _finding(
            findings,
            "error",
            "regulatory_watch_strategy14_exception_missing",
            "Baseline deve acompanhar a ausência terminológica da estratégia 14.",
            baseline_path,
        )

    if not workflow_path.exists():
        _finding(
            findings,
            "error",
            "regulatory_watch_workflow_missing",
            "Workflow agendado do Regulatory Watch ausente.",
            workflow_path,
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


def check_normative_governance(findings: list[Finding]) -> None:
    try:
        matrix = build_matrix()
    except Exception as exc:  # noqa: BLE001
        _finding(
            findings,
            "error",
            "normative_matrix_invalid",
            f"Falha ao construir matriz normativa: {exc}",
            REF / "normative_rules.json",
        )
        return

    unresolved = matrix.get("summary", {}).get("unresolved_legal_references") or []
    for act_id in unresolved:
        _finding(
            findings,
            "error",
            "normative_legal_reference_unresolved",
            f"Referência legal não resolvida: {act_id}.",
            REF / "normative_rules.json",
        )

    for item in matrix.get("immunobiologics") or []:
        iid = str(item.get("immunobiologic_id") or "")
        if item.get("monitored") and not (item.get("pni_codes") or []):
            _finding(
                findings,
                "error",
                "monitored_without_pni_code",
                f"Imunobiológico monitorado sem código nacional: {iid}.",
                REF / "immunobiologic_registry.json",
            )

        mapping_status = str(item.get("code_mapping_status") or "").lower()
        onboarding_status = str(item.get("onboarding_status") or "").lower()
        if item.get("monitored") and (
            "pending" in mapping_status
            or "partial_data_mapping" in onboarding_status
        ):
            _finding(
                findings,
                "error",
                "monitored_with_incomplete_registration_mapping",
                (
                    f"Imunobiológico {iid} está monitorado com mapeamento de registro "
                    f"incompleto: {item.get('code_mapping_status') or item.get('onboarding_status')}."
                ),
                REF / "immunobiologic_registry.json",
            )

        for rule in item.get("rules") or []:
            if rule.get("status") != "active":
                continue

            rid = str(rule.get("rule_id") or "")
            if not rule.get("effective_from"):
                _finding(
                    findings,
                    "error",
                    "active_rule_without_effective_from",
                    f"Regra ativa sem effective_from: {rid}.",
                    REF / "normative_rules.json",
                )

            scope = rule.get("geographic_scope") or {}
            scope_type = scope.get("type")
            scope_codes = scope.get("codes") or []
            if not scope_type:
                _finding(
                    findings,
                    "error",
                    "active_rule_without_scope",
                    f"Regra ativa sem geographic_scope.type: {rid}.",
                    REF / "normative_rules.json",
                )
            elif scope_type == "national" and "BR" not in scope_codes:
                _finding(
                    findings,
                    "error",
                    "national_rule_without_br_scope",
                    f"Regra nacional sem código BR: {rid}.",
                    REF / "normative_rules.json",
                )
            elif scope_type != "national" and not scope_codes:
                _finding(
                    findings,
                    "error",
                    "territorial_rule_without_codes",
                    f"Regra territorial sem códigos de escopo: {rid}.",
                    REF / "normative_rules.json",
                )

            if not (rule.get("normative_acts") or []):
                _finding(
                    findings,
                    "error",
                    "active_rule_without_normative_act",
                    f"Regra ativa sem normative_acts: {rid}.",
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
    check_sies_logistics_contract(findings)
    check_regulatory_compliance_policy(findings)
    check_regulatory_watch_contract(findings)
    check_source_registry(findings)
    check_vaccine_registry(findings)
    check_normative_governance(findings)
    check_indicator_catalog(findings)
    check_dashboard_runtime(findings, mode)
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
