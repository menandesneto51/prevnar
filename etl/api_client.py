"""Cliente HTTP da API DEMAS / OpenDataSUS."""
from __future__ import annotations

import json
import ssl
import time
from pathlib import Path
from typing import Any, Iterator
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://apidadosabertos.saude.gov.br"
PNI_2026 = f"{BASE}/vacinacao/doses-aplicadas-pni-2026"
PAGE_SIZE = 1000  # teto observado na API


def _ssl_contexts() -> list[ssl.SSLContext]:
    return [ssl.create_default_context(), ssl._create_unverified_context()]


def http_get_json(url: str, timeout: int = 120) -> Any:
    last_err: Exception | None = None
    for ctx in _ssl_contexts():
        try:
            req = Request(
                url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "radar-vacinal-vpc20/1.0",
                },
            )
            with urlopen(req, timeout=timeout, context=ctx) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (ssl.SSLError, URLError, HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            last_err = exc
            continue
    raise RuntimeError(f"Falha GET {url}: {last_err}")


def iter_pni_2026(
    *,
    limit: int = PAGE_SIZE,
    start_offset: int = 0,
    max_pages: int | None = None,
    sleep_s: float = 0.15,
    cache_dir: Path | None = None,
) -> Iterator[tuple[int, list[dict]]]:
    """Pagina doses_aplicadas_pni. Yield (offset, records)."""
    offset = start_offset
    pages = 0
    while True:
        if max_pages is not None and pages >= max_pages:
            break
        qs = urlencode({"limit": min(limit, PAGE_SIZE), "offset": offset})
        url = f"{PNI_2026}?{qs}"
        cache_file = None
        if cache_dir is not None:
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = cache_dir / f"pni2026_offset_{offset:08d}.json"
            if cache_file.exists():
                data = json.loads(cache_file.read_text(encoding="utf-8"))
                rows = data.get("doses_aplicadas_pni") or []
                if not rows:
                    break
                yield offset, rows
                offset += len(rows)
                pages += 1
                continue

        data = http_get_json(url)
        if cache_file is not None:
            cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        rows = data.get("doses_aplicadas_pni") or []
        if not rows:
            break
        yield offset, rows
        offset += len(rows)
        pages += 1
        if len(rows) < min(limit, PAGE_SIZE):
            break
        if sleep_s:
            time.sleep(sleep_s)
