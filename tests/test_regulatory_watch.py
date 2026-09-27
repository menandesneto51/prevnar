from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from regulatory_watch import (
    compare_target,
    parse_fhir_valueset_page,
    parse_rules_entry_page,
    run_watch,
)


def test_rules_entry_parser_detects_latest_version_and_date() -> None:
    html = """
    <h2>Regras de entrada de dados 5</h2>
    <p>Secretaria de Vigilância em Saúde e Ambiente | MS</p>
    <span>publicado 15/10/2026 16h02</span>
    <a>Regras de entrada de dados 5.xlsx</a>
    <h2>Regras de entrada de dados 4</h2>
    <span>publicado 04/09/2026 16h02</span>
    """
    observed = parse_rules_entry_page(html)
    assert observed["latest_version"] == 5
    assert observed["published_at"] == "2026-10-15"
    assert observed["file_name"] == "regras-de-entrada-de-dados-5.xlsx"


def test_fhir_parser_finds_required_code_and_absent_strategy() -> None:
    html = """
    <div>1.1.0 - STU1</div>
    <div>Active as of 2026-08-22</div>
    <table>
      <tr><td>87</td><td>COVID-19 PFIZER - COMIRNATY</td></tr>
      <tr><td>1</td><td>Rotina</td></tr>
    </table>
    """
    observed = parse_fhir_valueset_page(
        html,
        required_code_displays={"87": "COVID-19 PFIZER - COMIRNATY"},
        tracked_absent_code_displays={"14": "Vacinação Escolar"},
    )
    assert observed["version"] == "1.1.0"
    assert observed["active_as_of"] == "2026-08-22"
    assert observed["required_code_displays"]["87"] is True
    assert observed["tracked_absent_code_displays"]["14"] is False


def test_compare_detects_previously_absent_strategy_when_it_appears() -> None:
    target = {
        "expected": {
            "version": "1.1.0",
            "active_as_of": "2026-08-22",
            "tracked_absent_code_displays": {"14": "Vacinação Escolar"},
        },
        "material_change_fields": [
            "version",
            "active_as_of",
            "tracked_absent_code_displays",
        ],
    }
    observed = {
        "version": "1.1.0",
        "active_as_of": "2026-08-22",
        "tracked_absent_code_displays": {"14": True},
    }
    changes = compare_target(target, observed)
    assert any(
        row["change_type"] == "previously_absent_code_appeared"
        for row in changes
    )


def test_run_watch_reports_no_change_against_baseline(tmp_path: Path) -> None:
    baseline = {
        "version": "test",
        "targets": [
            {
                "target_id": "rules",
                "kind": "rules_entry_page",
                "url": "https://example.test/rules",
                "expected": {
                    "latest_version": 4,
                    "published_at": "2026-09-04",
                    "file_name": "regras-de-entrada-de-dados-4.xlsx",
                },
                "material_change_fields": [
                    "latest_version",
                    "published_at",
                    "file_name",
                ],
            }
        ],
    }
    path = tmp_path / "baseline.json"
    path.write_text(json.dumps(baseline), encoding="utf-8")

    def fetcher(_: str) -> str:
        return """
        <h2>Regras de entrada de dados 4</h2>
        <span>publicado 04/09/2026 16h02</span>
        <a>Regras de entrada de dados 4.xlsx</a>
        """

    report = run_watch(baseline_path=path, fetcher=fetcher)
    assert report["changed"] is False
    assert report["unavailable"] == 0
    assert report["targets"][0]["status"] == "unchanged"


def test_network_failure_is_unavailable_not_normative_change(tmp_path: Path) -> None:
    baseline = {
        "version": "test",
        "targets": [
            {
                "target_id": "rules",
                "kind": "rules_entry_page",
                "url": "https://example.test/rules",
                "expected": {"latest_version": 4},
                "material_change_fields": ["latest_version"],
            }
        ],
    }
    path = tmp_path / "baseline.json"
    path.write_text(json.dumps(baseline), encoding="utf-8")

    def fetcher(_: str) -> str:
        raise RuntimeError("network down")

    report = run_watch(baseline_path=path, fetcher=fetcher)
    assert report["changed"] is False
    assert report["unavailable"] == 1
    assert report["targets"][0]["status"] == "unavailable"
