"""Proveniência e freshness dos artefatos PREVNAR."""
from __future__ import annotations

import calendar
import hashlib
import json
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from paths import MART, REF

REGISTRY_PATH = REF / "source_registry.json"
META = MART / "_meta"
RUNS = META / "runs"
LATEST = META / "latest"


def load_source_registry() -> dict[str, dict[str, Any]]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {str(row["source_id"]): row for row in payload.get("sources", [])}


def _parse_reference_end(value: str | None) -> date | None:
    if not value:
        return None
    raw = str(value).strip()
    try:
        if len(raw) == 4 and raw.isdigit():
            return date(int(raw), 12, 31)
        if len(raw) >= 7 and raw[4] == "-":
            year = int(raw[:4])
            month = int(raw[5:7])
            if len(raw) >= 10:
                try:
                    return date.fromisoformat(raw[:10])
                except ValueError:
                    pass
            return date(year, month, calendar.monthrange(year, month)[1])
        return date.fromisoformat(raw[:10])
    except (TypeError, ValueError):
        return None


def classify_freshness(
    source_id: str,
    reference_period: str | None,
    *,
    now: date | None = None,
) -> dict[str, Any]:
    registry = load_source_registry()
    meta = registry.get(source_id)
    ref_end = _parse_reference_end(reference_period)
    if not meta or not ref_end:
        return {
            "status": "desconhecido",
            "source_id": source_id,
            "reference_period": reference_period,
            "reference_end": ref_end.isoformat() if ref_end else None,
            "age_days": None,
            "attention_after_days": meta.get("attention_after_days") if meta else None,
            "stale_after_days": meta.get("stale_after_days") if meta else None,
        }

    today = now or datetime.now(timezone.utc).date()
    age_days = max(0, (today - ref_end).days)
    attention = int(meta["attention_after_days"])
    stale = int(meta["stale_after_days"])
    if age_days <= attention:
        status = "atual"
    elif age_days <= stale:
        status = "atencao"
    else:
        status = "desatualizado"

    return {
        "status": status,
        "source_id": source_id,
        "reference_period": reference_period,
        "reference_end": ref_end.isoformat(),
        "age_days": age_days,
        "attention_after_days": attention,
        "stale_after_days": stale,
        "critical_for_decision": bool(meta.get("critical_for_decision")),
        "policy": "internal_operational_expectation",
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_metadata(paths: list[Path] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths or []:
        if not path.exists() or not path.is_file():
            continue
        rows.append(
            {
                "path": str(path),
                "name": path.name,
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return rows


def write_manifest(
    *,
    source_id: str,
    reference_period: str | None,
    record_count: int | None,
    status: str = "success",
    warnings: list[str] | None = None,
    files: list[Path] | None = None,
    schema_version: str = "1",
    pipeline_version: str = "2.0",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    run_id = uuid.uuid4().hex
    freshness = classify_freshness(source_id, reference_period)
    manifest = {
        "run_id": run_id,
        "source_id": source_id,
        "retrieved_at": now.isoformat(),
        "reference_period": reference_period,
        "record_count": record_count,
        "status": status,
        "schema_version": schema_version,
        "pipeline_version": pipeline_version,
        "warnings": warnings or [],
        "files": file_metadata(files),
        "freshness": freshness,
        **(extra or {}),
    }

    RUNS.mkdir(parents=True, exist_ok=True)
    LATEST.mkdir(parents=True, exist_ok=True)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    (RUNS / f"{source_id}-{stamp}-{run_id[:8]}.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (LATEST / f"{source_id}.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def latest_manifest(source_id: str) -> dict[str, Any] | None:
    path = LATEST / f"{source_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
