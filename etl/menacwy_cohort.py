"""Cobertura MenACWY por coorte — NT 50/2026-CGICI/DPNI/SVSA/MS.

Reproduz a lógica metodológica oficial:
- numerador nominal RNDS/PNI, código 74, ao menos uma dose por pessoa;
- coorte acompanhada das idades 11 a 14 ao longo dos anos;
- denominador Censo 2022/IBGE por idade simples;
- deduplicação individual apenas em memória;
- persistência somente de agregados.

Não inventa denominador quando o Censo normalizado não está disponível.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import requests
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from api_client import iter_pni_2026
from paths import MART, ROOT, UF_CODES
from provenance import write_manifest

DENOMINATOR_PATH = ROOT / "data" / "manual" / "denominators" / "censo2022_age_simple.csv"
SIDRA_TABLE = "9606"
SIDRA_PERIOD = "2022"
SIDRA_AGE_CATEGORY = {11: "6568", 12: "6569", 13: "6570", 14: "6571"}
OUTPUT_PATH = MART / "mart_menacwy_cohort_coverage.json"
WEB_PUBLIC = ROOT / "web" / "public" / "data"
CACHE = MART / "_cache" / "pni_menacwy_cohort"


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


def _age(row: dict[str, Any]) -> int | None:
    raw = str(row.get("numero_idade_paciente") or "").strip()
    try:
        value = int(raw)
    except ValueError:
        return None
    return value if 0 <= value <= 130 else None


def _patient(row: dict[str, Any]) -> str | None:
    raw = str(row.get("codigo_paciente") or "").strip()
    return raw or None


def _uf(row: dict[str, Any]) -> str:
    raw = str(row.get("sigla_uf_paciente") or "").strip().upper()
    if len(raw) == 2:
        return raw
    mun = _digits(row.get("codigo_municipio_paciente"))
    return UF_CODES.get(mun[:2], "ND") if len(mun) >= 2 else "ND"


def _municipality(row: dict[str, Any]) -> str | None:
    raw = _digits(row.get("codigo_municipio_paciente"))
    if not raw:
        return None
    return raw[:7] if len(raw) >= 7 else raw.zfill(6)


def cohort_year_for_target(reference_year: int, target_age: int) -> int:
    return reference_year - target_age


def expected_vaccination_year(reference_year: int, target_age: int, observed_age: int) -> int:
    """Ano em que a coorte-alvo teria a idade observada."""
    birth_year = cohort_year_for_target(reference_year, target_age)
    return birth_year + observed_age


def row_matches_target_cohort(
    *,
    vaccination_year: int,
    observed_age: int,
    reference_year: int,
    target_age: int,
) -> bool:
    if target_age not in (11, 12, 13, 14):
        return False
    if observed_age < 11 or observed_age > target_age:
        return False
    return vaccination_year == expected_vaccination_year(
        reference_year, target_age, observed_age
    )


def _geo_keys(row: dict[str, Any]) -> list[tuple[str, str]]:
    keys: list[tuple[str, str]] = [("BR", "BR")]
    uf = _uf(row)
    if uf != "ND":
        keys.append(("UF", uf))
    mun = _municipality(row)
    if mun:
        keys.append(("municipality", mun))
    return keys


def aggregate_numerator(
    rows: Iterable[dict[str, Any]],
    *,
    reference_year: int,
) -> dict[tuple[str, str, int], set[str]]:
    """Retorna conjuntos em memória por geografia e idade-alvo."""
    buckets: dict[tuple[str, str, int], set[str]] = defaultdict(set)

    for row in rows:
        if str(row.get("codigo_vacina") or "") != "74":
            continue
        pid = _patient(row)
        dt = _parse_date(row.get("data_vacina"))
        age = _age(row)
        if not pid or not dt or age is None:
            continue
        if dt.year < 2020:
            continue

        for target_age in (11, 12, 13, 14):
            if not row_matches_target_cohort(
                vaccination_year=dt.year,
                observed_age=age,
                reference_year=reference_year,
                target_age=target_age,
            ):
                continue
            for geo_type, geo_code in _geo_keys(row):
                buckets[(geo_type, geo_code, target_age)].add(pid)

    return buckets



def _sidra_url(level: str) -> str:
    ages = ",".join(SIDRA_AGE_CATEGORY.values())
    return (
        "https://apisidra.ibge.gov.br/values/"
        f"t/{SIDRA_TABLE}/{level}/all/v/93/p/{SIDRA_PERIOD}"
        f"/c86/0/c2/0/c287/{ages}?formato=json"
    )


def _header_key(header: dict[str, Any], exact_label: str) -> str | None:
    for key, label in header.items():
        if str(label).strip() == exact_label:
            return key
    return None


def _header_key_contains(header: dict[str, Any], *parts: str) -> str | None:
    """Localiza coluna por termos completos, evitando Idade ~= Unidade."""
    wanted = [p.casefold().strip() for p in parts]
    for key, label in header.items():
        text = str(label).casefold().strip()
        tokens = set(re.findall(r"[a-zà-ÿ0-9]+", text))
        if all(
            (part in tokens) or text.startswith(part + " ") or text.startswith(part + " (")
            for part in wanted
        ):
            return key
    return None


def parse_sidra_response(
    payload: list[dict[str, Any]],
    *,
    geography_type: str,
) -> list[dict[str, Any]]:
    if not payload:
        return []
    header = payload[0]
    value_key = _header_key(header, "Valor") or "V"
    age_code_key = _header_key_contains(header, "idade", "código")
    geo_label = {
        "BR": "Brasil",
        "UF": "Unidade da Federação",
        "municipality": "Município",
    }[geography_type]
    geo_code_key = _header_key_contains(header, geo_label, "código")

    if not age_code_key or not geo_code_key or value_key not in header:
        raise ValueError(
            f"Schema SIDRA inesperado para {geography_type}: {header}"
        )

    age_by_category = {v: k for k, v in SIDRA_AGE_CATEGORY.items()}
    rows: list[dict[str, Any]] = []
    for item in payload[1:]:
        age = age_by_category.get(str(item.get(age_code_key) or ""))
        if age is None:
            continue
        raw_value = str(item.get(value_key) or "").strip()
        if raw_value in {"", "-", "..", "...", "X"}:
            continue
        try:
            population = int(float(raw_value.replace(",", ".")))
        except ValueError:
            continue
        rows.append(
            {
                "geography_type": geography_type,
                "geography_code": str(item.get(geo_code_key) or "").strip(),
                "age": age,
                "population": population,
                "census_year": 2022,
            }
        )
    return rows


def fetch_censo2022_age_simple(
    path: Path = DENOMINATOR_PATH,
) -> list[dict[str, Any]]:
    ca_bundle = os.environ.get("PREVNAR_CA_BUNDLE", "").strip()
    verify: bool | str = ca_bundle if ca_bundle else True
    levels = [
        ("n1", "BR"),
        ("n3", "UF"),
        ("n6", "municipality"),
    ]
    rows: list[dict[str, Any]] = []
    for level, geography_type in levels:
        response = requests.get(
            _sidra_url(level),
            timeout=120,
            verify=verify,
            headers={"User-Agent": "prevnar/2.0"},
        )
        response.raise_for_status()
        rows.extend(
            parse_sidra_response(
                response.json(),
                geography_type=geography_type,
            )
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "geography_type",
                "geography_code",
                "age",
                "population",
                "census_year",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    return rows


def load_denominators(path: Path = DENOMINATOR_PATH) -> dict[tuple[str, str, int], int]:
    if not path.exists():
        return {}

    required = {"geography_type", "geography_code", "age", "population", "census_year"}
    out: dict[tuple[str, str, int], int] = {}

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"Denominador Censo inválido; colunas ausentes: {sorted(missing)}"
            )
        for row in reader:
            try:
                census_year = int(str(row["census_year"]).strip())
                age = int(str(row["age"]).strip())
                population = int(str(row["population"]).strip())
            except (TypeError, ValueError):
                continue
            if census_year != 2022 or age not in (11, 12, 13, 14) or population < 0:
                continue
            key = (
                str(row["geography_type"]).strip(),
                str(row["geography_code"]).strip(),
                age,
            )
            out[key] = population
    return out


def build_coverage(
    numerator: dict[tuple[str, str, int], set[str]],
    denominators: dict[tuple[str, str, int], int],
    *,
    reference_year: int,
) -> dict[str, Any]:
    geographies = sorted(
        {(geo_type, geo_code) for geo_type, geo_code, _ in set(numerator) | set(denominators)}
    )
    rows: list[dict[str, Any]] = []

    for geo_type, geo_code in geographies:
        age_rows = []
        cohort_sets: list[set[str]] = []
        denominator_total = 0
        denominator_complete = True

        for age in (11, 12, 13, 14):
            people = numerator.get((geo_type, geo_code, age), set())
            denom = denominators.get((geo_type, geo_code, age))
            if denom is None:
                denominator_complete = False
            else:
                denominator_total += denom
            cohort_sets.append(people)

            count = len(people)
            coverage = (
                round(100.0 * count / denom, 2)
                if denom is not None and denom > 0
                else None
            )
            age_rows.append(
                {
                    "age": age,
                    "birth_cohort_year": reference_year - age,
                    "vaccinated_unique": count,
                    "denominator_censo2022": denom,
                    "coverage_pct": coverage,
                    "decision_grade": denom is not None and denom > 0,
                }
            )

        union_people: set[str] = set()
        sum_age_unique = 0
        for people in cohort_sets:
            sum_age_unique += len(people)
            union_people |= people
        overlap = max(0, sum_age_unique - len(union_people))

        overall_coverage = (
            round(100.0 * len(union_people) / denominator_total, 2)
            if denominator_complete and denominator_total > 0
            else None
        )

        rows.append(
            {
                "geography_type": geo_type,
                "geography_code": geo_code,
                "reference_year": reference_year,
                "ages": age_rows,
                "vaccinated_unique_11_14": len(union_people),
                "denominator_11_14_censo2022": (
                    denominator_total if denominator_complete else None
                ),
                "coverage_11_14_pct": overall_coverage,
                "decision_grade": overall_coverage is not None,
                "possible_cross_cohort_overlap": overlap,
            }
        )

    return {
        "methodology_id": "menacwy_cohort_nt50_2026",
        "reference_year": reference_year,
        "denominator_source": "IBGE Censo 2022 por idade simples",
        "denominator_loaded": bool(denominators),
        "rows": rows,
        "limitations": [
            "Óbitos não são excluídos de forma exata das coortes vacinadas.",
            "Migração não é modelada de forma exata.",
            "Cobertura fica indisponível quando o denominador normalizado não está carregado.",
        ],
    }


def save_coverage(
    payload: dict[str, Any],
    *,
    numerator_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = write_manifest(
        source_id="ibge_censo2022_age_simple",
        reference_period="2022",
        record_count=sum(
            1
            for row in payload.get("rows", [])
            for age in row.get("ages", [])
            if age.get("denominator_censo2022") is not None
        ),
        status="success" if payload.get("denominator_loaded") else "warning",
        warnings=[] if payload.get("denominator_loaded") else ["denominator_missing"],
        files=[DENOMINATOR_PATH] if DENOMINATOR_PATH.exists() else [],
        schema_version="menacwy-cohort-coverage-v1",
        pipeline_version="2.0",
        extra={"reference_year": payload.get("reference_year")},
    )
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    payload["provenance"] = {
        "numerator": (
            {
                "run_id": numerator_manifest.get("run_id"),
                "source_id": numerator_manifest.get("source_id"),
                "retrieved_at": numerator_manifest.get("retrieved_at"),
                "reference_period": numerator_manifest.get("reference_period"),
                "freshness": numerator_manifest.get("freshness"),
            }
            if numerator_manifest
            else None
        ),
        "denominator": {
            "run_id": manifest["run_id"],
            "source_id": manifest["source_id"],
            "retrieved_at": manifest["retrieved_at"],
            "reference_period": manifest["reference_period"],
            "freshness": manifest["freshness"],
        },
    }
    raw = json.dumps(payload, ensure_ascii=False, indent=2)
    OUTPUT_PATH.write_text(raw, encoding="utf-8")
    WEB_PUBLIC.mkdir(parents=True, exist_ok=True)
    (WEB_PUBLIC / OUTPUT_PATH.name).write_text(raw, encoding="utf-8")
    return payload


def collect_api(
    *,
    reference_year: int,
    max_pages: int | None = None,
) -> dict[str, Any]:
    if max_pages is None:
        raw = os.environ.get("PREVNAR_MENACWY_COHORT_MAX_PAGES", "").strip()
        max_pages = int(raw) if raw.isdigit() else None

    pages = 0
    scanned = 0
    menacwy_hits = 0
    latest_date: date | None = None

    def stream() -> Iterable[dict[str, Any]]:
        nonlocal pages, scanned, menacwy_hits, latest_date
        for offset, rows in iter_pni_2026(max_pages=max_pages, cache_dir=CACHE):
            pages += 1
            scanned += len(rows)
            for row in rows:
                if str(row.get("codigo_vacina") or "") == "74":
                    menacwy_hits += 1
                    dt = _parse_date(row.get("data_vacina"))
                    if dt and (latest_date is None or dt > latest_date):
                        latest_date = dt
                yield row
            print(
                f"offset={offset} page={pages} scanned={scanned} "
                f"menacwy_hits={menacwy_hits}"
            )

    numerator = aggregate_numerator(stream(), reference_year=reference_year)
    if not DENOMINATOR_PATH.exists():
        try:
            fetched = fetch_censo2022_age_simple()
            print(f"Censo 2022 normalizado: {len(fetched)} linhas")
        except Exception as exc:  # noqa: BLE001
            print(f"Falha ao obter Censo 2022 SIDRA: {exc}")
    denominators = load_denominators()
    payload = build_coverage(
        numerator,
        denominators,
        reference_year=reference_year,
    )
    payload["pages"] = pages
    payload["records_scanned"] = scanned
    payload["menacwy_records_observed"] = menacwy_hits
    payload["numerator_reference_period"] = (
        latest_date.isoformat()[:7] if latest_date else None
    )

    numerator_manifest = write_manifest(
        source_id="pni_menacwy",
        reference_period=payload["numerator_reference_period"],
        record_count=menacwy_hits,
        status="success",
        warnings=[],
        schema_version="menacwy-cohort-numerator-v1",
        pipeline_version="2.0",
        extra={"reference_year": reference_year, "methodology_id": payload["methodology_id"]},
    )
    return save_coverage(payload, numerator_manifest=numerator_manifest)


def main() -> int:
    parser = argparse.ArgumentParser(description="PREVNAR MenACWY cohort coverage")
    parser.add_argument("--reference-year", type=int, default=datetime.now(timezone.utc).year)
    parser.add_argument("--max-pages", type=int, default=None)
    args = parser.parse_args()
    payload = collect_api(
        reference_year=args.reference_year,
        max_pages=args.max_pages,
    )
    br = next(
        (
            row for row in payload.get("rows", [])
            if row.get("geography_type") == "BR" and row.get("geography_code") == "BR"
        ),
        None,
    )
    print(
        "MenACWY cohort:",
        f"reference_year={args.reference_year}",
        f"denominator_loaded={payload.get('denominator_loaded')}",
        f"coverage_BR={None if not br else br.get('coverage_11_14_pct')}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
