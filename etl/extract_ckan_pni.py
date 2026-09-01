"""Extrai CSV CKAN PNI mensal (ZIP S3) filtrando VPC20 — streaming.

CSV oficial usa delimitador ';' e colunas co_vacina / sg_imunobiologico (sem CID).

Exemplo:
  .\\.venv\\Scripts\\python -u etl\\extract_ckan_pni.py --mes mai --ano 2026 --skip-download
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import ssl
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

from paths import RAW, REF

S3_TMPL = "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/PNI/csv/vacinacao_{mes}_{ano}_csv.zip"
MESES = {
    "jan": "jan",
    "fev": "fev",
    "mar": "mar",
    "abr": "abr",
    "mai": "mai",
    "jun": "jun",
    "jul": "jul",
    "ago": "ago",
    "set": "set",
    "out": "out",
    "nov": "nov",
    "dez": "dez",
}
VPC20_CODES = {"107", "107.0"}


def download(url: str, dest: Path, *, chunk: int = 8 * 1024 * 1024) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1_000_000_000:
        print(f"já existe {dest} ({dest.stat().st_size:,} bytes)", flush=True)
        return dest
    print(f"baixando {url}…", flush=True)
    ctx = ssl._create_unverified_context()
    req = Request(url, headers={"User-Agent": "radar-vacinal/1.0"})
    with urlopen(req, timeout=600, context=ctx) as resp, open(dest, "wb") as out:
        total = 0
        while True:
            buf = resp.read(chunk)
            if not buf:
                break
            out.write(buf)
            total += len(buf)
            if total % (50 * 1024 * 1024) < chunk:
                print(f"  {total / 1e9:.2f} GB…", flush=True)
    print(f"salvo {dest} ({dest.stat().st_size:,} bytes)", flush=True)
    return dest


def _detect_delim(header_line: str) -> str:
    return ";" if header_line.count(";") >= header_line.count(",") else ","


def _is_vpc20(row: dict, col_vac: str | None, col_sg: str | None) -> bool:
    if col_vac:
        code = str(row.get(col_vac) or "").strip()
        if code in VPC20_CODES:
            return True
    if col_sg:
        sg = str(row.get(col_sg) or "").upper()
        if "VPC20" in sg or "PNEUMOCOCICA 20" in sg or "PREVNAR 20" in sg:
            return True
    return False


def filter_zip(zip_path: Path, out_csv: Path, *, max_rows: int | None = None) -> dict:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    kept = 0
    scanned = 0
    grupo_hits = 0
    fields_sample: list[str] = []
    with zipfile.ZipFile(zip_path) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not names:
            raise FileNotFoundError(f"sem CSV em {zip_path}")
        name = names[0]
        print(f"lendo {name} de {zip_path.name}", flush=True)
        with zf.open(name) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
            first = text.readline()
            delim = _detect_delim(first)
            fields = next(csv.reader([first], delimiter=delim))
            fields_sample = list(fields)
            print(f"delim={delim!r} cols={len(fields)}", flush=True)
            reader = csv.DictReader(text, fieldnames=fields, delimiter=delim)
            col_vac = next(
                (c for c in fields if c.lower() in ("codigo_vacina", "co_vacina", "vacina_codigo")),
                None,
            )
            col_sg = next(
                (c for c in fields if c.lower() in ("sg_imunobiologico", "vacina_nome", "nm_vacina")),
                None,
            )
            col_grupo = next(
                (c for c in fields if "grupo_atendimento" in c.lower()),
                None,
            )
            if not col_vac and not col_sg:
                raise KeyError(f"coluna vacina não encontrada em {fields[:25]}")
            with open(out_csv, "w", encoding="utf-8", newline="") as out:
                writer = csv.DictWriter(out, fieldnames=fields, delimiter=";", extrasaction="ignore")
                writer.writeheader()
                for row in reader:
                    scanned += 1
                    if not _is_vpc20(row, col_vac, col_sg):
                        if scanned % 5_000_000 == 0:
                            print(f"  scanned={scanned:,} kept={kept:,}", flush=True)
                        continue
                    writer.writerow(row)
                    kept += 1
                    if col_grupo and str(row.get(col_grupo) or "").strip():
                        grupo_hits += 1
                    if max_rows and kept >= max_rows:
                        break
                    if kept % 50_000 == 0:
                        print(f"  scanned={scanned:,} kept={kept:,}", flush=True)
    meta = {
        "zip": str(zip_path),
        "out_csv": str(out_csv),
        "scanned": scanned,
        "kept_vpc20": kept,
        "grupo_preenchido": grupo_hits,
        "colunas": fields_sample,
        "nota": "CKAN PNI 2026 sem motivo_indicacao_CID — usar co_vacina_grupo_atendimento",
    }
    print(meta, flush=True)
    (REF / "ckan_pni_ultimo_filtro.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return meta


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--mes", default="mai", choices=sorted(MESES))
    p.add_argument("--ano", type=int, default=2026)
    p.add_argument("--url", default=None)
    p.add_argument("--zip", default=None, help="ZIP local já baixado")
    p.add_argument("--max-rows", type=int, default=None)
    p.add_argument("--skip-download", action="store_true")
    args = p.parse_args()

    url = args.url or S3_TMPL.format(mes=MESES[args.mes], ano=args.ano)
    zip_path = (
        Path(args.zip) if args.zip else RAW / "ckan_pni" / f"vacinacao_{args.mes}_{args.ano}_csv.zip"
    )
    if not args.skip_download and not args.zip:
        download(url, zip_path)
    out_csv = RAW / f"pni_vpc20_{args.mes}_{args.ano}.csv"
    filter_zip(zip_path, out_csv, max_rows=args.max_rows)
    print(f"→ {out_csv} — rode numerador com source=csv", flush=True)


if __name__ == "__main__":
    main()
