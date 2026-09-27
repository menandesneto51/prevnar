"""Adaptador institucional SIES/DW para transição covid-19.

Aceita CSV/JSON agregado conforme covid19_transition_inventory_schema.json.
Nunca persiste identificadores de pacientes nem linhas brutas no mart.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from covid19_transition_alerts import evaluate_inventory_row
from paths import MART, REF, ROOT
from provenance import write_manifest

SCHEMA_PATH = REF / "covid19_transition_inventory_schema.json"
CONTRACT_PATH = REF / "sies_transition_source_contract.json"
WEB_PUBLIC = ROOT / "web" / "public" / "data"

ALIASES = {
    "data_referencia": "reference_date",
    "dt_referencia": "reference_date",
    "territorio": "territory_code",
    "codigo_territorio": "territory_code",
    "ibge": "territory_code",
    "cnes": "facility_cnes",
    "estabelecimento_cnes": "facility_cnes",
    "produto": "product_variant_id",
    "produto_id": "product_variant_id",
    "lote": "lot",
    "validade": "expiry_date",
    "data_validade": "expiry_date",
    "estoque": "stock_available_doses",
    "saldo_estoque": "stock_available_doses",
    "estoque_disponivel_doses": "stock_available_doses",
    "aplicadas_30d": "doses_administered_30d",
    "doses_aplicadas_30d": "doses_administered_30d",
    "perdas_fisicas_30d": "physical_losses_30d",
    "perdas_tecnicas_30d": "technical_losses_30d",
    "populacao_elegivel_estimada": "eligible_population_estimate",
    "capacidade_armazenamento_doses": "storage_capacity_doses",
    "solicitadas_proximo_ciclo": "requested_doses_next_cycle",
    "doses_solicitadas_proximo_ciclo": "requested_doses_next_cycle",
}

PRODUCT_ALIASES = {
    "comirnaty_lp81_refrigerated_12plus": "comirnaty_lp81_refrigerated_12plus",
    "comirnaty lp.8.1": "comirnaty_lp81_refrigerated_12plus",
    "comirnaty refrigerada lp.8.1": "comirnaty_lp81_refrigerated_12plus",
    "pfizer lp.8.1": "comirnaty_lp81_refrigerated_12plus",
}

INTEGER_FIELDS = {
    "stock_available_doses",
    "doses_administered_30d",
    "physical_losses_30d",
    "technical_losses_30d",
    "eligible_population_estimate",
    "storage_capacity_doses",
    "requested_doses_next_cycle",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_key(value: str) -> str:
    raw = str(value or "").strip().lower()
    return ALIASES.get(raw, raw)


def _parse_date(value: Any, field: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError(f"{field} vazio")
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw[:10], fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"{field} inválido: {raw}")


def _parse_nonnegative_int(value: Any, field: str, *, default: int | None = None) -> int | None:
    raw = str(value if value is not None else "").strip()
    if not raw:
        return default
    try:
        number = int(float(raw.replace(",", ".")))
    except ValueError as exc:
        raise ValueError(f"{field} inválido: {raw}") from exc
    if number < 0:
        raise ValueError(f"{field} não pode ser negativo")
    return number


def _forbidden_columns() -> set[str]:
    contract = _load_json(CONTRACT_PATH)
    fields = (
        contract.get("sources", {})
        .get("sies_institutional_inventory", {})
        .get("forbidden_personal_fields", [])
    )
    return {str(x).strip().lower() for x in fields}


def normalize_row(row: dict[str, Any], *, row_number: int | None = None) -> dict[str, Any]:
    normalized = {
        _canonical_key(k): v
        for k, v in row.items()
        if str(k or "").strip()
    }

    forbidden = _forbidden_columns()
    present_forbidden = sorted(set(normalized) & forbidden)
    if present_forbidden:
        prefix = f"linha {row_number}: " if row_number is not None else ""
        raise ValueError(
            prefix + "campos pessoais proibidos: " + ", ".join(present_forbidden)
        )

    schema = _load_json(SCHEMA_PATH)
    required = {
        str(item["name"])
        for item in schema.get("fields", [])
        if item.get("required")
    }
    missing = sorted(
        key for key in required
        if str(normalized.get(key) or "").strip() == ""
    )
    if missing:
        prefix = f"linha {row_number}: " if row_number is not None else ""
        raise ValueError(prefix + "campos obrigatórios ausentes: " + ", ".join(missing))

    normalized["reference_date"] = _parse_date(
        normalized.get("reference_date"), "reference_date"
    )
    normalized["expiry_date"] = _parse_date(
        normalized.get("expiry_date"), "expiry_date"
    )

    product_raw = str(normalized.get("product_variant_id") or "").strip().lower()
    product = PRODUCT_ALIASES.get(product_raw)
    if not product:
        raise ValueError(
            "product_variant_id não reconhecido para esta versão: "
            + str(normalized.get("product_variant_id") or "")
        )
    normalized["product_variant_id"] = product

    normalized["territory_code"] = str(normalized["territory_code"]).strip()
    normalized["facility_cnes"] = str(normalized.get("facility_cnes") or "").strip() or None
    normalized["lot"] = str(normalized["lot"]).strip()

    for field in INTEGER_FIELDS:
        field_schema = next(
            (x for x in schema.get("fields", []) if x.get("name") == field),
            {},
        )
        default = field_schema.get("default")
        normalized[field] = _parse_nonnegative_int(
            normalized.get(field),
            field,
            default=int(default) if default is not None else None,
        )

    if date.fromisoformat(normalized["expiry_date"]) < date.fromisoformat(
        normalized["reference_date"]
    ):
        # Expired lots are allowed and must trigger an alert; do not reject.
        pass

    return normalized


def load_rows(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            sample = handle.read(8192)
            handle.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
            except csv.Error:
                dialect = csv.excel
            return [dict(row) for row in csv.DictReader(handle, dialect=dialect)]

    if suffix == ".json":
        payload = _load_json(path)
        if isinstance(payload, list):
            return [dict(x) for x in payload]
        if isinstance(payload, dict):
            rows = payload.get("rows") or payload.get("data")
            if isinstance(rows, list):
                return [dict(x) for x in rows]
        raise ValueError("JSON deve ser uma lista ou conter rows/data como lista")

    raise ValueError("Formato não suportado; use CSV ou JSON")


def build_dashboard(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    normalized_rows: list[dict[str, Any]] = []
    alerts: list[dict[str, Any]] = []
    by_territory: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "stock_available_doses": 0,
            "doses_administered_30d": 0,
            "physical_losses_30d": 0,
            "technical_losses_30d": 0,
            "lots": 0,
            "critical_alerts": 0,
            "attention_alerts": 0,
        }
    )

    latest_reference: str | None = None
    for index, raw in enumerate(rows, start=2):
        row = normalize_row(raw, row_number=index)
        normalized_rows.append(row)
        result = evaluate_inventory_row(row)

        territory = str(row["territory_code"])
        agg = by_territory[territory]
        agg["stock_available_doses"] += int(row["stock_available_doses"] or 0)
        agg["doses_administered_30d"] += int(row["doses_administered_30d"] or 0)
        agg["physical_losses_30d"] += int(row.get("physical_losses_30d") or 0)
        agg["technical_losses_30d"] += int(row.get("technical_losses_30d") or 0)
        agg["lots"] += 1

        for alert in result["alerts"]:
            if alert["severity"] == "critical":
                agg["critical_alerts"] += 1
            elif alert["severity"] == "attention":
                agg["attention_alerts"] += 1
            alerts.append({
                "territory_code": territory,
                "facility_cnes": row.get("facility_cnes"),
                "product_variant_id": row["product_variant_id"],
                "lot": row["lot"],
                "expiry_date": row["expiry_date"],
                **alert,
            })

        ref = row["reference_date"]
        if latest_reference is None or ref > latest_reference:
            latest_reference = ref

    totals = {
        "stock_available_doses": sum(
            int(row["stock_available_doses"] or 0) for row in normalized_rows
        ),
        "doses_administered_30d": sum(
            int(row["doses_administered_30d"] or 0) for row in normalized_rows
        ),
        "physical_losses_30d": sum(
            int(row.get("physical_losses_30d") or 0) for row in normalized_rows
        ),
        "technical_losses_30d": sum(
            int(row.get("technical_losses_30d") or 0) for row in normalized_rows
        ),
        "lots": len(normalized_rows),
        "territories": len(by_territory),
        "critical_alerts": sum(
            1 for alert in alerts if alert["severity"] == "critical"
        ),
        "attention_alerts": sum(
            1 for alert in alerts if alert["severity"] == "attention"
        ),
    }

    rank = {"critical": 0, "attention": 1, "info": 2}
    alerts.sort(
        key=lambda x: (
            rank.get(str(x["severity"]), 99),
            str(x["expiry_date"]),
            str(x["territory_code"]),
            str(x["lot"]),
        )
    )

    return {
        "schema_version": "1.0",
        "source_id": "sies_institutional_inventory",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "reference_period": latest_reference,
        "record_count": len(normalized_rows),
        "totals": totals,
        "by_territory": [
            {"territory_code": territory, **values}
            for territory, values in sorted(by_territory.items())
        ],
        "alerts": alerts,
        "interpretation": (
            "Estoque institucional agregado por lote. Não deriva do endpoint público de "
            "doses distribuídas. Alertas são operacionais e exigem validação logística."
        ),
    }


def process_file(path: Path) -> dict[str, Any]:
    rows = load_rows(path)
    dashboard = build_dashboard(rows)
    warnings: list[str] = []
    if dashboard["totals"]["critical_alerts"]:
        warnings.append("critical_logistics_alerts_present")
    if dashboard["record_count"] == 0:
        warnings.append("empty_inventory_extract")

    manifest = write_manifest(
        source_id="sies_institutional_inventory",
        reference_period=dashboard.get("reference_period"),
        record_count=dashboard["record_count"],
        warnings=warnings,
        files=[path],
        schema_version="covid19-transition-inventory-v1",
        pipeline_version="2.0",
        extra={
            "data_semantics": "current_inventory_lot_level_aggregate",
            "contains_personal_data": False,
        },
    )
    dashboard["provenance"] = {
        "run_id": manifest["run_id"],
        "source_id": manifest["source_id"],
        "retrieved_at": manifest["retrieved_at"],
        "reference_period": manifest["reference_period"],
        "freshness": manifest["freshness"],
        "input_files": manifest["files"],
    }

    rendered = json.dumps(dashboard, ensure_ascii=False, indent=2)
    (MART / "covid19_transition_dashboard.json").write_text(
        rendered, encoding="utf-8"
    )
    WEB_PUBLIC.mkdir(parents=True, exist_ok=True)
    (WEB_PUBLIC / "covid19_transition_dashboard.json").write_text(
        rendered, encoding="utf-8"
    )
    return dashboard


def main() -> int:
    parser = argparse.ArgumentParser(
        description="PREVNAR — adaptador SIES/DW institucional para transição covid-19"
    )
    parser.add_argument("input", type=Path, help="CSV ou JSON agregado autorizado")
    args = parser.parse_args()

    payload = process_file(args.input)
    print(
        "SIES institutional inventory:",
        f"rows={payload['record_count']}",
        f"stock={payload['totals']['stock_available_doses']}",
        f"critical={payload['totals']['critical_alerts']}",
        f"attention={payload['totals']['attention_alerts']}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
