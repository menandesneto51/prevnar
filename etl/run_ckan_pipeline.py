"""Pipeline CKAN completo: mai→jul 2026 → VPC20 CSV → numerador + mart + timeline."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from paths import RAW, REF

CACHE = Path(os.environ.get("LOCALAPPDATA", ".")) / "prevnar_ckan"
S3 = "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/PNI/csv/vacinacao_{mes}_{ano}_csv.zip"

# fallback se ckan_pni_2026_resources.json não listar o mês
DEFAULT_MONTHS = [
    ("mai", 2026, 3324886864),
    ("jun", 2026, 2751059346),
    ("jul", 2026, 2266767355),
]


def load_months() -> list[tuple[str, int, int]]:
    p = REF / "ckan_pni_2026_resources.json"
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        out: list[tuple[str, int, int]] = []
        for ex in data.get("exemplos") or []:
            mes = ex.get("mes")
            ano = ex.get("ano")
            size = ex.get("tamanho_bytes")
            if mes and ano and size:
                out.append((mes, int(ano), int(size)))
        if out:
            return out
    return DEFAULT_MONTHS


def seed_cache(cache_zip: Path, raw_zip: Path) -> None:
    """Usa ZIP parcial já baixado em data/raw para retomar curl -C -."""
    if not raw_zip.exists():
        return
    raw_sz = raw_zip.stat().st_size
    if raw_sz < 1_000_000:
        return
    if not cache_zip.exists() or cache_zip.stat().st_size < raw_sz:
        print(f"seed cache ← {raw_zip} ({raw_sz:,} bytes)", flush=True)
        shutil.copy2(raw_zip, cache_zip)


def curl_download(url: str, dest: Path, expected: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size >= expected * 0.98:
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
    if sz < expected * 0.98:
        raise RuntimeError(f"incompleto {dest.name}: {sz:,} < {expected:,}")


def main() -> None:
    etl = Path(__file__).resolve().parent
    raw_ckan = RAW / "ckan_pni"
    raw_ckan.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)

    for mes, ano, expected in load_months():
        url = S3.format(mes=mes, ano=ano)
        name = f"vacinacao_{mes}_{ano}_csv.zip"
        cache_zip = CACHE / name
        raw_zip = raw_ckan / name
        out_csv = RAW / f"pni_vpc20_{mes}_{ano}.csv"
        print(f"\n=== {mes}/{ano} ===", flush=True)
        if out_csv.exists() and out_csv.stat().st_size > 1_000_000:
            print(f"CSV VPC20 já existe: {out_csv}", flush=True)
            continue
        seed_cache(cache_zip, raw_zip)
        curl_download(url, cache_zip, expected)
        if not raw_zip.exists() or raw_zip.stat().st_size < expected * 0.98:
            print(f"copiando → {raw_zip}", flush=True)
            shutil.copy2(cache_zip, raw_zip)
        rc = subprocess.call(
            [sys.executable, "-u", str(etl / "extract_ckan_pni.py"), "--mes", mes, "--ano", str(ano), "--skip-download"],
            cwd=etl,
        )
        if rc != 0:
            raise SystemExit(f"filtro {mes} falhou rc={rc}")

    print("\n=== numerador + mart (todos os CSV pni_vpc20_*.csv) ===", flush=True)
    os.environ["RADAR_NUMERADOR_SOURCE"] = "csv"
    import build_mart
    import build_nacional
    import numerador

    n = numerador.run(source="csv")
    print(
        f"numerador: pessoas={n.get('total_pessoas')} doses={n.get('total_doses')} "
        f"meses={len(n.get('linha_tempo') or [])}",
        flush=True,
    )
    print(f"  arquivos={n.get('fonte_arquivos')}", flush=True)
    for row in n.get("linha_tempo") or []:
        print(
            f"  {row['ano_mes']}: {row['doses_mes']:,} doses / "
            f"{row['pessoas_mes']:,} pessoas (acum {row['doses_acumuladas']:,})",
            flush=True,
        )
    d = build_mart.run(refresh_sources=False)
    print(f"mart vac={d['nacional']['pessoas_vacinadas']}", flush=True)
    out = build_nacional.build()
    print(
        f"OK vac_kpi={out['kpis'].get('pessoas_vacinadas_vpc20')} "
        f"timeline_meses={len(out.get('linha_tempo_vpc20') or [])}",
        flush=True,
    )


if __name__ == "__main__":
    main()
