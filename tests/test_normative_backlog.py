from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from normative_backlog import build_backlog


AS_OF = date(2026, 9, 26)


def test_backlog_is_deterministic_and_prioritized() -> None:
    payload = build_backlog(as_of=AS_OF)
    priorities = [row["priority"] for row in payload["items"]]
    rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    assert priorities == sorted(priorities, key=lambda x: rank[x])


def test_influenza_and_covid_are_flagged_as_normative_pending() -> None:
    payload = build_backlog(as_of=AS_OF)
    pairs = {
        (row["immunobiologic_id"], row["category"])
        for row in payload["items"]
    }
    assert ("influenza", "normative_rule_pending") in pairs
    assert ("covid19", "normative_rule_pending") in pairs


def test_hpv_partial_mapping_is_flagged() -> None:
    payload = build_backlog(as_of=AS_OF)
    rows = [
        row
        for row in payload["items"]
        if row["immunobiologic_id"] == "hpv4"
        and row["category"] == "data_mapping_incomplete"
    ]
    assert rows
    assert rows[0]["priority"] == "P1"


def test_backlog_priority_is_technical_not_clinical() -> None:
    payload = build_backlog(as_of=AS_OF)
    assert "não prioridade clínica" in payload["interpretation"].lower()
