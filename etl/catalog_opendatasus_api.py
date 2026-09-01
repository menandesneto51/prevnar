"""Catalog OpenDataSUS swagger endpoints and probe vacinação PNI 2026."""
from __future__ import annotations

import json
import ssl
from collections import defaultdict
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "data" / "reference"
RAW = ROOT / "data" / "raw"
REF.mkdir(parents=True, exist_ok=True)
RAW.mkdir(parents=True, exist_ok=True)

SWAGGER_URL = "https://apidadosabertos.saude.gov.br/static/swagger.json"
BASE = "https://apidadosabertos.saude.gov.br"


def fetch(url: str, timeout: int = 60) -> bytes:
    ctx = ssl.create_default_context()
    try:
        req = Request(url, headers={"Accept": "application/json", "User-Agent": "radar-vacinal/1.0"})
        with urlopen(req, timeout=timeout, context=ctx) as r:
            return r.read()
    except ssl.SSLError:
        ctx = ssl._create_unverified_context()
        req = Request(url, headers={"Accept": "application/json", "User-Agent": "radar-vacinal/1.0"})
        with urlopen(req, timeout=timeout, context=ctx) as r:
            return r.read()


def main() -> None:
    print(f"Baixando {SWAGGER_URL}…")
    blob = fetch(SWAGGER_URL)
    swagger_path = REF / "opendatasus_swagger.json"
    swagger_path.write_bytes(blob)
    spec = json.loads(blob)
    paths = spec.get("paths") or {}

    by: dict[str, list] = defaultdict(list)
    catalog = []
    for path, methods in paths.items():
        for method, op in methods.items():
            if method.startswith("x") or not isinstance(op, dict):
                continue
            tags = op.get("tags") or ["(sem tag)"]
            entry = {
                "method": method.upper(),
                "path": path,
                "tags": tags,
                "operationId": op.get("operationId"),
                "summary": op.get("summary"),
                "parameters": [
                    {
                        "name": p.get("name"),
                        "in": p.get("in"),
                        "required": bool(p.get("required")),
                        "type": (p.get("schema") or {}).get("type") or p.get("type"),
                        "description": p.get("description"),
                    }
                    for p in (op.get("parameters") or [])
                ],
            }
            catalog.append(entry)
            for t in tags:
                by[t].append(entry)

    vac = [e for e in catalog if "vacin" in e["path"].lower() or "pni" in e["path"].lower()]
    out = {
        "fonte": SWAGGER_URL,
        "title": (spec.get("info") or {}).get("title"),
        "version": (spec.get("info") or {}).get("version"),
        "base": BASE,
        "total_endpoints": len(catalog),
        "total_tags": len(by),
        "tags": {t: len(v) for t, v in sorted(by.items())},
        "vacinacao": vac,
        "endpoints": catalog,
    }
    catalog_path = REF / "opendatasus_api_catalog.json"
    catalog_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"title: {out['title']} v{out['version']}")
    print(f"endpoints: {out['total_endpoints']} | tags: {out['total_tags']}")
    print("\nTags:")
    for t, n in out["tags"].items():
        print(f"  {n:4}  {t}")

    print("\n=== Vacinação ===")
    for e in vac:
        print(f"{e['method']} {e['path']}")
        print(f"  {e.get('summary')}")
        for p in e["parameters"]:
            print(f"  - {p['name']} ({p['in']}, req={p['required']}) {p.get('type')}")

    # Probe PNI 2026 with small page
    candidates = [
        f"{BASE}/v1/vacinacao/doses-aplicadas-pni-2026?limit=5&offset=0",
        f"{BASE}/vacinacao/doses-aplicadas-pni-2026?limit=5&offset=0",
        f"{BASE}/v1/vacinacao/doses_aplicadas_pni_2026?limit=5&offset=0",
    ]
    # also from swagger paths
    for e in vac:
        if "2026" in e["path"]:
            candidates.insert(0, f"{BASE}{e['path']}?limit=5&offset=0")
            candidates.insert(1, f"{BASE}/v1{e['path']}?limit=5&offset=0")

    seen = set()
    sample = None
    for url in candidates:
        if url in seen:
            continue
        seen.add(url)
        print(f"\nProbe {url}")
        try:
            data = fetch(url, timeout=90)
            print(f"  OK {len(data)} bytes")
            sample_path = RAW / "api_pni_2026_sample.json"
            sample_path.write_bytes(data)
            sample = json.loads(data)
            break
        except Exception as exc:  # noqa: BLE001
            print(f"  FAIL {exc}")

    if sample is not None:
        keys = list(sample.keys()) if isinstance(sample, dict) else type(sample).__name__
        print("\nSample top-level:", keys)
        if isinstance(sample, dict):
            for k in ("count", "total", "totalCount", "total_count", "next", "offset", "limit"):
                if k in sample:
                    print(f"  {k}: {sample[k]}")
            # find list of records
            for k, v in sample.items():
                if isinstance(v, list) and v:
                    print(f"  records in '{k}': {len(v)} | fields: {list(v[0].keys())[:40]}")
                    fields_path = REF / "opendatasus_pni_2026_fields.json"
                    fields_path.write_text(
                        json.dumps(
                            {"fonte": "api sample", "record_key": k, "fields": list(v[0].keys()), "exemplo": v[0]},
                            ensure_ascii=False,
                            indent=2,
                        ),
                        encoding="utf-8",
                    )
                    break
            else:
                if any(isinstance(v, dict) for v in sample.values()):
                    print("  nested dict sample keys explored")

    print(f"\nCatalogo: {catalog_path}")


if __name__ == "__main__":
    main()
