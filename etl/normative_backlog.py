"""Backlog normativo e de dados derivado da matriz PREVNAR."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from build_normative_matrix import build_matrix
from paths import MART

ROOT = Path(__file__).resolve().parents[1]
WEB_PUBLIC = ROOT / "web" / "public" / "data"


def build_backlog(*, as_of: date | None = None) -> dict[str, Any]:
    matrix = build_matrix(as_of=as_of)
    items: list[dict[str, Any]] = []

    for row in matrix.get("immunobiologics") or []:
        iid = row["immunobiologic_id"]
        display = row["display"]
        active_rules = int(row.get("active_rule_count") or 0)
        draft_rules = int(row.get("draft_rule_count") or 0)
        monitored = bool(row.get("monitored"))
        pni_codes = row.get("pni_codes") or []
        onboarding = str(row.get("onboarding_status") or "")
        mapping = str(row.get("code_mapping_status") or "")

        if draft_rules and active_rules == 0:
            items.append({
                "priority": "P1",
                "category": "normative_rule_pending",
                "immunobiologic_id": iid,
                "display": display,
                "message": f"{draft_rules} regra(s) permanecem em draft e nenhuma está ativa.",
                "next_gate": "validar norma, vigência, população, esquema e testes",
            })

        if "partial" in onboarding or "pending" in onboarding or "pending" in mapping:
            items.append({
                "priority": "P1" if active_rules else "P2",
                "category": "data_mapping_incomplete",
                "immunobiologic_id": iid,
                "display": display,
                "message": f"Mapeamento de dados incompleto: {onboarding or mapping or 'não definido'}.",
                "next_gate": "consolidar códigos, estratégia, dose, grupos e source registry",
            })

        if not pni_codes and row.get("type") == "vaccine":
            items.append({
                "priority": "P1" if active_rules else "P2",
                "category": "national_code_missing",
                "immunobiologic_id": iid,
                "display": display,
                "message": "Vacina sem código nacional registrado no immunobiologic registry.",
                "next_gate": "confirmar código em terminologia/regra de entrada oficial",
            })

        if active_rules and not monitored:
            items.append({
                "priority": "P2",
                "category": "monitoring_not_enabled",
                "immunobiologic_id": iid,
                "display": display,
                "message": "Há regra ativa, mas a camada de monitoramento ainda não está habilitada.",
                "next_gate": "definir data plan, indicadores, ETL, provenance e freshness",
            })

    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    items.sort(
        key=lambda x: (
            order.get(str(x["priority"]), 99),
            str(x["display"]).lower(),
            str(x["category"]),
        )
    )

    counts: dict[str, int] = {}
    for item in items:
        key = str(item["priority"])
        counts[key] = counts.get(key, 0) + 1

    return {
        "schema_version": "1.0",
        "as_of": matrix["as_of"],
        "summary": {
            "total": len(items),
            "by_priority": counts,
        },
        "items": items,
        "interpretation": (
            "Backlog derivado automaticamente do estado normativo e de dados. "
            "Prioridade indica gate técnico/metodológico, não prioridade clínica."
        ),
    }


def write_backlog(*, as_of: date | None = None) -> dict[str, Any]:
    payload = build_backlog(as_of=as_of)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    MART.mkdir(parents=True, exist_ok=True)
    (MART / "normative_backlog.json").write_text(rendered, encoding="utf-8")
    WEB_PUBLIC.mkdir(parents=True, exist_ok=True)
    (WEB_PUBLIC / "normative_backlog.json").write_text(rendered, encoding="utf-8")
    return payload


def main() -> int:
    payload = write_backlog()
    print(
        "Normative backlog:",
        f"total={payload['summary']['total']}",
        f"priorities={payload['summary']['by_priority']}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
