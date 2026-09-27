"""ETL PREVNAR — Influenza 2026.

Base: NT 24/2026-DPNI/SVSA/MS.
Processa somente agregados persistentes; identificadores individuais ficam em memória.
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

REGISTRY = REF / "immunobiologic_registry.json"
CACHE = MART / "_cache" / "pni_influenza_2026"
WEB_PUBLIC = Path(__file__).resolve().parents[1] / "web" / "public" / "data"


def _load_registry() -> dict[str, Any]:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return next(
        x for x in payload["immunobiologics"]
        if x["immunobiologic_id"] == "influenza"
    )


def _digits(value: Any) -> str:
    return re.sub(r"\D", "", str(value or ""))


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


def _patient(row: dict[str, Any]) -> str | None:
    value = str(row.get("codigo_paciente") or "").strip()
    return value or None


def _context(row: dict[str, Any]) -> str | None:
    code = str(row.get("codigo_vacina") or "")
    strategy = str(row.get("codigo_estrategia_vacinacao") or "")
    dose = str(row.get("codigo_dose_vacina") or "")

    if code == "33" and strategy == "1" and dose in {"1", "2", "9"}:
        return "public_routine"
    if code == "33" and strategy == "2" and dose in {"1", "2", "9"}:
        return "public_special"
    if code == "33" and strategy == "14" and dose in {"1", "2", "9"}:
        return "school_vaccination"
    if code == "77" and strategy == "8" and dose in {"1", "2", "9"}:
        return "private_tetravalent"
    if code == "110" and strategy == "8" and dose == "9":
        return "private_high_dose"
    return None


def process_rows(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    item = _load_registry()
    target_codes = {str(x) for x in item.get("pni_codes", [])}

    observed = 0
    confirmed = 0
    observed_people: set[str] = set()
    confirmed_people: set[str] = set()
    context_counts: dict[str, int] = defaultdict(int)
    strategy_counts: dict[str, int] = defaultdict(int)
    dose_counts: dict[str, int] = defaultdict(int)
    presentation_counts: dict[str, int] = defaultdict(int)
    uf_observed: dict[str, int] = defaultdict(int)
    uf_confirmed: dict[str, int] = defaultdict(int)
    people_by_uf: dict[str, set[str]] = defaultdict(set)
    confirmed_people_by_uf: dict[str, set[str]] = defaultdict(set)
    month_observed: dict[str, int] = defaultdict(int)
    month_confirmed: dict[str, int] = defaultdict(int)
    mismatches: dict[str, int] = defaultdict(int)
    latest: date | None = None
    scanned = 0

    for row in rows:
        scanned += 1
        code = str(row.get("codigo_vacina") or "")
        if code not in target_codes:
            continue

        pid = _patient(row)
        dt = _parse_date(row.get("data_vacina"))
        if not pid or not dt:
            mismatches["missing_patient_or_date"] += 1
            continue

        uf = _uf(row)
        month = dt.isoformat()[:7]
        strategy = str(row.get("codigo_estrategia_vacinacao") or "")
        dose = str(row.get("codigo_dose_vacina") or "")

        observed += 1
        observed_people.add(pid)
        uf_observed[uf] += 1
        people_by_uf[uf].add(pid)
        month_observed[month] += 1
        strategy_counts[strategy] += 1
        dose_counts[dose] += 1
        presentation_counts[code] += 1
        if latest is None or dt > latest:
            latest = dt

        context = _context(row)
        if context is None:
            mismatches["code_hit_outside_confirmed_context"] += 1
            continue

        confirmed += 1
        confirmed_people.add(pid)
        context_counts[context] += 1
        uf_confirmed[uf] += 1
        confirmed_people_by_uf[uf].add(pid)
        month_confirmed[month] += 1

    sus = (
        context_counts.get("public_routine", 0)
        + context_counts.get("public_special", 0)
    )
    private = (
        context_counts.get("private_tetravalent", 0)
        + context_counts.get("private_high_dose", 0)
    )

    return {
        "immunobiologic_id": "influenza",
        "scanned": scanned,
        "observed_code_hits": observed,
        "observed_people": len(observed_people),
        "confirmed_context_doses": confirmed,
        "confirmed_context_people": len(confirmed_people),
        "confirmed_share_pct": round(100 * confirmed / observed, 2) if observed else None,
        "sus_confirmed_doses": sus,
        "private_confirmed_doses": private,
        "private_share_pct": round(100 * private / confirmed, 2) if confirmed else None,
        "contextos_confirmados": dict(sorted(context_counts.items())),
        "estrategias": dict(sorted(strategy_counts.items())),
        "doses_codigos": dict(sorted(dose_counts.items())),
        "apresentacoes": dict(sorted(presentation_counts.items())),
        "por_uf": [
            {
                "uf": uf,
                "observed_doses": uf_observed[uf],
                "observed_people": len(people_by_uf[uf]),
                "confirmed_doses": uf_confirmed[uf],
                "confirmed_people": len(confirmed_people_by_uf[uf]),
            }
            for uf in sorted(uf_observed)
        ],
        "linha_tempo": [
            {
                "ano_mes": month,
                "observed_doses": month_observed[month],
                "confirmed_doses": month_confirmed[month],
            }
            for month in sorted(month_observed)
        ],
        "mismatches": dict(mismatches),
        "reference_period": latest.isoformat()[:7] if latest else None,
        "terminology_notes": [
            {
                "id": "school_vaccination_strategy_14",
                "status": "official_guidance_confirmed_valueset_sync_pending",
                "note": (
                    "Estratégia 14 é sustentada por orientação oficial específica de registro; "
                    "BREstrategiaVacinacao 1.1.0 publicado ainda não lista o conceito."
                ),
            }
        ],
        "interpretation": (
            "Registros confirmados seguem apenas as combinações de código/estratégia/dose "
            "explicitamente documentadas na NT 24/2026. Cobertura não é inferida para grupos "
            "sem denominador compatível."
        ),
    }


def collect_api(*, max_pages: int | None = None) -> dict[str, Any]:
    if max_pages is None:
        raw = os.environ.get("PREVNAR_INFLUENZA_API_MAX_PAGES", "").strip()
        max_pages = int(raw) if raw.isdigit() else None

    pages = 0
    streamed = 0

    def stream() -> Iterable[dict[str, Any]]:
        nonlocal pages, streamed
        for offset, rows in iter_pni_2026(max_pages=max_pages, cache_dir=CACHE):
            pages += 1
            streamed += len(rows)
            print(
                f"offset={offset} page={pages} rows={len(rows)} scanned={streamed}"
            )
            yield from rows

    payload = process_rows(stream())
    payload["pages"] = pages
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()

    warnings: list[str] = []
    if payload["mismatches"].get("code_hit_outside_confirmed_context"):
        warnings.append("records_outside_confirmed_mapping_context")
    # Estratégia 14 é confirmada por orientação oficial específica de registro.
    # O ValueSet FHIR BREstrategiaVacinacao 1.1.0 ainda não lista esse conceito;
    # manter a divergência documentada no registry/data plan.

    manifest = write_manifest(
        source_id="pni_influenza_2026",
        reference_period=payload.get("reference_period"),
        record_count=int(payload.get("observed_code_hits") or 0),
        warnings=warnings,
        schema_version="influenza-2026-pni-v1",
        pipeline_version="2.0",
        extra={
            "immunobiologic_id": "influenza",
            "mapping_scope": "nt24_2026_confirmed_contexts",
        },
    )
    payload["provenance"] = {
        "run_id": manifest["run_id"],
        "source_id": "pni_influenza_2026",
        "reference_period": manifest["reference_period"],
        "retrieved_at": manifest["retrieved_at"],
        "freshness": manifest["freshness"],
    }

    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    (MART / "influenza_2026_dashboard.json").write_text(rendered, encoding="utf-8")
    WEB_PUBLIC.mkdir(parents=True, exist_ok=True)
    (WEB_PUBLIC / "influenza_2026_dashboard.json").write_text(rendered, encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="PREVNAR Influenza 2026 PNI ETL")
    parser.add_argument("--max-pages", type=int, default=None)
    args = parser.parse_args()
    result = collect_api(max_pages=args.max_pages)
    print(
        "Influenza ETL:",
        f"observed={result['observed_code_hits']}",
        f"confirmed={result['confirmed_context_doses']}",
        f"sus={result['sus_confirmed_doses']}",
        f"private={result['private_confirmed_doses']}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
