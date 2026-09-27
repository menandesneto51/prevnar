"""Prontidão de mapeamento de registro vacinal no PREVNAR."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from paths import MART, REF, ROOT

REGISTRY = REF / "registration_mapping_registry.json"
IMMUNOBIOLOGICS = REF / "immunobiologic_registry.json"
WEB_PUBLIC = ROOT / "web" / "public" / "data"
VALID_STATUSES = {"confirmed", "partial", "pending", "not_required"}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_mapping(item: dict[str, Any]) -> dict[str, Any]:
    required = list(item.get("required_dimensions") or [])
    dimensions = item.get("dimensions") or {}

    blocking: list[str] = []
    confirmed_required = 0
    rows: list[dict[str, Any]] = []

    for name, detail in dimensions.items():
        status = str(detail.get("status") or "")
        if status not in VALID_STATUSES:
            raise ValueError(
                f"{item.get('immunobiologic_id')}: status inválido em {name}: {status}"
            )
        is_required = name in required
        if is_required and status == "confirmed":
            confirmed_required += 1
        elif is_required:
            blocking.append(name)

        rows.append(
            {
                "dimension": name,
                "required": is_required,
                "status": status,
                "values": detail.get("values") or [],
                "evidence_type": detail.get("evidence_type"),
                "note": detail.get("note"),
            }
        )

    missing_required = sorted(set(required) - set(dimensions))
    blocking.extend(missing_required)

    readiness_pct = (
        round(100 * confirmed_required / len(required), 1)
        if required
        else 100.0
    )

    return {
        "immunobiologic_id": item["immunobiologic_id"],
        "required_dimensions": required,
        "confirmed_required_dimensions": confirmed_required,
        "required_dimension_count": len(required),
        "readiness_pct": readiness_pct,
        "etl_ready": not blocking,
        "blocking_dimensions": sorted(set(blocking)),
        "dimensions": sorted(rows, key=lambda row: row["dimension"]),
    }


def build_registration_readiness() -> dict[str, Any]:
    mapping = _load(REGISTRY)
    immunobiologic_payload = _load(IMMUNOBIOLOGICS)
    immunobiologics = {
        str(row["immunobiologic_id"]): row
        for row in immunobiologic_payload.get("immunobiologics", [])
    }

    rows: list[dict[str, Any]] = []
    for item in mapping.get("immunobiologics") or []:
        row = evaluate_mapping(item)
        registry_item = immunobiologics.get(row["immunobiologic_id"])
        if not registry_item:
            raise ValueError(
                f"Mapping sem imunobiológico correspondente: {row['immunobiologic_id']}"
            )
        row["display"] = registry_item.get("display")
        row["monitored"] = bool(registry_item.get("monitored"))
        row["onboarding_status"] = registry_item.get("onboarding_status")
        row["code_mapping_status"] = registry_item.get("code_mapping_status")
        rows.append(row)

    rows.sort(key=lambda row: (not row["monitored"], row["display"] or row["immunobiologic_id"]))

    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mapping_version": mapping.get("version"),
        "summary": {
            "immunobiologics": len(rows),
            "etl_ready": sum(1 for row in rows if row["etl_ready"]),
            "blocked": sum(1 for row in rows if not row["etl_ready"]),
            "monitored": sum(1 for row in rows if row["monitored"]),
            "monitored_not_ready": [
                row["immunobiologic_id"]
                for row in rows
                if row["monitored"] and not row["etl_ready"]
            ],
        },
        "items": rows,
        "interpretation": (
            "Prontidão de registro mede apenas completude do mapeamento transacional. "
            "Não equivale à completude da regra clínica."
        ),
    }


def write_registration_readiness() -> dict[str, Any]:
    payload = build_registration_readiness()
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    MART.mkdir(parents=True, exist_ok=True)
    (MART / "registration_readiness.json").write_text(rendered, encoding="utf-8")
    WEB_PUBLIC.mkdir(parents=True, exist_ok=True)
    (WEB_PUBLIC / "registration_readiness.json").write_text(rendered, encoding="utf-8")
    return payload


def main() -> int:
    payload = write_registration_readiness()
    print(
        "Registration readiness:",
        f"ready={payload['summary']['etl_ready']}",
        f"blocked={payload['summary']['blocked']}",
        f"monitored_not_ready={payload['summary']['monitored_not_ready']}",
    )
    return 0 if not payload["summary"]["monitored_not_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
