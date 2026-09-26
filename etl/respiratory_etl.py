"""ETL respiratório PREVNAR: VVSR materna e nirsevimabe.

Usa códigos oficiais do Immunobiologic Registry e gera somente agregados.
Identificadores individuais são usados transitoriamente para deduplicação em memória
e nunca são persistidos nos marts.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from api_client import iter_pni_2026
from paths import MART, REF, UF_CODES
from provenance import write_manifest

REGISTRY_PATH = REF / "immunobiologic_registry.json"
CACHE = MART / "_cache" / "pni_respiratory"
WEB_PUBLIC = Path(__file__).resolve().parents[1] / "web" / "public" / "data"


def _load_registry() -> dict[str, dict[str, Any]]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {
        str(x["immunobiologic_id"]): x
        for x in payload.get("immunobiologics", [])
    }


def _digits(value: Any) -> str:
    return re.sub(r"\D", "", str(value or ""))


def _pid(row: dict[str, Any]) -> str | None:
    value = str(row.get("codigo_paciente") or "").strip()
    return value or None


def _parse_date(value: Any) -> date | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _uf(row: dict[str, Any]) -> str:
    value = str(row.get("sigla_uf_paciente") or "").strip().upper()
    if len(value) == 2:
        return value
    mun = _digits(
        row.get("codigo_municipio_paciente")
        or row.get("codigo_municipio_estabelecimento")
    )
    return UF_CODES.get(mun[:2], "ND") if len(mun) >= 2 else "ND"


def _mun(row: dict[str, Any]) -> str | None:
    raw = _digits(
        row.get("codigo_municipio_paciente")
        or row.get("codigo_municipio_estabelecimento")
    )
    if not raw:
        return None
    return raw[:7] if len(raw) >= 7 else raw.zfill(6)


def _month(dt: date | None) -> str | None:
    return dt.isoformat()[:7] if dt else None


def _base_accumulator() -> dict[str, Any]:
    return {
        "doses": 0,
        "people": set(),
        "people_by_uf": defaultdict(set),
        "people_by_mun": defaultdict(set),
        "doses_by_uf": defaultdict(int),
        "doses_by_mun": defaultdict(int),
        "doses_by_month": defaultdict(int),
        "people_by_month": defaultdict(set),
        "strategy_counts": defaultdict(int),
        "dose_counts": defaultdict(int),
        "group_counts": defaultdict(int),
        "presentation_counts": defaultdict(int),
        "invalid_mapping": defaultdict(int),
        "latest_date": None,
    }


def _update_common(acc: dict[str, Any], row: dict[str, Any]) -> bool:
    pid = _pid(row)
    dt = _parse_date(row.get("data_vacina"))
    if not pid or not dt:
        acc["invalid_mapping"]["missing_patient_or_date"] += 1
        return False

    uf = _uf(row)
    mun = _mun(row)
    month = _month(dt)

    acc["doses"] += 1
    acc["people"].add(pid)
    acc["people_by_uf"][uf].add(pid)
    acc["doses_by_uf"][uf] += 1
    if mun:
        acc["people_by_mun"][mun].add(pid)
        acc["doses_by_mun"][mun] += 1
    if month:
        acc["doses_by_month"][month] += 1
        acc["people_by_month"][month].add(pid)

    strategy = str(row.get("codigo_estrategia_vacinacao") or "")
    dose = str(row.get("codigo_dose_vacina") or "")
    group = _digits(row.get("codigo_vacina_grupo_atendimento")).zfill(6)
    presentation = str(row.get("codigo_vacina") or "")

    acc["strategy_counts"][strategy] += 1
    acc["dose_counts"][dose] += 1
    if group and group != "000000":
        acc["group_counts"][group] += 1
    acc["presentation_counts"][presentation] += 1

    if acc["latest_date"] is None or dt > acc["latest_date"]:
        acc["latest_date"] = dt
    return True


def _is_vvsr(row: dict[str, Any], item: dict[str, Any]) -> bool:
    code = str(row.get("codigo_vacina") or "")
    if code not in {str(x) for x in item.get("pni_codes", [])}:
        return False
    reg = item.get("pni_registration") or {}
    strategy = str(row.get("codigo_estrategia_vacinacao") or "")
    dose = str(row.get("codigo_dose_vacina") or "")
    group = _digits(row.get("codigo_vacina_grupo_atendimento")).zfill(6)
    return (
        strategy in {str(x) for x in reg.get("strategy_codes", [])}
        and dose in {str(x) for x in (reg.get("dose_codes") or {})}
        and group in {str(x).zfill(6) for x in (reg.get("attendance_groups") or {})}
    )


def _is_nirsevimab(row: dict[str, Any], item: dict[str, Any]) -> bool:
    code = str(row.get("codigo_vacina") or "")
    if code not in {str(x) for x in item.get("pni_codes", [])}:
        return False
    reg = item.get("pni_registration") or {}
    strategy = str(row.get("codigo_estrategia_vacinacao") or "")
    dose = str(row.get("codigo_dose_vacina") or "")
    return (
        strategy in {str(x) for x in reg.get("strategy_codes", [])}
        and dose in {str(x) for x in (reg.get("dose_codes") or {})}
    )


def process_rows(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    registry = _load_registry()
    vvsr_item = registry["vvsr_materna"]
    nirs_item = registry["nirsevimab"]

    vvsr = _base_accumulator()
    nirs = _base_accumulator()
    scanned = 0
    raw_codes: dict[str, int] = defaultdict(int)

    for row in rows:
        scanned += 1
        code = str(row.get("codigo_vacina") or "")
        raw_codes[code] += 1

        if code in {str(x) for x in vvsr_item.get("pni_codes", [])}:
            if _is_vvsr(row, vvsr_item):
                _update_common(vvsr, row)
            else:
                vvsr["invalid_mapping"]["code_hit_but_registration_mismatch"] += 1

        if code in {str(x) for x in nirs_item.get("pni_codes", [])}:
            if _is_nirsevimab(row, nirs_item):
                _update_common(nirs, row)
            else:
                nirs["invalid_mapping"]["code_hit_but_registration_mismatch"] += 1

    return {
        "scanned": scanned,
        "raw_codes": dict(raw_codes),
        "vvsr_materna": _finalize(vvsr, "vvsr_materna"),
        "nirsevimab": _finalize(nirs, "nirsevimab"),
    }


def _finalize(acc: dict[str, Any], immunobiologic_id: str) -> dict[str, Any]:
    months = sorted(acc["doses_by_month"])
    timeline = [
        {
            "ano_mes": month,
            "doses": acc["doses_by_month"][month],
            "pessoas": len(acc["people_by_month"][month]),
        }
        for month in months
    ]
    latest_date = acc["latest_date"]
    return {
        "immunobiologic_id": immunobiologic_id,
        "total_doses": acc["doses"],
        "total_pessoas": len(acc["people"]),
        "por_uf": [
            {
                "uf": uf,
                "doses": acc["doses_by_uf"][uf],
                "pessoas": len(acc["people_by_uf"][uf]),
            }
            for uf in sorted(acc["doses_by_uf"])
        ],
        "por_municipio": [
            {
                "municipio_ibge": mun,
                "doses": acc["doses_by_mun"][mun],
                "pessoas": len(acc["people_by_mun"][mun]),
            }
            for mun in sorted(
                acc["doses_by_mun"],
                key=lambda x: -acc["doses_by_mun"][x],
            )
        ],
        "linha_tempo": timeline,
        "estrategias": dict(sorted(acc["strategy_counts"].items())),
        "doses_codigos": dict(sorted(acc["dose_counts"].items())),
        "grupos_atendimento": dict(
            sorted(acc["group_counts"].items(), key=lambda x: -x[1])
        ),
        "apresentacoes": dict(sorted(acc["presentation_counts"].items())),
        "invalid_mapping": dict(acc["invalid_mapping"]),
        "reference_period": latest_date.isoformat()[:7] if latest_date else None,
    }


def _decorate_nirsevimab(payload: dict[str, Any]) -> None:
    strategy = payload.get("estrategias") or {}
    sus = int(strategy.get("2") or 0)
    private = int(strategy.get("8") or 0)
    total = sus + private
    payload["sus_doses"] = sus
    payload["private_doses"] = private
    payload["private_share_pct"] = round(private * 100 / total, 2) if total else None
    payload["pt1_doses"] = int((payload.get("doses_codigos") or {}).get("59") or 0)
    payload["pt2_doses"] = int((payload.get("doses_codigos") or {}).get("60") or 0)


def _write_mart(source_id: str, payload: dict[str, Any], filename: str) -> dict[str, Any]:
    warnings: list[str] = []
    invalid = payload.get("invalid_mapping") or {}
    if invalid:
        warnings.append("registration_mapping_mismatches_present")
    manifest = write_manifest(
        source_id=source_id,
        reference_period=payload.get("reference_period"),
        record_count=int(payload.get("total_doses") or 0),
        warnings=warnings,
        schema_version="respiratory-pni-v1",
        pipeline_version="2.0",
        extra={"immunobiologic_id": payload["immunobiologic_id"]},
    )
    payload["provenance"] = {
        "run_id": manifest["run_id"],
        "source_id": source_id,
        "reference_period": manifest["reference_period"],
        "retrieved_at": manifest["retrieved_at"],
        "freshness": manifest["freshness"],
    }
    path = MART / filename
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def collect_api(*, max_pages: int | None = None) -> dict[str, Any]:
    if max_pages is None:
        raw = os.environ.get("PREVNAR_RESP_API_MAX_PAGES", "").strip()
        max_pages = int(raw) if raw.isdigit() else None

    pages = 0
    streamed_rows = 0

    def row_stream() -> Iterable[dict[str, Any]]:
        nonlocal pages, streamed_rows
        for offset, rows in iter_pni_2026(max_pages=max_pages, cache_dir=CACHE):
            pages += 1
            streamed_rows += len(rows)
            print(
                f"offset={offset} page={pages} rows={len(rows)} "
                f"scanned={streamed_rows}"
            )
            yield from rows

    result = process_rows(row_stream())
    result["pages"] = pages
    result["generated_at"] = datetime.now(timezone.utc).isoformat()

    _decorate_nirsevimab(result["nirsevimab"])
    _write_mart(
        "pni_vvsr_maternal",
        result["vvsr_materna"],
        "mart_respiratory_vvsr_maternal.json",
    )
    _write_mart(
        "pni_nirsevimab",
        result["nirsevimab"],
        "mart_respiratory_nirsevimab.json",
    )

    summary = {
        "generated_at": result["generated_at"],
        "pages": pages,
        "scanned": result["scanned"],
        "vvsr_materna": result["vvsr_materna"],
        "nirsevimab": result["nirsevimab"],
    }
    dashboard_json = json.dumps(summary, ensure_ascii=False, indent=2)
    (MART / "respiratory_dashboard.json").write_text(
        dashboard_json,
        encoding="utf-8",
    )
    WEB_PUBLIC.mkdir(parents=True, exist_ok=True)
    (WEB_PUBLIC / "respiratory_dashboard.json").write_text(
        dashboard_json,
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="PREVNAR respiratory PNI ETL")
    parser.add_argument("--max-pages", type=int, default=None)
    args = parser.parse_args()
    result = collect_api(max_pages=args.max_pages)
    print(
        "Respiratory ETL:",
        f"VVSR doses={result['vvsr_materna']['total_doses']}",
        f"Nirsevimab doses={result['nirsevimab']['total_doses']}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
