"""ETL PREVNAR para MenACWY, febre amarela e tríplice viral.

Princípios:
- usa somente mapeamentos confirmados no routine_rescue_data_plan.json;
- processa páginas PNI em streaming;
- identificador individual existe apenas em memória para COUNT DISTINCT;
- marts persistem somente agregados;
- contextos não mapeados são contabilizados como mismatch/unknown, não absorvidos.
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
PLAN_PATH = REF / "routine_rescue_data_plan.json"
CACHE = MART / "_cache" / "pni_routine_rescue"
WEB_PUBLIC = Path(__file__).resolve().parents[1] / "web" / "public" / "data"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _registry() -> dict[str, dict[str, Any]]:
    payload = _load_json(REGISTRY_PATH)
    return {
        str(x["immunobiologic_id"]): x
        for x in payload.get("immunobiologics", [])
    }


def _plan() -> dict[str, dict[str, Any]]:
    payload = _load_json(PLAN_PATH)
    return {
        str(x["immunobiologic_id"]): x
        for x in payload.get("sources", [])
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


def _acc() -> dict[str, Any]:
    return {
        "observed_code_hits": 0,
        "confirmed_context_doses": 0,
        "people": set(),
        "people_confirmed": set(),
        "people_by_uf": defaultdict(set),
        "people_confirmed_by_uf": defaultdict(set),
        "doses_by_uf": defaultdict(int),
        "confirmed_doses_by_uf": defaultdict(int),
        "doses_by_mun": defaultdict(int),
        "confirmed_doses_by_mun": defaultdict(int),
        "doses_by_month": defaultdict(int),
        "confirmed_doses_by_month": defaultdict(int),
        "strategy_counts": defaultdict(int),
        "dose_counts": defaultdict(int),
        "group_counts": defaultdict(int),
        "context_counts": defaultdict(int),
        "mismatch_counts": defaultdict(int),
        "latest_date": None,
    }


def _update_observed(acc: dict[str, Any], row: dict[str, Any]) -> tuple[str, date, str, str | None] | None:
    pid = _pid(row)
    dt = _parse_date(row.get("data_vacina"))
    if not pid or not dt:
        acc["mismatch_counts"]["missing_patient_or_date"] += 1
        return None

    uf = _uf(row)
    mun = _mun(row)
    month = _month(dt)

    acc["observed_code_hits"] += 1
    acc["people"].add(pid)
    acc["people_by_uf"][uf].add(pid)
    acc["doses_by_uf"][uf] += 1
    if mun:
        acc["doses_by_mun"][mun] += 1
    if month:
        acc["doses_by_month"][month] += 1

    strategy = str(row.get("codigo_estrategia_vacinacao") or "")
    dose = str(row.get("codigo_dose_vacina") or "")
    group = _digits(row.get("codigo_vacina_grupo_atendimento")).zfill(6)
    acc["strategy_counts"][strategy] += 1
    acc["dose_counts"][dose] += 1
    if group and group != "000000":
        acc["group_counts"][group] += 1

    if acc["latest_date"] is None or dt > acc["latest_date"]:
        acc["latest_date"] = dt

    return pid, dt, uf, mun


def _mark_confirmed(
    acc: dict[str, Any],
    *,
    pid: str,
    dt: date,
    uf: str,
    mun: str | None,
    context: str,
) -> None:
    month = _month(dt)
    acc["confirmed_context_doses"] += 1
    acc["people_confirmed"].add(pid)
    acc["people_confirmed_by_uf"][uf].add(pid)
    acc["confirmed_doses_by_uf"][uf] += 1
    if mun:
        acc["confirmed_doses_by_mun"][mun] += 1
    if month:
        acc["confirmed_doses_by_month"][month] += 1
    acc["context_counts"][context] += 1


def _context_menacwy(row: dict[str, Any]) -> str | None:
    strategy = str(row.get("codigo_estrategia_vacinacao") or "")
    dose = str(row.get("codigo_dose_vacina") or "")
    if strategy == "1" and dose == "38":
        return "routine_booster_confirmed"
    return None


def _context_yellow_fever(row: dict[str, Any]) -> str | None:
    dose = str(row.get("codigo_dose_vacina") or "")
    if dose in {"1", "9", "36"}:
        return f"coverage_dose_{dose}"
    return None


def _context_mmr(row: dict[str, Any]) -> str | None:
    strategy = str(row.get("codigo_estrategia_vacinacao") or "")
    dose = str(row.get("codigo_dose_vacina") or "")
    if strategy == "3" and dose in {"1", "2", "8", "57"}:
        return f"blockade_dose_{dose}"
    if strategy == "4" and dose in {"1", "2"}:
        return f"intensification_dose_{dose}"
    return None


CONTEXT_RESOLVERS = {
    "menacwy": _context_menacwy,
    "febre_amarela": _context_yellow_fever,
    "triplice_viral": _context_mmr,
}


def _finalize(acc: dict[str, Any], immunobiologic_id: str) -> dict[str, Any]:
    latest = acc["latest_date"]
    return {
        "immunobiologic_id": immunobiologic_id,
        "observed_code_hits": acc["observed_code_hits"],
        "observed_people": len(acc["people"]),
        "confirmed_context_doses": acc["confirmed_context_doses"],
        "confirmed_context_people": len(acc["people_confirmed"]),
        "confirmed_share_pct": (
            round(100 * acc["confirmed_context_doses"] / acc["observed_code_hits"], 2)
            if acc["observed_code_hits"]
            else None
        ),
        "por_uf": [
            {
                "uf": uf,
                "observed_doses": acc["doses_by_uf"][uf],
                "observed_people": len(acc["people_by_uf"][uf]),
                "confirmed_doses": acc["confirmed_doses_by_uf"][uf],
                "confirmed_people": len(acc["people_confirmed_by_uf"][uf]),
            }
            for uf in sorted(acc["doses_by_uf"])
        ],
        "linha_tempo": [
            {
                "ano_mes": month,
                "observed_doses": acc["doses_by_month"][month],
                "confirmed_doses": acc["confirmed_doses_by_month"][month],
            }
            for month in sorted(acc["doses_by_month"])
        ],
        "estrategias": dict(sorted(acc["strategy_counts"].items())),
        "doses_codigos": dict(sorted(acc["dose_counts"].items())),
        "grupos_atendimento": dict(
            sorted(acc["group_counts"].items(), key=lambda x: -x[1])
        ),
        "contextos_confirmados": dict(sorted(acc["context_counts"].items())),
        "mismatches": dict(acc["mismatch_counts"]),
        "reference_period": latest.isoformat()[:7] if latest else None,
        "interpretation": (
            "observed_code_hits inclui todos os registros do código do imunobiológico; "
            "confirmed_context_doses inclui apenas combinações de estratégia/dose "
            "explicitamente mapeadas nesta versão."
        ),
    }


def process_rows(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    registry = _registry()
    plan = _plan()
    targets = ("menacwy", "febre_amarela", "triplice_viral")
    codes = {
        target: {str(x) for x in registry[target].get("pni_codes", [])}
        for target in targets
    }
    accs = {target: _acc() for target in targets}
    scanned = 0

    for row in rows:
        scanned += 1
        vaccine_code = str(row.get("codigo_vacina") or "")

        for target in targets:
            if vaccine_code not in codes[target]:
                continue

            acc = accs[target]
            observed = _update_observed(acc, row)
            if not observed:
                continue

            pid, dt, uf, mun = observed
            resolver = CONTEXT_RESOLVERS[target]
            context = resolver(row)
            if context:
                _mark_confirmed(
                    acc,
                    pid=pid,
                    dt=dt,
                    uf=uf,
                    mun=mun,
                    context=context,
                )
            else:
                acc["mismatch_counts"]["code_hit_outside_confirmed_context"] += 1

    return {
        "scanned": scanned,
        **{target: _finalize(accs[target], target) for target in targets},
        "mapping_plan_version": _load_json(PLAN_PATH).get("version"),
        "hpv4": {
            "status": "not_collected",
            "reason": "partial mapping: immunobiologic code confirmed but strategy/dose/groups pending",
            "immunobiologic_codes": plan["hpv4"].get("immunobiologic_codes"),
        },
    }


def _write_mart(source_id: str, payload: dict[str, Any], filename: str) -> dict[str, Any]:
    warnings: list[str] = []
    if (payload.get("mismatches") or {}).get("code_hit_outside_confirmed_context"):
        warnings.append("records_outside_confirmed_mapping_context")

    manifest = write_manifest(
        source_id=source_id,
        reference_period=payload.get("reference_period"),
        record_count=int(payload.get("observed_code_hits") or 0),
        warnings=warnings,
        schema_version="routine-rescue-pni-v1",
        pipeline_version="2.0",
        extra={
            "immunobiologic_id": payload["immunobiologic_id"],
            "mapping_scope": "partial_confirmed_contexts",
        },
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
        raw = os.environ.get("PREVNAR_ROUTINE_API_MAX_PAGES", "").strip()
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

    result = process_rows(stream())
    result["pages"] = pages
    result["generated_at"] = datetime.now(timezone.utc).isoformat()

    _write_mart("pni_menacwy", result["menacwy"], "mart_menacwy.json")
    _write_mart(
        "pni_febre_amarela",
        result["febre_amarela"],
        "mart_febre_amarela.json",
    )
    _write_mart(
        "pni_triplice_viral",
        result["triplice_viral"],
        "mart_triplice_viral.json",
    )

    dashboard = {
        "generated_at": result["generated_at"],
        "pages": pages,
        "scanned": result["scanned"],
        "mapping_plan_version": result["mapping_plan_version"],
        "hpv4": result["hpv4"],
        "menacwy": result["menacwy"],
        "febre_amarela": result["febre_amarela"],
        "triplice_viral": result["triplice_viral"],
    }

    dashboard_json = json.dumps(dashboard, ensure_ascii=False, indent=2)
    (MART / "routine_rescue_dashboard.json").write_text(
        dashboard_json,
        encoding="utf-8",
    )
    WEB_PUBLIC.mkdir(parents=True, exist_ok=True)
    (WEB_PUBLIC / "routine_rescue_dashboard.json").write_text(
        dashboard_json,
        encoding="utf-8",
    )
    return dashboard


def main() -> int:
    parser = argparse.ArgumentParser(description="PREVNAR routine/rescue PNI ETL")
    parser.add_argument("--max-pages", type=int, default=None)
    args = parser.parse_args()

    result = collect_api(max_pages=args.max_pages)
    print(
        "Routine/rescue ETL:",
        f"MenACWY={result['menacwy']['observed_code_hits']}",
        f"VFA={result['febre_amarela']['observed_code_hits']}",
        f"SCR={result['triplice_viral']['observed_code_hits']}",
        "HPV4=not_collected",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
