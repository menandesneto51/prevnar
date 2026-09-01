"""Discover CKAN PNI 2026 download URLs from HTML (API often 404)."""
from __future__ import annotations

import json
import re
import ssl
from pathlib import Path
from urllib.request import Request, urlopen

from paths import MART, RAW, REF

DATASET = (
    "https://dadosabertos.saude.gov.br/dataset/"
    "doses-aplicadas-pelo-programa-de-nacional-de-imunizacoes-pni-2026"
)


def fetch_html(url: str) -> str:
    ctx = ssl._create_unverified_context()
    req = Request(url, headers={"User-Agent": "radar-vacinal/1.0", "Accept": "text/html"})
    with urlopen(req, timeout=90, context=ctx) as r:
        return r.read().decode("utf-8", "replace")


def main() -> None:
    html = fetch_html(DATASET)
    print(f"html_len={len(html)}")
    links = re.findall(r'href="([^"]+)"', html)
    interesting = [
        l
        for l in links
        if any(x in l.lower() for x in ["download", "csv", "resource", "s3", "blob", ".zip"])
    ]
    print(f"interesting_links={len(interesting)}")
    for l in interesting[:50]:
        print(l[:200])

    rids = list(dict.fromkeys(re.findall(r"/resource/([0-9a-f-]{36})", html)))
    print(f"resource_ids={len(rids)}")
    resources = []
    for rid in rids:
        page = f"{DATASET}/resource/{rid}"
        try:
            rh = fetch_html(page)
        except Exception as exc:  # noqa: BLE001
            print(f"resource fail {rid}: {exc}")
            continue
        title = re.search(r"<h1[^>]*>([^<]+)</h1>", rh)
        dls = re.findall(
            r'href="([^"]*(?:download|\.csv|\.zip|s3\.amazonaws|blob)[^"]*)"',
            rh,
            flags=re.I,
        )
        # also data-module / resource-url
        dls += re.findall(r'data-module-resource-url="([^"]+)"', rh)
        dls += re.findall(r'resource-url-with-hash[^>]*href="([^"]+)"', rh)
        resources.append(
            {
                "id": rid,
                "page": page,
                "title": (title.group(1).strip() if title else None),
                "downloads": list(dict.fromkeys(dls))[:10],
            }
        )
        print(rid, resources[-1]["title"], resources[-1]["downloads"][:3])

    out = {
        "dataset": DATASET,
        "resources": resources,
    }
    path = REF / "ckan_pni_2026_resources.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
