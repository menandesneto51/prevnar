"""Benchmark regulatório PREVNAR para mudanças em regras vacinais.

Não declara conformidade jurídica. Usa a Portaria GM/MS 5.663/2024 como
benchmark interno de governança para acompanhar a atualização do PREVNAR.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from paths import MART, REF, ROOT

LEGAL_REGISTER = ROOT / "docs" / "legal_register.json"
NORMATIVE_RULES = REF / "normative_rules.json"
IMMUNOBIOLOGIC_REGISTRY = REF / "immunobiologic_registry.json"
POLICY = REF / "regulatory_compliance_policy.json"
WEB_PUBLIC = ROOT / "web" / "public" / "data"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_date(value: Any) -> date | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _mapping_pending(item: dict[str, Any]) -> bool:
    values = " ".join(
        str(item.get(key) or "").lower()
        for key in ("onboarding_status", "code_mapping_status")
    )
    return any(token in values for token in ("pending", "partial", "draft"))


def build_regulatory_compliance(*, as_of: date | None = None) -> dict[str, Any]:
    today = as_of or datetime.now(timezone.utc).date()
    legal = _load(LEGAL_REGISTER)
    rules_payload = _load(NORMATIVE_RULES)
    registry_payload = _load(IMMUNOBIOLOGIC_REGISTRY)
    policy = _load(POLICY)

    acts = {str(row["id"]): row for row in legal.get("acts", [])}
    immunobiologics = {
        str(row["immunobiologic_id"]): row
        for row in registry_payload.get("immunobiologics", [])
    }

    referenced: dict[str, dict[str, Any]] = {}
    for rule in rules_payload.get("rules", []):
        iid = str(rule.get("immunobiologic_id") or "")
        for act_id in rule.get("normative_acts") or []:
            bucket = referenced.setdefault(
                str(act_id),
                {"rule_ids": [], "immunobiologic_ids": set(), "rule_statuses": []},
            )
            bucket["rule_ids"].append(str(rule.get("rule_id") or ""))
            if iid:
                bucket["immunobiologic_ids"].add(iid)
            bucket["rule_statuses"].append(str(rule.get("status") or ""))

    tracked_types = set(policy.get("tracked_act_types") or [])
    benchmark_days = int(
        policy.get("benchmarks", {}).get("technical_revision_adaptation_days") or 15
    )
    legal_effective = _parse_date(policy.get("legal_effective_from"))

    rows: list[dict[str, Any]] = []
    for act_id, ref in referenced.items():
        act = acts.get(act_id)
        if not act:
            continue
        if act.get("type") not in tracked_types:
            continue

        published = _parse_date(act.get("published_at"))
        if legal_effective and published and published < legal_effective:
            continue

        immunobiologic_ids = sorted(ref["immunobiologic_ids"])
        items = [immunobiologics.get(iid, {}) for iid in immunobiologic_ids]
        pending_ids = [
            iid
            for iid, item in zip(immunobiologic_ids, items)
            if item and _mapping_pending(item)
        ]

        deadline = published + timedelta(days=benchmark_days) if published else None
        age_days = (today - published).days if published else None
        days_to_deadline = (deadline - today).days if deadline else None

        statuses = set(ref["rule_statuses"])
        if not published:
            benchmark_status = "date_unavailable"
        elif today <= deadline:
            benchmark_status = "within_benchmark"
        elif pending_ids or "draft" in statuses:
            benchmark_status = "benchmark_exceeded_mapping_pending"
        else:
            benchmark_status = "benchmark_exceeded_mapping_complete"

        rows.append(
            {
                "act_id": act_id,
                "number": act.get("number"),
                "type": act.get("type"),
                "published_at": published.isoformat() if published else None,
                "benchmark_deadline": deadline.isoformat() if deadline else None,
                "age_days": age_days,
                "days_to_benchmark_deadline": days_to_deadline,
                "benchmark_status": benchmark_status,
                "rule_ids": sorted(ref["rule_ids"]),
                "rule_statuses": sorted(statuses),
                "immunobiologic_ids": immunobiologic_ids,
                "mapping_pending_immunobiologic_ids": pending_ids,
                "official_url": act.get("official_url"),
            }
        )

    rank = {
        "benchmark_exceeded_mapping_pending": 0,
        "within_benchmark": 1,
        "benchmark_exceeded_mapping_complete": 2,
        "date_unavailable": 3,
    }
    rows.sort(
        key=lambda row: (
            rank.get(str(row["benchmark_status"]), 99),
            str(row.get("benchmark_deadline") or "9999-12-31"),
            str(row.get("number") or ""),
        )
    )

    summary: dict[str, int] = {
        "tracked_acts": len(rows),
        "within_benchmark": 0,
        "benchmark_exceeded_mapping_pending": 0,
        "benchmark_exceeded_mapping_complete": 0,
        "date_unavailable": 0,
    }
    for row in rows:
        status = str(row["benchmark_status"])
        summary[status] = summary.get(status, 0) + 1

    return {
        "schema_version": "1.0",
        "as_of": today.isoformat(),
        "policy_id": policy.get("policy_id"),
        "legal_basis": policy.get("legal_basis"),
        "applicability": policy.get("applicability"),
        "benchmark_days": benchmark_days,
        "summary": summary,
        "items": rows,
        "interpretation": policy.get("interpretation"),
    }


def write_regulatory_compliance(*, as_of: date | None = None) -> dict[str, Any]:
    payload = build_regulatory_compliance(as_of=as_of)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    MART.mkdir(parents=True, exist_ok=True)
    (MART / "regulatory_compliance.json").write_text(rendered, encoding="utf-8")
    WEB_PUBLIC.mkdir(parents=True, exist_ok=True)
    (WEB_PUBLIC / "regulatory_compliance.json").write_text(rendered, encoding="utf-8")
    return payload


def main() -> int:
    payload = write_regulatory_compliance()
    print(
        "Regulatory benchmark:",
        f"tracked={payload['summary']['tracked_acts']}",
        f"pending_overdue={payload['summary']['benchmark_exceeded_mapping_pending']}",
        f"within={payload['summary']['within_benchmark']}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
