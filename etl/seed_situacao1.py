"""Gera CSVs seed Situação 1 (todas as UFs) até carga oficial SICLOM/ABTO/etc."""
from __future__ import annotations

import csv
from pathlib import Path

from paths import SIT1, UF_CODES

# Totais nacionais provisórios (ordem de grandeza clínica/CRIE; substituir por cadastro).
NACIONAIS = {
    "1": 480_000,  # HIV/AIDS — proxy SICLOM
    "2": 220_000,  # Oncológicos em tratamento — proxy SIA/APAC
    "3": 55_000,  # Transplantados órgãos sólidos — proxy ABTO
    "4": 18_000,  # TCTH — proxy ABTO
    "8": 6_500,  # Fibrose cística — proxy REBRAFC
    "12_dialise": 148_000,  # Diálise crônica — proxy SBN
}

# Peso relativo por UF (concentração conhecida + pop); normalizado depois.
PESO = {
    "SP": 22.0,
    "RJ": 9.5,
    "MG": 8.5,
    "BA": 5.5,
    "PR": 5.0,
    "RS": 5.0,
    "PE": 4.0,
    "CE": 3.8,
    "GO": 3.0,
    "PA": 2.8,
    "SC": 2.8,
    "MA": 2.5,
    "DF": 2.2,
    "ES": 2.0,
    "PB": 1.8,
    "AM": 1.8,
    "RN": 1.7,
    "MT": 1.6,
    "MS": 1.5,
    "AL": 1.4,
    "PI": 1.4,
    "SE": 1.1,
    "RO": 0.9,
    "TO": 0.8,
    "AC": 0.5,
    "AP": 0.4,
    "RR": 0.35,
}


def _distribute(total: int) -> dict[str, int]:
    ufs = list(UF_CODES.values())
    weights = {uf: PESO.get(uf, 1.0) for uf in ufs}
    s = sum(weights.values())
    raw = {uf: total * w / s for uf, w in weights.items()}
    out = {uf: int(round(v)) for uf, v in raw.items()}
    # ajuste residual no maior
    delta = total - sum(out.values())
    if delta and out:
        top = max(out, key=out.get)
        out[top] += delta
    return out


def run(*, overwrite: bool = False) -> dict[str, Path]:
    SIT1.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    for key, total in NACIONAIS.items():
        path = SIT1 / f"{key}.csv"
        if path.exists() and not overwrite and key == "1":
            # preservar 1.csv se já tiver dados; completar UFs faltantes
            existing: dict[str, int] = {}
            with open(path, encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    uf = (row.get("uf") or "").strip().upper()
                    if uf:
                        existing[uf] = int(float(str(row.get("elegiveis") or 0)))
            dist = _distribute(total)
            # manter valores manuais já informados; preencher só faltantes
            for uf, n in dist.items():
                if uf not in existing:
                    existing[uf] = n
            rows = existing
        else:
            if path.exists() and not overwrite and key != "1":
                continue
            rows = _distribute(total)

        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["uf", "elegiveis"])
            w.writeheader()
            for uf in sorted(rows):
                w.writerow({"uf": uf, "elegiveis": rows[uf]})
        written[key] = path
        print(f"  {path.name}: {sum(rows.values()):,} elegíveis ({len(rows)} UFs)")
    return written


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--overwrite", action="store_true")
    args = p.parse_args()
    print("Seed Situação 1…")
    run(overwrite=args.overwrite)
