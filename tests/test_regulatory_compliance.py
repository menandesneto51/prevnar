from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from regulatory_compliance import build_regulatory_compliance


AS_OF = date(2026, 9, 26)


def _item(payload: dict, act_id: str) -> dict:
    return next(row for row in payload["items"] if row["act_id"] == act_id)


def test_portaria_5663_effective_date_and_provisions_are_corrected() -> None:
    legal = json.loads((ROOT / "docs/legal_register.json").read_text(encoding="utf-8"))
    act = next(
        row for row in legal["acts"]
        if row["id"] == "portaria_5663_2024_rnds_vacinacao"
    )
    assert act["published_at"] == "2024-11-04"
    assert act["effective_from"] == "2025-03-04"
    assert act["provisions"]["system_adaptation_after_technical_revision_days"] == 15
    assert act["provisions"]["rnds_online_submission_hours"] == 24
    assert act["provisions"]["rnds_offline_submission_days"] == 15


def test_policy_does_not_claim_prevnar_is_directly_legally_bound() -> None:
    policy = json.loads(
        (ROOT / "data/reference/regulatory_compliance_policy.json").read_text(
            encoding="utf-8"
        )
    )
    applicability = policy["applicability"]
    assert applicability["prevnar_current_role"] == "analytical_monitoring"
    assert applicability["prevnar_treatment"] == "internal_regulatory_benchmark"
    assert "não implica" in applicability["warning"].lower()


def test_covid_nt91_is_over_benchmark_with_mapping_pending() -> None:
    payload = build_regulatory_compliance(as_of=AS_OF)
    row = _item(payload, "nt_91_2026_covid")
    assert row["published_at"] == "2026-09-09"
    assert row["benchmark_deadline"] == "2026-09-24"
    assert row["benchmark_status"] == "benchmark_exceeded_mapping_pending"
    assert "covid19" in row["mapping_pending_immunobiologic_ids"]


def test_triplice_nt98_is_still_within_benchmark() -> None:
    payload = build_regulatory_compliance(as_of=AS_OF)
    row = _item(payload, "nt_98_2026_triplice_viral_d0")
    assert row["published_at"] == "2026-09-18"
    assert row["benchmark_deadline"] == "2026-10-03"
    assert row["benchmark_status"] == "within_benchmark"


def test_benchmark_output_avoids_legal_violation_language() -> None:
    payload = build_regulatory_compliance(as_of=AS_OF)
    text = json.dumps(payload, ensure_ascii=False).lower()
    assert "infração legal" not in text
    assert "internal_regulatory_benchmark" in text
