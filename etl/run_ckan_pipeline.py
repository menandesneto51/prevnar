"""Pipeline CKAN jun/jul: download em cache local → filtrar VPC20 → numerador + mart."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from paths import RAW

CACHE = Path(os.environ.get("LOCALAPPDATA", ".")) / "prevnar_ckan"
MONTHS = [
    ("jun", 2026, 2751059346),
    ("jul", 2026, 2266767355),
]
S3 = "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/PNI/csv/vacinacao_{mes}_{ano}_csv.zip"


def curl_download(url: str, dest: Path, expected: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size >= expected:
        print(f"já completo {dest} ({dest.stat().st_size:,})", flush=True)
        return
    print(f"curl → {dest}", flush=True)
    cmd = [
        "curl.exe",
        "-L",
        "--retry",
        "10",
        "--retry-delay",
        "5",
        "-C",
        "-",
        "-o",
        str(dest),
        url,
    ]
    rc = subprocess.call(cmd)
    if rc not in (0, 18):
        raise RuntimeError(f"curl exit {rc}")
    sz = dest.stat().st_size
    if sz < expected:
        raise RuntimeError(f"incompleto {dest.name}: {sz:,} < {expected:,}")


def main() -> None:
    etl = Path(__file__).resolve().parent
    raw_ckan = RAW / "ckan_pni"
    raw_ckan.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)

    for mes, ano, expected in MONTHS:
        url = S3.format(mes=mes, ano=ano)
        name = f"vacinacao_{mes}_{ano}_csv.zip"
        cache_zip = CACHE / name
        raw_zip = raw_ckan / name
        print(f"\n=== {mes}/{ano} ===", flush=True)
        curl_download(url, cache_zip, expected)
        if not raw_zip.exists() or raw_zip.stat().st_size < expected:
            print(f"copiando → {raw_zip}", flush=True)
            shutil.copy2(cache_zip, raw_zip)
        rc = subprocess.call(
            [sys.executable, "-u", str(etl / "extract_ckan_pni.py"), "--mes", mes, "--ano", str(ano), "--skip-download"],
            cwd=etl,
        )
        if rc != 0:
            raise SystemExit(f"filtro {mes} falhou rc={rc}")

    print("\n=== numerador + mart ===", flush=True)
    os.environ["RADAR_NUMERADOR_SOURCE"] = "csv"
    import build_mart
    import build_nacional
    import numerador

    n = numerador.run(source="csv")
    print(f"numerador: pessoas={n.get('total_pessoas')} doses={n.get('total_doses')}", flush=True)
    print(f"  arquivos={n.get('fonte_arquivos')}", flush=True)
    d = build_mart.run(refresh_sources=False)
    print(f"mart vac={d.get('pessoas_vacinadas')}", flush=True)
    out = build_nacional.build()
    print(
        f"OK vac_kpi={out['kpis'].get('pessoas_vacinadas_vpc20')} "
        f"mun={out['kpis'].get('municipios_com_vacinado')}",
        flush=True,
    )


if __name__ == "__main__":
    main()
