"""Governança estruturada de privacidade do PREVNAR."""
from __future__ import annotations

import json
from pathlib import Path

from paths import REF, ROOT

ALLOWED_CLASSIFICATIONS = {"public", "internal", "confidential", "sensitive_health"}
ALLOWED_IDENTIFICATION = {"aggregate", "pseudonymized", "identifiable"}
ALLOWED_ENVIRONMENTS = {"public_static", "institutional_restricted"}
REQUIRED_FIELDS = {
    "source_id", "data_classification", "identification_level",
    "contains_cpf", "contains_cns", "contains_health_data",
    "linkage_allowed", "linkage_purpose", "allowed_environments",
    "public_mart_allowed", "public_output_requirements",
    "retention_policy", "controller", "custodian",
    "legal_basis_refs", "ripd_required",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_privacy_manifest(
    manifest_path: Path | None = None,
    source_registry_path: Path | None = None,
    legal_register_path: Path | None = None,
) -> list[dict]:
    manifest_path = manifest_path or REF / "privacy_manifest.json"
    source_registry_path = source_registry_path or REF / "source_registry.json"
    legal_register_path = legal_register_path or ROOT / "docs" / "legal_register.json"

    manifest = _load(manifest_path)
    source_registry = _load(source_registry_path)
    legal_register = _load(legal_register_path)

    findings: list[dict] = []
    source_ids = {str(x.get("source_id") or "") for x in source_registry.get("sources", [])}
    legal_ids = {str(x.get("id") or "") for x in legal_register.get("acts", [])}
    rows = manifest.get("sources") or []

    seen: set[str] = set()
    for idx, row in enumerate(rows):
        sid = str(row.get("source_id") or "")
        missing = sorted(REQUIRED_FIELDS - set(row))
        if missing:
            findings.append({"severity":"error","code":"privacy_fields_missing","message":f"{sid or idx}: campos ausentes: {', '.join(missing)}"})
            continue
        if not sid:
            findings.append({"severity":"error","code":"privacy_source_id_missing","message":f"Registro #{idx} sem source_id."})
            continue
        if sid in seen:
            findings.append({"severity":"error","code":"privacy_source_duplicate","message":f"source_id duplicado: {sid}."})
        seen.add(sid)

        if row["data_classification"] not in ALLOWED_CLASSIFICATIONS:
            findings.append({"severity":"error","code":"privacy_classification_invalid","message":f"{sid}: classificação inválida."})
        if row["identification_level"] not in ALLOWED_IDENTIFICATION:
            findings.append({"severity":"error","code":"privacy_identification_invalid","message":f"{sid}: nível de identificação inválido."})
        envs = set(row.get("allowed_environments") or [])
        if not envs or not envs.issubset(ALLOWED_ENVIRONMENTS):
            findings.append({"severity":"error","code":"privacy_environment_invalid","message":f"{sid}: ambiente inválido."})

        for field in ("contains_cpf","contains_cns","contains_health_data","linkage_allowed","public_mart_allowed","ripd_required"):
            if not isinstance(row.get(field), bool):
                findings.append({"severity":"error","code":"privacy_boolean_invalid","message":f"{sid}: {field} deve ser booleano."})

        if (row.get("contains_cpf") or row.get("contains_cns")) and "public_static" in envs:
            findings.append({"severity":"error","code":"personal_data_public_environment","message":f"{sid}: fonte com identificador não pode ser processada em public_static."})
        if row.get("identification_level") != "aggregate" and "public_static" in envs:
            findings.append({"severity":"error","code":"nonaggregate_public_environment","message":f"{sid}: dado não agregado não pode ser processado em public_static."})
        if row.get("data_classification") in {"confidential","sensitive_health"} and "public_static" in envs:
            findings.append({"severity":"error","code":"restricted_data_public_environment","message":f"{sid}: dado restrito/sensível não pode ser processado em public_static."})
        if row.get("linkage_allowed") and "institutional_restricted" not in envs:
            findings.append({"severity":"error","code":"linkage_without_restricted_env","message":f"{sid}: linkage requer ambiente institucional restrito."})
        if row.get("linkage_allowed") and not str(row.get("linkage_purpose") or "").strip():
            findings.append({"severity":"error","code":"linkage_purpose_missing","message":f"{sid}: linkage sem finalidade documentada."})
        if not row.get("linkage_allowed") and row.get("linkage_purpose") not in (None, ""):
            findings.append({"severity":"warning","code":"linkage_purpose_without_permission","message":f"{sid}: finalidade de linkage informada, mas linkage_allowed=false."})

        if row.get("public_mart_allowed") and row.get("data_classification") in {"confidential","sensitive_health"}:
            reqs = set(row.get("public_output_requirements") or [])
            if "aggregate_only" not in reqs or "disclosure_risk_review" not in reqs:
                findings.append({"severity":"error","code":"unsafe_public_mart_policy","message":f"{sid}: saída pública de fonte restrita exige aggregate_only e disclosure_risk_review."})

        for ref in row.get("legal_basis_refs") or []:
            if ref not in legal_ids:
                findings.append({"severity":"error","code":"privacy_legal_ref_missing","message":f"{sid}: referência legal ausente: {ref}."})

        if row.get("contains_health_data") and row.get("identification_level") != "aggregate" and not row.get("ripd_required"):
            findings.append({"severity":"error","code":"ripd_gate_missing","message":f"{sid}: dado de saúde não agregado requer gate RIPD."})

    missing_manifest = sorted(source_ids - seen)
    orphan = sorted(seen - source_ids)
    for sid in missing_manifest:
        findings.append({"severity":"error","code":"privacy_source_unclassified","message":f"Fonte sem privacy manifest: {sid}."})
    for sid in orphan:
        findings.append({"severity":"error","code":"privacy_orphan_source","message":f"Privacy manifest órfão: {sid}."})

    return findings
