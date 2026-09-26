"""Cliente HTTP da API DEMAS / OpenDataSUS."""
from __future__ import annotations

import json
import os
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


def _ssl_context() -> ssl.SSLContext:
    """Contexto TLS validado.

    Ambientes corporativos com proxy/inspeção TLS devem informar a CA institucional
    via PREVNAR_CA_BUNDLE. Nunca desabilitamos verificação de certificado.
    """
    ca_bundle = os.environ.get("PREVNAR_CA_BUNDLE", "").strip()
    if ca_bundle:
        path = Path(ca_bundle)
        if not path.exists() or not path.is_file():
            raise RuntimeError(f"PREVNAR_CA_BUNDLE não encontrado: {path}")
        return ssl.create_default_context(cafile=str(path))
    return ssl.create_default_context()


def http_get_json(url: str, timeout: int = 120) -> Any:
    try:
        req = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "prevnar/2.0",
            },
        )
        with urlopen(req, timeout=timeout, context=_ssl_context()) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (ssl.SSLError, URLError, HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Falha GET {url} com validação TLS ativa. "
            "Se houver proxy corporativo, configure PREVNAR_CA_BUNDLE com a CA institucional. "
            f"Erro: {exc}"
        ) from exc


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
