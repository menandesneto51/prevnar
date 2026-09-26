from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from provenance import classify_freshness


def test_month_reference_uses_real_end_of_month() -> None:
    result = classify_freshness("pni", "2026-08", now=date(2026, 9, 26))
    assert result["reference_end"] == "2026-08-31"
    assert result["age_days"] == 26
    assert result["status"] == "atual"


def test_pni_attention_window() -> None:
    result = classify_freshness("pni", "2026-07", now=date(2026, 9, 26))
    assert result["age_days"] == 57
    assert result["status"] == "atencao"


def test_pni_stale_window() -> None:
    result = classify_freshness("pni", "2026-06", now=date(2026, 9, 26))
    assert result["age_days"] == 88
    assert result["status"] == "desatualizado"
    assert result["critical_for_decision"] is True


def test_unknown_source_is_not_silently_current() -> None:
    result = classify_freshness("fonte_inexistente", "2026-08", now=date(2026, 9, 26))
    assert result["status"] == "desconhecido"
    assert result["age_days"] is None
