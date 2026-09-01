"""Monta mart_gap_condicao_uf e resumos para o dashboard."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from paths import MART, REF
from situacao1 import apply_to_denominadores, load_all, status as sit1_status
import denominadores as denom_mod
import numerador as num_mod


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def format_elegiveis(n: int | None, raro: bool) -> dict:
    if n is None:
        return {"valor": None, "display": "—", "suprimido": False}
    if raro and n < 50:
        return {"valor": n, "display": "< 100", "suprimido": True}
    return {"valor": n, "display": f"{n:,}".replace(",", "."), "suprimido": False}


def build_gap(denoms: list[dict], numerador: dict, condicoes: list[dict]) -> list[dict]:
    vac_map: dict[tuple[int, str], int] = {}
    for r in numerador.get("linhas", []):
        vac_map[(r["condicao_id"], r["uf"])] = r["pessoas_vacinadas"]

    cond_meta = {c["condicao_id"]: c for c in condicoes if c.get("ativo_v1", True)}
    rows = []
    for d in denoms:
        cid = d["condicao_id"]
        if cid not in cond_meta:
            continue
        uf = d["uf"]
        meta = cond_meta[cid]
        eleg = d.get("elegiveis")
        vac = vac_map.get((cid, uf), 0)
        pendente = bool(d.get("carga_pendente"))
        gap = None if eleg is None else max(0, int(eleg) - vac)
        cobertura = None
        if (
            meta.get("exibe_cobertura")
            and eleg
            and not pendente
            and int(eleg) > 0
        ):
            cobertura = round(100.0 * vac / int(eleg), 2)

        raro = bool(meta.get("raro") or d.get("raro"))
        fmt = format_elegiveis(None if pendente else eleg, raro)

        rows.append(
            {
                "condicao_id": cid,
                "condicao_nt52": meta["condicao_nt52"],
                "uf": uf,
                "elegiveis": None if pendente else eleg,
                "elegiveis_display": "carga pendente" if pendente else fmt["display"],
                "elegiveis_suprimido": fmt["suprimido"],
                "pessoas_vacinadas": vac,
                "gap": gap,
                "cobertura_pct": cobertura,
                "exibe_cobertura": bool(meta.get("exibe_cobertura")) and not pendente,
                "situacao_denominador": d.get("situacao_denominador"),
                "carga_pendente": pendente,
                "fonte_denominador": d.get("fonte"),
                "raro": raro,
                "taxa_cid_preenchido": numerador.get("taxa_cid_preenchido"),
                "atualizado_em": datetime.now(timezone.utc).isoformat(),
            }
        )
    return rows


def summarize(gap_rows: list[dict], numerador: dict, condicoes: list[dict]) -> dict:
    ativos = [c for c in condicoes if c.get("ativo_v1")]
    # Totais: somar elegíveis (exceto pendentes); vacinados consolidados do numerador
    eleg_total = sum(r["elegiveis"] or 0 for r in gap_rows if r["elegiveis"] is not None)
    # Para vacinados nacionais use total_pessoas (anti double-count), não soma por condição
    vac_total = numerador.get("total_pessoas", 0)
    gap_total = max(0, eleg_total - vac_total) if eleg_total else None

    por_condicao = []
    for c in ativos:
        subset = [r for r in gap_rows if r["condicao_id"] == c["condicao_id"]]
        eleg = sum(r["elegiveis"] or 0 for r in subset if r["elegiveis"] is not None)
        vac = sum(r["pessoas_vacinadas"] for r in subset)
        pendente = all(r["carga_pendente"] for r in subset) if subset else True
        raro = bool(c.get("raro"))
        fmt = format_elegiveis(None if (c["situacao_denominador"] == 1 and pendente) else eleg, raro)
        cobertura = None
        if c.get("exibe_cobertura") and not pendente and eleg > 0:
            cobertura = round(100.0 * vac / eleg, 2)
        por_condicao.append(
            {
                "condicao_id": c["condicao_id"],
                "condicao_nt52": c["condicao_nt52"],
                "situacao_denominador": c["situacao_denominador"],
                "elegiveis": None if (c["situacao_denominador"] == 1 and pendente) else eleg,
                "elegiveis_display": "carga pendente" if (c["situacao_denominador"] == 1 and pendente) else fmt["display"],
                "pessoas_vacinadas": vac,
                "gap": None if (c["situacao_denominador"] == 1 and pendente) else max(0, eleg - vac),
                "cobertura_pct": cobertura,
                "exibe_cobertura": bool(c.get("exibe_cobertura")) and not pendente,
                "carga_pendente": c["situacao_denominador"] == 1 and pendente,
                "raro": raro,
            }
        )

    por_uf: dict[str, dict] = {}
    for r in gap_rows:
        uf = r["uf"]
        bucket = por_uf.setdefault(
            uf,
            {"uf": uf, "elegiveis": 0, "pessoas_vacinadas": 0, "gap": 0, "pendencias": 0},
        )
        if r["elegiveis"] is not None:
            bucket["elegiveis"] += r["elegiveis"]
            bucket["gap"] += r["gap"] or 0
        else:
            bucket["pendencias"] += 1
        bucket["pessoas_vacinadas"] += r["pessoas_vacinadas"]

    sanity_ref = numerador.get("sanity_referencia_doses")
    sanity_div = numerador.get("sanity_divergencia_pct")
    if sanity_ref and numerador.get("total_doses"):
        sanity_div = abs(numerador["total_doses"] - sanity_ref) / max(sanity_ref, 1) * 100

    # Totais por UF: preferir consolidado do numerador (anti dupla-contagem / API)
    for uf, n in numerador.get("pessoas_por_uf", {}).items():
        if uf in por_uf:
            por_uf[uf]["pessoas_vacinadas_consolidado"] = n
            por_uf[uf]["pessoas_vacinadas"] = n
            if por_uf[uf]["elegiveis"]:
                por_uf[uf]["gap"] = max(0, por_uf[uf]["elegiveis"] - n)

    return {
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
        "nacional": {
            "elegiveis": eleg_total,
            "pessoas_vacinadas": vac_total,
            "gap": gap_total,
            "taxa_cid_preenchido": numerador.get("taxa_cid_preenchido"),
            "total_doses": numerador.get("total_doses"),
            "fixture": numerador.get("fixture", False),
            "fonte_numerador": numerador.get("fonte"),
            "fonte_tipo": numerador.get("fonte_tipo"),
            "sem_cid_na_fonte": numerador.get("sem_cid_na_fonte", False),
        },
        "por_condicao": sorted(por_condicao, key=lambda x: -(x["gap"] or 0)),
        "por_uf": sorted(por_uf.values(), key=lambda x: -x["gap"]),
        "por_municipio": numerador.get("por_municipio")
        or [
            {
                "municipio_ibge": mun,
                "uf": mun[:2] if len(mun) >= 2 else "ND",
                "nome": None,
                "pessoas_vacinadas": n,
                "doses": n,
            }
            for mun, n in sorted(
                (numerador.get("pessoas_por_municipio") or {}).items(),
                key=lambda x: -x[1],
            )
        ],
        "qualidade": {
            "taxa_cid_preenchido": numerador.get("taxa_cid_preenchido"),
            "cids_nao_mapeados": numerador.get("cids_nao_mapeados", {}),
            "filtro_crie_aplicado": numerador.get("filtro_crie_aplicado"),
            "sem_cid_na_fonte": numerador.get("sem_cid_na_fonte", False),
            "fonte_tipo": numerador.get("fonte_tipo"),
            "filtro_detalhe": numerador.get("filtro_detalhe"),
            "sanity_divergencia_pct": sanity_div,
            "sanity_alerta": bool(sanity_div is not None and sanity_div > 5),
            "situacao1": sit1_status(),
            "nota_numerador": numerador.get("nota"),
        },
    }


def run(refresh_sources: bool = True) -> dict:
    if refresh_sources:
        print("=== Denominadores ===")
        denom_mod.run()
        print("=== Numerador ===")
        num_mod.run()

    denoms_payload = load_json(MART / "denominadores.json")
    numerador = load_json(MART / "numerador.json")
    condicoes = load_json(REF / "condicoes.json")
    ufs = load_json(REF / "ufs.json")

    sit1 = load_all()
    denoms = apply_to_denominadores(denoms_payload["linhas"], sit1)

    gap_rows = build_gap(denoms, numerador, condicoes)
    save_json(MART / "mart_gap_condicao_uf.json", {
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
        "linhas": gap_rows,
    })

    summary = summarize(gap_rows, numerador, condicoes)
    summary["ufs"] = ufs
    summary["condicoes"] = [c for c in condicoes if c.get("ativo_v1")]
    save_json(MART / "dashboard.json", summary)

    # espelhar para o app Next.js
    web_public = Path(__file__).resolve().parents[1] / "web" / "public" / "data"
    web_public.mkdir(parents=True, exist_ok=True)
    save_json(web_public / "dashboard.json", summary)
    save_json(web_public / "mart_gap_condicao_uf.json", {"linhas": gap_rows})
    save_json(
        web_public / "por_municipio.json",
        {
            "atualizado_em": summary["atualizado_em"],
            "fonte": numerador.get("fonte"),
            "linhas": summary.get("por_municipio") or [],
        },
    )
    save_json(MART / "por_municipio.json", {"linhas": summary.get("por_municipio") or []})

    print(f"Mart: {len(gap_rows)} linhas gap | dashboard.json gerado")
    return summary


if __name__ == "__main__":
    run()
