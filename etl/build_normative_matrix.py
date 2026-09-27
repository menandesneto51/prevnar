"""Constrói a matriz normativa auditável do PREVNAR.

Une:
- immunobiologic_registry.json;
- normative_rules.json;
- legal_register.json.

A saída é agregada/configuracional, sem dados pessoais.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from paths import MART, REF

ROOT = Path(__file__).resolve().parents[1]
LEGAL = ROOT / "docs" / "legal_register.json"
REGISTRY = REF / "immunobiologic_registry.json"
RULES = REF / "normative_rules.json"
WEB_PUBLIC = ROOT / "web" / "public" / "data"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _active_on(rule: dict[str, Any], day: date) -> bool:
    if rule.get("status") != "active":
        return False
    start = rule.get("effective_from")
    end = rule.get("effective_until")
    if start and day < date.fromisoformat(str(start)):
        return False
    if end and day > date.fromisoformat(str(end)):
        return False
    return True


def build_matrix(*, as_of: date | None = None) -> dict[str, Any]:
    day = as_of or date.today()
    registry = _load(REGISTRY)
    normative = _load(RULES)
    legal = _load(LEGAL)

    acts = {
        str(item["id"]): item
        for item in legal.get("acts", [])
        if item.get("id")
    }
    rules = normative.get("rules", [])
    rules_by_item: dict[str, list[dict[str, Any]]] = {}
    for rule in rules:
        iid = str(
            rule.get("immunobiologic_id")
            or rule.get("vaccine_id")
            or ""
        )
        if iid:
            rules_by_item.setdefault(iid, []).append(rule)

    rows: list[dict[str, Any]] = []
    unresolved_acts: set[str] = set()

    for item in registry.get("immunobiologics", []):
        iid = str(item.get("immunobiologic_id") or "")
        item_rules = rules_by_item.get(iid, [])
        active = [r for r in item_rules if _active_on(r, day)]
        draft = [r for r in item_rules if r.get("status") == "draft"]

        act_ids = set(str(x) for x in (item.get("normative_acts") or []))
        for rule in item_rules:
            act_ids.update(str(x) for x in (rule.get("normative_acts") or []))

        act_rows: list[dict[str, Any]] = []
        for act_id in sorted(act_ids):
            act = acts.get(act_id)
            if not act:
                unresolved_acts.add(act_id)
                act_rows.append({
                    "id": act_id,
                    "resolved": False,
                })
                continue
            act_rows.append({
                "id": act_id,
                "resolved": True,
                "type": act.get("type"),
                "number": act.get("number"),
                "scope": act.get("scope"),
                "published_at": act.get("published_at"),
                "effective_from": act.get("effective_from"),
                "official_url": act.get("official_url"),
                "topic": act.get("topic") or [],
            })

        rule_rows = []
        for rule in sorted(item_rules, key=lambda x: str(x.get("rule_id") or "")):
            scope = rule.get("geographic_scope") or {}
            rule_rows.append({
                "rule_id": rule.get("rule_id"),
                "rule_type": rule.get("rule_type"),
                "rule_context": rule.get("rule_context"),
                "status": rule.get("status"),
                "active_on_as_of": _active_on(rule, day),
                "effective_from": rule.get("effective_from"),
                "effective_until": rule.get("effective_until"),
                "geographic_scope": {
                    "type": scope.get("type"),
                    "codes": scope.get("codes") or [],
                },
                "normative_acts": rule.get("normative_acts") or [],
                "note": rule.get("note"),
            })

        rows.append({
            "immunobiologic_id": iid,
            "display": item.get("display") or item.get("name") or iid,
            "name": item.get("name"),
            "type": item.get("type"),
            "active_entity": bool(item.get("active")),
            "monitored": bool(item.get("monitored")),
            "onboarding_status": item.get("onboarding_status"),
            "pni_codes": item.get("pni_codes") or [],
            "code_mapping_status": item.get("code_mapping_status"),
            "active_rule_count": len(active),
            "draft_rule_count": len(draft),
            "rules": rule_rows,
            "normative_acts": act_rows,
        })

    status_counts = Counter(
        str(row.get("onboarding_status") or "not_defined")
        for row in rows
    )
    type_counts = Counter(str(row.get("type") or "unknown") for row in rows)

    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "as_of": day.isoformat(),
        "registry_version": registry.get("version"),
        "rules_version": normative.get("version"),
        "legal_updated_at": legal.get("updated_at"),
        "summary": {
            "immunobiologics": len(rows),
            "active_rules": sum(r["active_rule_count"] for r in rows),
            "draft_rules": sum(r["draft_rule_count"] for r in rows),
            "monitored_immunobiologics": sum(1 for r in rows if r["monitored"]),
            "types": dict(sorted(type_counts.items())),
            "onboarding_status": dict(sorted(status_counts.items())),
            "unresolved_legal_references": sorted(unresolved_acts),
        },
        "immunobiologics": sorted(rows, key=lambda x: x["display"].lower()),
        "interpretation": (
            "Matriz de rastreabilidade normativa e maturidade de dados. "
            "Regra ativa não implica disponibilidade de dado nem cobertura calculável."
        ),
    }


def write_matrix(*, as_of: date | None = None) -> dict[str, Any]:
    payload = build_matrix(as_of=as_of)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    MART.mkdir(parents=True, exist_ok=True)
    (MART / "normative_matrix.json").write_text(rendered, encoding="utf-8")
    WEB_PUBLIC.mkdir(parents=True, exist_ok=True)
    (WEB_PUBLIC / "normative_matrix.json").write_text(rendered, encoding="utf-8")
    return payload


def main() -> int:
    payload = write_matrix()
    summary = payload["summary"]
    print(
        "Normative matrix:",
        f"immunobiologics={summary['immunobiologics']}",
        f"active_rules={summary['active_rules']}",
        f"draft_rules={summary['draft_rules']}",
        f"unresolved={len(summary['unresolved_legal_references'])}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
