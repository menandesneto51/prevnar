"""Loader Situação 1 — CSVs manuais por condição."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from paths import MART, SIT1, TEMPLATES

# Arquivo esperado: data/manual/situacao1/{condicao_id}.csv com colunas uf,elegiveis
# Ex.: 1.csv = HIV, 2.csv = oncológicos, 3.csv = transplante, 4.csv = TCTH,
#      8.csv = fibrose cística, 12_dialise.csv = diálise (overlay)


def ensure_templates() -> None:
    template = TEMPLATES / "situacao1_template.csv"
    if not template.exists():
        template.write_text("uf,elegiveis\nSP,0\nRJ,0\nMG,0\n", encoding="utf-8")
    readme = SIT1 / "README.txt"
    if not readme.exists():
        readme.write_text(
            "Coloque um CSV por condição Situação 1:\n"
            "  1.csv  HIV/AIDS (SICLOM)\n"
            "  2.csv  Oncológicos (SIA/APAC)\n"
            "  3.csv  Transplantados órgãos sólidos (ABTO)\n"
            "  4.csv  TCTH (ABTO)\n"
            "  8.csv  Fibrose cística (REBRAFC)\n"
            "  12_dialise.csv  Diálise crônica (SBN) — overlay em nefropatias\n\n"
            "Colunas: uf,elegiveis\n",
            encoding="utf-8",
        )


def load_csv(path: Path) -> dict[str, int]:
    out: dict[str, int] = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            uf = (row.get("uf") or "").strip().upper()
            if not uf:
                continue
            try:
                out[uf] = int(float(str(row.get("elegiveis", "0")).replace(",", ".")))
            except ValueError:
                continue
    return out


def load_all() -> dict[str, dict[str, int]]:
    """Retorna {condicao_key: {uf: elegiveis}}."""
    ensure_templates()
    result: dict[str, dict[str, int]] = {}
    for path in sorted(SIT1.glob("*.csv")):
        key = path.stem  # "1", "2", "12_dialise"
        result[key] = load_csv(path)
    return result


def apply_to_denominadores(denoms: list[dict], sit1: dict[str, dict[str, int]]) -> list[dict]:
    """Atualiza linhas situação 1 e overlay diálise."""
    updated = []
    for row in denoms:
        cid = row["condicao_id"]
        uf = row["uf"]
        key = str(cid)
        if key in sit1 and uf in sit1[key]:
            row = {
                **row,
                "elegiveis": sit1[key][uf],
                "carga_pendente": False,
                "situacao_denominador": 1,
                "exibe_cobertura": True,
            }
        # Overlay diálise: se 12_dialise carregado, soma ao elegível de condicao 12 (sit2)
        if cid == 12 and "12_dialise" in sit1 and uf in sit1["12_dialise"]:
            base = row.get("elegiveis") or 0
            dialise = sit1["12_dialise"][uf]
            row = {
                **row,
                "elegiveis": int(base) + int(dialise),
                "fonte": f"{row.get('fonte', '')} + SBN diálise",
                "tem_dialise_sbn": True,
            }
        updated.append(row)
    return updated


def status() -> dict:
    sit1 = load_all()
    expected = ["1", "2", "3", "4", "8"]
    return {
        "carregados": list(sit1.keys()),
        "pendentes": [k for k in expected if k not in sit1],
        "detalhe": {k: len(v) for k, v in sit1.items()},
    }


if __name__ == "__main__":
    ensure_templates()
    print(json.dumps(status(), indent=2, ensure_ascii=False))
