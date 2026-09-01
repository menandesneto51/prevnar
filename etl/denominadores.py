"""Denominadores Situação 2 (prevalência × IBGE) e Situação 3 (estimativa nacional)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import requests

from paths import MART, REF, UF_CODES

IBGE_POP_TOTAL = (
    "https://servicodados.ibge.gov.br/api/v3/agregados/6579/"
    "periodos/2024/variaveis/9324?localidades=N3[all]"
)

# Frações etárias aproximadas (Censo 2022) por UF — ≥18 e ≥40 sobre pop total.
# Usadas para escalar a população total 2024 (tabela 6579) às bases do guia.
FRACAO_ETARIA_DEFAULT = {"ge18": 0.76, "ge40": 0.42}

# Ajustes regionais leves (proxy até carga completa SIDRA 9514)
FRACAO_ETARIA_UF: dict[str, dict[str, float]] = {
    "SP": {"ge18": 0.78, "ge40": 0.45},
    "RJ": {"ge18": 0.79, "ge40": 0.46},
    "MG": {"ge18": 0.77, "ge40": 0.44},
    "RS": {"ge18": 0.80, "ge40": 0.48},
    "SC": {"ge18": 0.78, "ge40": 0.44},
    "PR": {"ge18": 0.77, "ge40": 0.43},
    "BA": {"ge18": 0.74, "ge40": 0.39},
    "AM": {"ge18": 0.70, "ge40": 0.33},
    "PA": {"ge18": 0.71, "ge40": 0.34},
    "MA": {"ge18": 0.70, "ge40": 0.33},
    "DF": {"ge18": 0.77, "ge40": 0.40},
}


def load_json(name: str) -> Any:
    with open(REF / name, encoding="utf-8") as f:
        return json.load(f)


def fetch_pop_total_2024() -> dict[str, int]:
    """População residente estimada 2024 por UF (sigla)."""
    try:
        r = requests.get(IBGE_POP_TOTAL, timeout=60)
    except requests.exceptions.SSLError:
        # Ambientes com proxy corporativo / MITM
        r = requests.get(IBGE_POP_TOTAL, timeout=60, verify=False)
    r.raise_for_status()
    data = r.json()
    series = data[0]["resultados"][0]["series"]
    out: dict[str, int] = {}
    for s in series:
        codigo = s["localidade"]["id"]
        uf = UF_CODES.get(codigo)
        if not uf:
            continue
        val = s["serie"].get("2024")
        if val and val != "...":
            out[uf] = int(val)
    return out


def pop_faixa(uf: str, pop_total: int, pop_base: str) -> int:
    if pop_base == "total":
        return pop_total
    # Preferir frações geradas por extract_nacional (SIDRA proxy)
    try:
        payload = load_json("fracoes_etarias_uf.json")
        fracs = (payload.get("por_uf") or {}).get(uf) or FRACAO_ETARIA_UF.get(uf, FRACAO_ETARIA_DEFAULT)
    except Exception:  # noqa: BLE001
        fracs = FRACAO_ETARIA_UF.get(uf, FRACAO_ETARIA_DEFAULT)
    return int(round(pop_total * fracs.get(pop_base, FRACAO_ETARIA_DEFAULT.get(pop_base, 1.0))))


def build_situacao_2(pop: dict[str, int]) -> list[dict]:
    taxas = load_json("taxas_situacao_2.json")
    rows: list[dict] = []
    for t in taxas:
        for uf, pop_total in pop.items():
            base = pop_faixa(uf, pop_total, t["pop_base"])
            elegiveis = int(round((t["taxa_por_100mil"] / 100_000) * base))
            rows.append(
                {
                    "condicao_id": t["condicao_id"],
                    "condicao_nt52": t["condicao_nt52"],
                    "uf": uf,
                    "elegiveis": elegiveis,
                    "situacao_denominador": 2,
                    "exibe_cobertura": False,
                    "fonte": t["fonte"],
                    "carga_pendente": False,
                }
            )
    return rows


def build_situacao_3(pop: dict[str, int]) -> list[dict]:
    estimativas = load_json("estimativas_situacao_3.json")
    trissomias = load_json("trissomias_por_uf.json")
    pop_br = sum(pop.values())
    pop_adulta_br = sum(pop_faixa(uf, p, "ge18") for uf, p in pop.items())
    rows: list[dict] = []

    for e in estimativas:
        cid = e["condicao_id"]
        if e["metodo"] == "seed_por_uf":
            for uf, n in trissomias["por_uf"].items():
                rows.append(
                    {
                        "condicao_id": cid,
                        "condicao_nt52": e["condicao_nt52"],
                        "uf": uf,
                        "elegiveis": int(n),
                        "situacao_denominador": 3,
                        "exibe_cobertura": False,
                        "fonte": e["fonte"],
                        "raro": e.get("raro", False),
                        "carga_pendente": False,
                    }
                )
            continue

        nacional = e["estimativa_nacional"]
        for uf, pop_total in pop.items():
            if e["metodo"] == "rateio_pop_adulta":
                share = pop_faixa(uf, pop_total, "ge18") / pop_adulta_br
            else:
                share = pop_total / pop_br
            elegiveis = int(round(nacional * share))
            rows.append(
                {
                    "condicao_id": cid,
                    "condicao_nt52": e["condicao_nt52"],
                    "uf": uf,
                    "elegiveis": elegiveis,
                    "situacao_denominador": 3,
                    "exibe_cobertura": False,
                    "fonte": e["fonte"],
                    "raro": e.get("raro", False),
                    "carga_pendente": False,
                }
            )
    return rows


def build_situacao_1_placeholders() -> list[dict]:
    """Placeholders para Situação 1 até carga manual CSV."""
    condicoes = [c for c in load_json("condicoes.json") if c["situacao_denominador"] == 1 and c["ativo_v1"]]
    # Diálise entra via situação 1 separada (condicao 12 overlay) — placeholder próprio
    sit1_ids = {c["condicao_id"] for c in condicoes}
    # Adicionar dialise como overlay de condicao 12 quando arquivo dialise existir (loader separado)
    ufs = [u["uf"] for u in load_json("ufs.json")]
    rows: list[dict] = []
    fontes = {
        1: "SICLOM — carga manual",
        2: "SIA/APAC — carga manual",
        3: "ABTO — carga manual",
        4: "ABTO TCTH — carga manual",
        8: "REBRAFC — carga manual",
        12: "Censo SBN — carga manual (diálise)",
    }
    # Nefropatia DRC fica em sit 2; diálise (12 overlay) usa sit1 se CSV dialise existir
    for c in condicoes:
        for uf in ufs:
            rows.append(
                {
                    "condicao_id": c["condicao_id"],
                    "condicao_nt52": c["condicao_nt52"],
                    "uf": uf,
                    "elegiveis": None,
                    "situacao_denominador": 1,
                    "exibe_cobertura": True,
                    "fonte": fontes.get(c["condicao_id"], "Cadastro administrativo"),
                    "carga_pendente": True,
                }
            )
    return rows


def run() -> dict:
    print("Buscando população IBGE 2024…")
    try:
        pop = fetch_pop_total_2024()
    except Exception as exc:  # noqa: BLE001
        print(f"Falha IBGE ({exc}); usando fallback estático.")
        pop = {
            "RO": 1746227, "AC": 880631, "AM": 4281209, "RR": 716793, "PA": 8664306,
            "AP": 802837, "TO": 1577342, "MA": 7010960, "PI": 3375646, "CE": 9233656,
            "RN": 3446071, "PB": 4145040, "PE": 9539029, "AL": 3220104, "SE": 2291077,
            "BA": 14850513, "MG": 21322691, "ES": 4102129, "RJ": 17219679, "SP": 45973194,
            "PR": 11824665, "SC": 8058441, "RS": 11229915, "MS": 2901895, "MT": 3836399,
            "GO": 7350483, "DF": 2982818,
        }

    rows = build_situacao_1_placeholders() + build_situacao_2(pop) + build_situacao_3(pop)
    payload = {
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
        "pop_ibge_2024": pop,
        "linhas": rows,
    }
    out = MART / "denominadores.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Escrito {out} ({len(rows)} linhas)")
    return payload


if __name__ == "__main__":
    run()
