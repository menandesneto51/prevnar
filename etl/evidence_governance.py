"""Governança estruturada de evidências do PREVNAR."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from paths import REF

REGISTRY_PATH = REF / "evidence_registry.json"

CANONICAL_CLASSES = {
    "legislation",
    "federal_normative",
    "official_terminology",
    "official_registration_artifact",
    "state_normative",
    "official_manual",
    "official_operational",
}
NON_NATIONAL_CLASSES = {
    "supplementary_official",
    "institutional_authorized",
    "secondary",
}


def load_evidence_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_evidence_registry(
    payload: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    data = payload or load_evidence_registry()
    findings: list[dict[str, str]] = []
    seen: set[str] = set()

    rows = data.get("evidence") or []
    if not rows:
        findings.append({
            "severity": "error",
            "code": "evidence_registry_empty",
            "message": "Registro de evidências sem entradas.",
        })
        return findings

    for index, row in enumerate(rows):
        eid = str(row.get("evidence_id") or "").strip()
        if not eid:
            findings.append({
                "severity": "error",
                "code": "evidence_id_missing",
                "message": f"Evidência #{index} sem evidence_id.",
            })
            continue
        if eid in seen:
            findings.append({
                "severity": "error",
                "code": "evidence_id_duplicate",
                "message": f"evidence_id duplicado: {eid}.",
            })
        seen.add(eid)

        evidence_class = str(row.get("evidence_class") or "").strip()
        authority_level = str(row.get("authority_level") or "").strip()
        authority_scope = str(row.get("authority_scope") or "").strip()

        if not evidence_class or not authority_level or not authority_scope:
            findings.append({
                "severity": "error",
                "code": "evidence_authority_incomplete",
                "message": (
                    f"{eid}: evidence_class, authority_level e authority_scope "
                    "são obrigatórios."
                ),
            })

        if row.get("canonical") is True and row.get("official") is not True:
            findings.append({
                "severity": "error",
                "code": "canonical_evidence_not_official",
                "message": f"{eid}: evidência canônica deve ser oficial.",
            })

        if (
            evidence_class in NON_NATIONAL_CLASSES
            and row.get("can_define_national_rule") is True
        ):
            findings.append({
                "severity": "error",
                "code": "noncanonical_source_defines_national_rule",
                "message": (
                    f"{eid}: classe {evidence_class} não pode definir regra nacional."
                ),
            })

        if (
            row.get("can_define_national_rule") is True
            and authority_level != "federal"
        ):
            findings.append({
                "severity": "error",
                "code": "nonfederal_source_defines_national_rule",
                "message": (
                    f"{eid}: apenas autoridade federal pode definir regra nacional "
                    "neste registry."
                ),
            })

        if row.get("canonical") is True and evidence_class not in CANONICAL_CLASSES:
            findings.append({
                "severity": "error",
                "code": "invalid_canonical_evidence_class",
                "message": (
                    f"{eid}: classe {evidence_class} não é elegível a canônica."
                ),
            })

        if evidence_class == "institutional_authorized" and not row.get("access"):
            findings.append({
                "severity": "error",
                "code": "institutional_evidence_access_missing",
                "message": f"{eid}: fonte institucional deve declarar access.",
            })

        if row.get("official_url") is None and evidence_class != "institutional_authorized":
            findings.append({
                "severity": "warning",
                "code": "official_url_missing",
                "message": f"{eid}: fonte sem official_url.",
            })

    return findings


def evidence_by_id(evidence_id: str) -> dict[str, Any] | None:
    payload = load_evidence_registry()
    return next(
        (
            row
            for row in payload.get("evidence") or []
            if row.get("evidence_id") == evidence_id
        ),
        None,
    )


def can_define_national_rule(evidence_id: str) -> bool:
    row = evidence_by_id(evidence_id)
    return bool(row and row.get("can_define_national_rule") is True)
