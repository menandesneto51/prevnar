"""Regulatory Watch Agent do PREVNAR.

Consulta fontes oficiais, compara com baseline versionado e gera relatório.
Nunca altera regras clínicas, registries ou flags de monitoramento.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import ssl
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from paths import MART, REF

BASELINE = REF / "regulatory_watch_baseline.json"


def _ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context()


def fetch_text(url: str, timeout: int = 60) -> str:
    req = Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": "prevnar-regulatory-watch/1.0",
        },
    )
    try:
        with urlopen(req, timeout=timeout, context=_ssl_context()) as response:
            return response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError, ssl.SSLError) as exc:
        raise RuntimeError(f"Falha ao consultar {url}: {exc}") from exc


def normalize_text(raw_html: str) -> str:
    no_tags = re.sub(r"<[^>]+>", " ", raw_html)
    decoded = html.unescape(no_tags)
    return re.sub(r"\s+", " ", decoded).strip()


def _ascii(value: str) -> str:
    return (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )


def parse_rules_entry_page(raw_html: str) -> dict[str, Any]:
    text = normalize_text(raw_html)
    versions = [
        int(x)
        for x in re.findall(
            r"Regras de entrada de dados\s+(\d+)",
            text,
            flags=re.IGNORECASE,
        )
    ]
    if not versions:
        raise ValueError("Nenhuma versão de Regras de entrada encontrada.")
    latest = max(versions)

    pattern = re.compile(
        rf"Regras de entrada de dados\s+{latest}.*?publicado\s+(\d{{2}}/\d{{2}}/\d{{4}})",
        flags=re.IGNORECASE,
    )
    match = pattern.search(text)
    published = None
    if match:
        day, month, year = match.group(1).split("/")
        published = f"{year}-{month}-{day}"

    return {
        "latest_version": latest,
        "published_at": published,
        "file_name": f"regras-de-entrada-de-dados-{latest}.xlsx",
    }


def _extract_version(text: str) -> str | None:
    patterns = [
        r"Vers[aã]o:\s*([0-9]+(?:\.[0-9]+)+)",
        r"\(v([0-9]+(?:\.[0-9]+)+):\s*Release\)",
        r"\b([0-9]+(?:\.[0-9]+)+)\s*-\s*STU",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def _contains_code_display(text: str, code: str, display: str) -> bool:
    normalized = _ascii(text)
    display_norm = re.escape(_ascii(display))
    return bool(
        re.search(
            rf"(?:^|\s){re.escape(str(code))}\s+{display_norm}(?:\s|$)",
            normalized,
            flags=re.IGNORECASE,
        )
    )


def parse_fhir_valueset_page(
    raw_html: str,
    *,
    required_code_displays: dict[str, str] | None = None,
    tracked_absent_code_displays: dict[str, str] | None = None,
) -> dict[str, Any]:
    text = normalize_text(raw_html)
    version = _extract_version(text)
    active_match = re.search(
        r"Active as of\s+(\d{4}-\d{2}-\d{2})",
        text,
        flags=re.IGNORECASE,
    )
    active_as_of = active_match.group(1) if active_match else None

    required_results = {
        code: _contains_code_display(text, code, display)
        for code, display in (required_code_displays or {}).items()
    }
    absent_results = {
        code: _contains_code_display(text, code, display)
        for code, display in (tracked_absent_code_displays or {}).items()
    }

    return {
        "version": version,
        "active_as_of": active_as_of,
        "required_code_displays": required_results,
        "tracked_absent_code_displays": absent_results,
    }


def inspect_target(target: dict[str, Any], raw_html: str) -> dict[str, Any]:
    expected = target.get("expected") or {}
    kind = target.get("kind")
    if kind == "rules_entry_page":
        return parse_rules_entry_page(raw_html)
    if kind == "fhir_valueset_page":
        return parse_fhir_valueset_page(
            raw_html,
            required_code_displays=expected.get("required_code_displays") or {},
            tracked_absent_code_displays=expected.get("tracked_absent_code_displays") or {},
        )
    raise ValueError(f"Tipo de alvo não suportado: {kind}")


def compare_target(target: dict[str, Any], observed: dict[str, Any]) -> list[dict[str, Any]]:
    expected = target.get("expected") or {}
    changes: list[dict[str, Any]] = []

    for field in target.get("material_change_fields") or []:
        if field == "required_code_displays":
            expected_map = expected.get(field) or {}
            observed_map = observed.get(field) or {}
            missing = [
                {"code": code, "display": display}
                for code, display in expected_map.items()
                if observed_map.get(code) is not True
            ]
            if missing:
                changes.append(
                    {
                        "field": field,
                        "change_type": "required_codes_missing",
                        "expected": expected_map,
                        "observed": observed_map,
                        "details": missing,
                    }
                )
            continue

        if field == "tracked_absent_code_displays":
            expected_map = expected.get(field) or {}
            observed_map = observed.get(field) or {}
            appeared = [
                {"code": code, "display": display}
                for code, display in expected_map.items()
                if observed_map.get(code) is True
            ]
            if appeared:
                changes.append(
                    {
                        "field": field,
                        "change_type": "previously_absent_code_appeared",
                        "expected_absent": expected_map,
                        "observed": observed_map,
                        "details": appeared,
                    }
                )
            continue

        if observed.get(field) != expected.get(field):
            changes.append(
                {
                    "field": field,
                    "change_type": "value_changed",
                    "expected": expected.get(field),
                    "observed": observed.get(field),
                }
            )

    return changes


def run_watch(
    *,
    baseline_path: Path = BASELINE,
    fetcher=fetch_text,
) -> dict[str, Any]:
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    target_reports: list[dict[str, Any]] = []
    all_changes: list[dict[str, Any]] = []
    unavailable = 0

    for target in baseline.get("targets") or []:
        target_id = str(target.get("target_id") or "")
        try:
            raw = fetcher(str(target["url"]))
            observed = inspect_target(target, raw)
            changes = compare_target(target, observed)
            status = "changed" if changes else "unchanged"
        except Exception as exc:  # noqa: BLE001
            observed = None
            changes = []
            status = "unavailable"
            unavailable += 1
            error = str(exc)
        else:
            error = None

        report = {
            "target_id": target_id,
            "url": target.get("url"),
            "kind": target.get("kind"),
            "status": status,
            "expected": target.get("expected"),
            "observed": observed,
            "changes": changes,
            "error": error,
        }
        target_reports.append(report)
        for change in changes:
            all_changes.append({"target_id": target_id, **change})

    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "baseline_version": baseline.get("version"),
        "changed": bool(all_changes),
        "unavailable": unavailable,
        "summary": {
            "targets": len(target_reports),
            "changed_targets": sum(1 for x in target_reports if x["status"] == "changed"),
            "unavailable_targets": unavailable,
        },
        "changes": all_changes,
        "targets": target_reports,
        "interpretation": (
            "Mudança detectada exige revisão humana e PR. "
            "O Regulatory Watch não altera regras clínicas, registries ou monitored."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="PREVNAR Regulatory Watch Agent")
    parser.add_argument(
        "--baseline",
        type=Path,
        default=BASELINE,
        help="Baseline regulatório versionado.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=MART / "regulatory_watch.json",
        help="Arquivo JSON de saída.",
    )
    args = parser.parse_args()

    report = run_watch(baseline_path=args.baseline)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        "Regulatory Watch:",
        f"changed={report['changed']}",
        f"changed_targets={report['summary']['changed_targets']}",
        f"unavailable={report['unavailable']}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
