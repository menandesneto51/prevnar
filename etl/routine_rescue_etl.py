"""ETL de rotina/resgate PREVNAR.

Escopo inicial com códigos PNI confirmados:
- MenACWY: 74
- Febre amarela: 14
- Tríplice viral: 24

HPV4 permanece bloqueado até confirmação inequívoca do código PNI.

Privacidade:
- identificadores individuais são usados apenas em memória para deduplicação;
- nenhuma chave individual é persistida nos marts.
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
CACHE = MART / "_cache" / "pni_routine_rescue"
WEB_PUBLIC = Path(__file__).resolve().parents[1] / "web" / "public" / "data"

TARGETS = {
    "menacwy": {"source_id": "pni_menacwy", "filename": "mart_routine_menacwy.json"},
    "febre_amarela": {"source_id": "pni_febre_amarela", "filename": "mart_routine_febre_amarela.json"},
    "triplice_viral": {"source_id": "pni_triplice_viral", "filename": "mart_routine_triplice_viral.json"},
}


def _registry() -> dict[str, dict[str, Any]]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {
        str(item["immunobiologic_id"]): item
        for item in payload.get("immunobiologics", [])
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
    raw = str(row.get("sigla_uf_paciente") or "").strip().upper()
    if len(raw) == 2:
        return raw
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


def _new_acc() -> dict[str, Any]:
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
        "latest_date": None,
        "invalid": defaultdict(int),
        "context_counts": defaultdict(int),
    }


def _update(acc: dict[str, Any], row: dict[str, Any]) -> bool:
    pid = _pid(row)
    dt = _parse_date(row.get("data_vacina"))
    if not pid or not dt:
        acc["invalid"]["missing_patient_or_date"] += 1
        return False

    uf = _uf(row)
    mun = _mun(row)
    month = dt.isoformat()[:7]
    strategy = str(row.get("codigo_estrategia_vacinacao") or "")
    dose = str(row.get("codigo_dose_vacina") or "")

    acc["doses"] += 1
    acc["people"].add(pid)
    acc["people_by_uf"][uf].add(pid)
    acc["doses_by_uf"][uf] += 1
    if mun:
        acc["people_by_mun"][mun].add(pid)
        acc["doses_by_mun"][mun] += 1
    acc["doses_by_month"][month] += 1
    acc["people_by_month"][month].add(pid)
    acc["strategy_counts"][strategy] += 1
    acc["dose_counts"][dose] += 1
    if acc["latest_date"] is None or dt > acc["latest_date"]:
        acc["latest_date"] = dt
    return True


def _finalize(acc: dict[str, Any], immunobiologic_id: str) -> dict[str, Any]:
    latest = acc["latest_date"]
    payload = {
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
        "linha_tempo": [
            {
                "ano_mes": month,
                "doses": acc["doses_by_month"][month],
                "pessoas": len(acc["people_by_month"][month]),
            }
            for month in sorted(acc["doses_by_month"])
        ],
        "estrategias": dict(sorted(acc["strategy_counts"].items())),
        "doses_codigos": dict(sorted(acc["dose_counts"].items())),
        "invalid_mapping": dict(acc["invalid"]),
        "context_counts": dict(acc["context_counts"]),
        "reference_period": latest.isoformat()[:7] if latest else None,
    }
    return payload


def _decorate(payload: dict[str, Any]) -> None:
    iid = payload["immunobiologic_id"]
    strategies = payload.get("estrategias") or {}
    doses = payload.get("doses_codigos") or {}

    if iid == "menacwy":
        payload["known_routine_booster_records"] = int(
            (payload.get("context_counts") or {}).get("routine_booster") or 0
        )
        payload["known_context_note"] = (
            "Contagem linha a linha: código 74 + estratégia 1 + dose 38."
        )

    elif iid == "febre_amarela":
        known = {"1", "9", "36"}
        payload["known_dose_records"] = sum(
            int(value) for code, value in doses.items() if code in known
        )
        payload["unknown_dose_records"] = max(
            0, int(payload["total_doses"]) - int(payload["known_dose_records"])
        )

    elif iid == "triplice_viral":
        contexts = payload.get("context_counts") or {}
        payload["blockade_records"] = int(contexts.get("blockade") or 0)
        payload["intensification_records"] = int(contexts.get("intensification") or 0)
        payload["context_note"] = (
            "Estratégia identifica contexto observado. Dose zero/bloqueio/intensificação "
            "não equivalem à rotina nacional."
        )


def process_rows(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    registry = _registry()
    code_to_id: dict[str, str] = {}
    for iid in TARGETS:
        for code in registry[iid].get("pni_codes", []):
            code_to_id[str(code)] = iid

    accs = {iid: _new_acc() for iid in TARGETS}
    scanned = 0
    target_hits = 0

    for row in rows:
        scanned += 1
        code = str(row.get("codigo_vacina") or "")
        iid = code_to_id.get(code)
        if not iid:
            continue
        target_hits += 1
        accepted = _update(accs[iid], row)
        if not accepted:
            continue

        strategy = str(row.get("codigo_estrategia_vacinacao") or "")
        dose = str(row.get("codigo_dose_vacina") or "")
        if iid == "menacwy" and strategy == "1" and dose == "38":
            accs[iid]["context_counts"]["routine_booster"] += 1
        elif iid == "triplice_viral":
            if strategy == "3" and dose in {"1", "2", "8", "57"}:
                accs[iid]["context_counts"]["blockade"] += 1
            if strategy == "4" and dose in {"1", "2"}:
                accs[iid]["context_counts"]["intensification"] += 1

    result = {
        "scanned": scanned,
        "target_hits": target_hits,
        "hpv4_status": "blocked_pending_official_code",
    }
    for iid, acc in accs.items():
        payload = _finalize(acc, iid)
        _decorate(payload)
        result[iid] = payload
    return result


def _write_mart(iid: str, payload: dict[str, Any]) -> None:
    meta = TARGETS[iid]
    warnings = []
    if payload.get("invalid_mapping"):
        warnings.append("invalid_or_incomplete_rows_present")

    manifest = write_manifest(
        source_id=meta["source_id"],
        reference_period=payload.get("reference_period"),
        record_count=int(payload.get("total_doses") or 0),
        warnings=warnings,
        schema_version="routine-rescue-pni-v1",
        pipeline_version="2.0",
        extra={"immunobiologic_id": iid},
    )
    payload["provenance"] = {
        "run_id": manifest["run_id"],
        "source_id": manifest["source_id"],
        "reference_period": manifest["reference_period"],
        "retrieved_at": manifest["retrieved_at"],
        "freshness": manifest["freshness"],
    }
    (MART / meta["filename"]).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def collect_api(*, max_pages: int | None = None) -> dict[str, Any]:
    if max_pages is None:
        raw = os.environ.get("PREVNAR_ROUTINE_API_MAX_PAGES", "").strip()
        max_pages = int(raw) if raw.isdigit() else None

    pages = 0
    streamed_rows = 0

    def stream() -> Iterable[dict[str, Any]]:
        nonlocal pages, streamed_rows
        for offset, rows in iter_pni_2026(max_pages=max_pages, cache_dir=CACHE):
            pages += 1
            streamed_rows += len(rows)
            print(
                f"offset={offset} page={pages} rows={len(rows)} "
                f"scanned={streamed_rows}"
            )
            yield from rows

    result = process_rows(stream())
    result["pages"] = pages
    result["generated_at"] = datetime.now(timezone.utc).isoformat()

    for iid in TARGETS:
        _write_mart(iid, result[iid])

    dashboard = {
        "generated_at": result["generated_at"],
        "pages": pages,
        "scanned": result["scanned"],
        "target_hits": result["target_hits"],
        "hpv4_status": result["hpv4_status"],
        "menacwy": result["menacwy"],
        "febre_amarela": result["febre_amarela"],
        "triplice_viral": result["triplice_viral"],
    }
    raw = json.dumps(dashboard, ensure_ascii=False, indent=2)
    (MART / "routine_rescue_dashboard.json").write_text(raw, encoding="utf-8")
    WEB_PUBLIC.mkdir(parents=True, exist_ok=True)
    (WEB_PUBLIC / "routine_rescue_dashboard.json").write_text(raw, encoding="utf-8")
    return dashboard


def main() -> int:
    parser = argparse.ArgumentParser(description="PREVNAR routine/rescue PNI ETL")
    parser.add_argument("--max-pages", type=int, default=None)
    args = parser.parse_args()
    result = collect_api(max_pages=args.max_pages)
    print(
        "Routine/rescue ETL:",
        f"MenACWY={result['menacwy']['total_doses']}",
        f"FA={result['febre_amarela']['total_doses']}",
        f"MMR={result['triplice_viral']['total_doses']}",
        "HPV4=blocked",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
