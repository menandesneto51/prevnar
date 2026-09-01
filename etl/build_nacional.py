"""Monta marts do dashboard nacional (oportunidade + novos indicadores)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from paths import MART, REF, ROOT

WEB_DATA = ROOT / "web" / "public" / "data"


def load(name: str, default=None):
    p = MART / name
    if not p.exists():
        p = REF / name
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def save_mart(name: str, payload) -> None:
    for base in (MART, WEB_DATA):
        base.mkdir(parents=True, exist_ok=True)
        (base / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"mart {name}")


def ipca_fator_acumulado(serie: list, ref_mes: str) -> float:
    """Fator multiplicativo IPCA acumulado após ref_mes (MM/AAAA)."""
    acc = 1.0
    past = False
    for pt in serie:
        if pt.get("data") == ref_mes:
            past = True
            continue
        if past:
            try:
                acc *= 1 + float(str(pt.get("valor", "0")).replace(",", ".")) / 100
            except ValueError:
                continue
    return round(acc, 6)


def build() -> dict:
    dash = load("dashboard.json", {})
    num = load("numerador.json", {})
    den = load("denominadores.json", {})
    pop = (den or {}).get("pop_ibge_2024") or {}
    sinan = load("sinan_meningite.json", {"linhas": []})
    sih = load("sih_pneumo.json", {"linhas": []})
    sim = load("sim_pneumo.json", {"linhas": []})
    srag = load("srag_pneumo.json", {"linhas": []})
    sies = load("sies.json", {})
    esavi = load("esavi.json", {})
    serie = load("serie_transicao_pneumo.json", {"linhas": []})
    qualidade_oferta = load("qualidade_oferta.json", {})
    ipca = load("ipca.json", {})
    bps = load("preco_bps_vpc20.json", {"preco_unitario": 180.0})
    siops = load("siops_per_capita_uf.json", {"por_uf": {}})
    indicadores = json.loads((REF / "indicadores_nacionais.json").read_text(encoding="utf-8"))
    extracao = load("plano_extracao_nacional.json", {})
    if not extracao:
        p = REF / "plano_extracao_nacional.json"
        if p.exists():
            extracao = json.loads(p.read_text(encoding="utf-8"))

    nacional = (dash or {}).get("nacional") or {}
    gap = nacional.get("gap") or 0
    vac = nacional.get("pessoas_vacinadas") or 0
    doses = nacional.get("total_doses") or vac
    preco_nominal = float(bps.get("preco_unitario") or 180)
    ref_raw = str(bps.get("referencia") or "2026-01")
    if "-" in ref_raw and len(ref_raw) >= 7:
        y, m = ref_raw.split("-", 1)
        ref_mes = f"01/{m}/{y}"  # formato BCB MM/AAAA com dia fixo
    else:
        ref_mes = ref_raw
    ipca_serie = (ipca.get("serie") or []) if isinstance(ipca, dict) else []
    ipca_fator = ipca_fator_acumulado(ipca_serie, ref_mes) if ipca_serie else 1.0
    preco = round(preco_nominal * ipca_fator, 2)
    custo_gap = round(gap * preco, 2)

    # Monitoramento por UF
    sinan_uf: dict[str, int] = {}
    for r in sinan.get("linhas") or []:
        sinan_uf[r["uf"]] = sinan_uf.get(r["uf"], 0) + int(r["casos"])
    sih_uf: dict[str, int] = {}
    for r in sih.get("linhas") or []:
        sih_uf[r["uf"]] = sih_uf.get(r["uf"], 0) + int(r["internacoes"])
    sim_uf: dict[str, int] = {}
    for r in sim.get("linhas") or []:
        sim_uf[r["uf"]] = sim_uf.get(r["uf"], 0) + int(r["obitos"])
    srag_uf: dict[str, int] = {}
    for r in srag.get("linhas") or []:
        srag_uf[r["uf"]] = srag_uf.get(r["uf"], 0) + int(r["casos"])

    pessoas_uf = num.get("pessoas_por_uf") or {}
    mon_rows = []
    ufs = sorted(
        set(pop) | set(pessoas_uf) | set(sinan_uf) | set(sih_uf) | set(sim_uf) | set(srag_uf)
    )
    for uf in ufs:
        if uf == "ND":
            continue
        p = int(pop.get(uf) or 0)
        v = int(pessoas_uf.get(uf) or 0)
        s = int(sinan_uf.get(uf) or 0)
        h = int(sih_uf.get(uf) or 0)
        o = int(sim_uf.get(uf) or 0)
        g = int(srag_uf.get(uf) or 0)
        casos = s + h
        mon_rows.append(
            {
                "uf": uf,
                "pop": p,
                "pessoas_vacinadas_vpc20": v,
                "sinan_casos": s,
                "sih_internacoes": h,
                "sim_obitos": o,
                "srag_casos": g,
                "sinan_100k": round(100000 * s / p, 2) if p else None,
                "sih_100k": round(100000 * h / p, 2) if p else None,
                "sim_100k": round(100000 * o / p, 2) if p else None,
                "srag_100k": round(100000 * g / p, 2) if p else None,
                "razao_doses_casos": round(v / casos, 2) if casos else None,
            }
        )

    # Estoque: SIES agregado ou seed
    sies_uf = sies.get("por_uf_distribuidas") or sies.get("por_uf_seed") or {}
    estoque_rows = []
    for uf, dist in sorted(sies_uf.items()):
        aplicada = int(pessoas_uf.get(uf) or 0)
        estoque_rows.append(
            {
                "uf": uf,
                "distribuidas": dist,
                "aplicadas": aplicada,
                "razao_dist_aplic": round(dist / aplicada, 2) if aplicada else None,
            }
        )
    # enriquecer com doses/CRIE
    oferta_by_uf = {r["uf"]: r for r in (qualidade_oferta.get("oferta_uf") or [])}
    for row in estoque_rows:
        of = oferta_by_uf.get(row["uf"]) or {}
        row["doses_por_crie"] = of.get("doses_por_crie")
        row["pct_fora_crie"] = of.get("pct_fora_crie")
        row["n_cries_seed"] = of.get("n_cries_seed")

    esavi_uf = esavi.get("por_uf") or {}
    esavi_100k = None
    total_esavi = sum(esavi_uf.values()) if esavi_uf else esavi.get("registros") or 0
    if doses:
        esavi_100k = round(100000 * total_esavi / max(doses, 1), 2)

    # Custo por UF
    custo_rows = []
    for u in (dash or {}).get("por_uf") or []:
        g = u.get("gap") or 0
        pc = (siops.get("por_uf") or {}).get(u["uf"])
        custo = round(g * preco, 2)
        pop_u = pop.get(u["uf"]) or 0
        pressao = None
        if pc and pop_u:
            gasto = pc * pop_u
            pressao = round(custo / gasto, 6) if gasto else None
        custo_rows.append(
            {
                "uf": u["uf"],
                "gap": g,
                "custo_gap_brl": custo,
                "siops_per_capita": pc,
                "pressao_fiscal_indice": pressao,
            }
        )

    # Cobertura Situação 1 (só condições com exibe_cobertura)
    cob_sit1 = []
    for c in (dash or {}).get("por_condicao") or []:
        if not c.get("exibe_cobertura"):
            continue
        cob_sit1.append(
            {
                "condicao_id": c["condicao_id"],
                "condicao_nt52": c["condicao_nt52"],
                "elegiveis": c.get("elegiveis"),
                "pessoas_vacinadas": c.get("pessoas_vacinadas"),
                "cobertura_pct": c.get("cobertura_pct"),
                "carga_pendente": c.get("carga_pendente"),
            }
        )

    # Gap por região de saúde (elegíveis UF rateados por pop RS)
    rs_src = load("regiao_saude.json", {})
    if not (rs_src or {}).get("municipios"):
        ref_rs = REF / "regiao_saude_municipios.json"
        if ref_rs.exists():
            rs_src = json.loads(ref_rs.read_text(encoding="utf-8"))
    mun_rs = (rs_src or {}).get("municipios") or {}
    eleg_uf = {u["uf"]: int(u.get("elegiveis") or 0) for u in (dash or {}).get("por_uf") or []}
    pop_rs_uf: dict[str, int] = {}
    for m in mun_rs.values():
        uf = m.get("uf") or "ND"
        pop_rs_uf[uf] = pop_rs_uf.get(uf, 0) + int(m.get("pop_ibge_2022") or 0)

    vac_rs: dict[str, int] = {}
    mun_vac_hit = 0
    for row in num.get("por_municipio") or []:
        mun = str(row.get("municipio_ibge") or "")[:6]
        meta = mun_rs.get(mun)
        if not meta:
            continue
        cod = meta.get("codigo_regiao_saude")
        if not cod:
            continue
        vac_rs[cod] = vac_rs.get(cod, 0) + int(row.get("pessoas_vacinadas") or 0)
        mun_vac_hit += 1

    gap_rs_rows = []
    for reg in (rs_src or {}).get("regioes") or []:
        cod = reg["codigo_regiao_saude"]
        uf = reg.get("uf") or "ND"
        pop_r = int(reg.get("pop_ibge_2022") or 0)
        pop_u = pop_rs_uf.get(uf) or 0
        eleg_u = eleg_uf.get(uf) or 0
        eleg_r = int(round(eleg_u * pop_r / pop_u)) if pop_u and eleg_u else 0
        vac_r = int(vac_rs.get(cod) or 0)
        gap_rs_rows.append(
            {
                "codigo_regiao_saude": cod,
                "regiao_saude": reg.get("regiao_saude"),
                "uf": uf,
                "macrorregiao_saude": reg.get("macrorregiao_saude"),
                "n_municipios": reg.get("n_municipios"),
                "pop_ibge_2022": pop_r,
                "elegiveis_rateados": eleg_r,
                "pessoas_vacinadas": vac_r,
                "gap": max(0, eleg_r - vac_r),
            }
        )
    gap_rs_rows.sort(key=lambda x: -x["gap"])

    pop_br = sum(int(v or 0) for k, v in pop.items() if k != "ND")
    sinan_br = sum(sinan_uf.values())
    sih_br = sum(sih_uf.values())
    sim_br = sum(sim_uf.values())
    srag_br = sum(srag_uf.values())
    esavi_manual = "manual" in str(esavi.get("fonte") or "").lower()

    # Valores atuais por indicador (para aba Indicadores)
    valores = {
        "elegiveis": nacional.get("elegiveis"),
        "pessoas_vacinadas_vpc20": vac,
        "pessoas_vacinadas_municipio": len(num.get("por_municipio") or []),
        "gap_absoluto": gap,
        "cobertura_sit1": cob_sit1,
        "share_transicao_pneumo": len(serie.get("linhas") or []),
        "sies_distribuida_aplicada": (
            round(sum(r["distribuidas"] for r in estoque_rows) / max(vac, 1), 2) if vac else None
        ),
        "doses_por_crie": qualidade_oferta.get("doses_por_crie_nacional"),
        "pct_fora_crie": qualidade_oferta.get("pct_fora_crie"),
        "taxa_cid_preenchido": nacional.get("taxa_cid_preenchido"),
        "atraso_rnds": (qualidade_oferta.get("atraso_rnds_dias") or {}).get("mediana"),
        "esavi_por_100k": esavi_100k,
        "sinan_meningite_100k": round(100000 * sinan_br / pop_br, 2) if pop_br else None,
        "sih_pneumo_100k": round(100000 * sih_br / pop_br, 2) if pop_br else None,
        "sim_pneumo_100k": round(100000 * sim_br / pop_br, 2) if pop_br else None,
        "srag_casos_100k": round(100000 * srag_br / pop_br, 2) if pop_br else None,
        "razao_doses_casos": (
            round(vac / max(sinan_br + sih_br, 1), 2) if (sinan_br + sih_br) else None
        ),
        "custo_gap": custo_gap,
        "pressao_fiscal_gap": (
            max((r.get("pressao_fiscal_indice") or 0) for r in custo_rows) if custo_rows else None
        ),
        "gap_regiao_saude": sum(r["gap"] for r in gap_rs_rows) if gap_rs_rows else None,
    }

    status_map = []
    for ind in indicadores.get("indicadores") or []:
        iid = ind["id"]
        val = valores.get(iid)
        if iid == "cobertura_sit1":
            if not cob_sit1 or any(c.get("carga_pendente") for c in cob_sit1):
                st = "parcial"
            elif nacional.get("sem_cid_na_fonte"):
                st = "parcial"  # elegíveis ok; vacinados Sit.1 dependem de CID (CKAN)
            else:
                st = "ok"
        elif iid == "gap_regiao_saude":
            st = "ok" if gap_rs_rows else "planejado"
        elif iid in ("esavi_por_100k",) and esavi_manual:
            st = "parcial"
        elif iid == "sies_distribuida_aplicada" and not sies.get("por_uf_vpc20"):
            st = "parcial"
        elif iid == "srag_casos_100k" and not (srag.get("linhas") or []):
            st = "sem_dado"
        elif val is None:
            st = "sem_dado"
        else:
            st = "ok"
        status_map.append(
            {
                "id": iid,
                "nome": ind.get("nome"),
                "familia": ind.get("familia"),
                "status": st,
                "valor": val if not isinstance(val, list) else f"{len(val)} itens",
                "unidade": ind.get("unidade"),
            }
        )

    nacional_payload = {
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
        "kpis": {
            "elegiveis": nacional.get("elegiveis"),
            "pessoas_vacinadas_vpc20": vac,
            "gap_absoluto": gap,
            "custo_gap_brl": custo_gap,
            "preco_bps_vpc20": preco,
            "preco_bps_nominal": preco_nominal,
            "ipca_fator_acumulado": ipca_fator,
            "ipca_referencia_bps": ref_mes,
            "esavi_total": total_esavi,
            "esavi_por_100k_doses": esavi_100k,
            "taxa_cid_preenchido": nacional.get("taxa_cid_preenchido"),
            "atraso_rnds_mediana_dias": (qualidade_oferta.get("atraso_rnds_dias") or {}).get(
                "mediana"
            ),
            "pct_fora_crie": qualidade_oferta.get("pct_fora_crie"),
            "doses_por_crie": qualidade_oferta.get("doses_por_crie_nacional"),
            "municipios_com_vacinado": len(num.get("por_municipio") or []),
            "regioes_saude": len(gap_rs_rows),
            "municipios_vac_com_rs": mun_vac_hit,
            "fonte_numerador": nacional.get("fonte_numerador"),
            "fonte_tipo": nacional.get("fonte_tipo"),
            "sem_cid_na_fonte": nacional.get("sem_cid_na_fonte"),
            "ipca_ultimo": ipca.get("ultimo"),
        },
        "monitoramento_uf": sorted(
            mon_rows,
            key=lambda x: -(x["sih_internacoes"] + x["sinan_casos"] + x["sim_obitos"] + x["srag_casos"]),
        ),
        "estoque_uf": estoque_rows,
        "sies_resumo": {
            "por_classe_insumo": sies.get("por_classe_insumo"),
            "nota": sies.get("nota"),
        },
        "oferta_uf": qualidade_oferta.get("oferta_uf") or [],
        "custo_uf": sorted(custo_rows, key=lambda x: -x["custo_gap_brl"]),
        "gap_regiao_saude": gap_rs_rows,
        "serie_transicao": serie,
        "cobertura_sit1": cob_sit1,
        "qualidade_oferta": qualidade_oferta,
        "indicadores_catalogo": indicadores,
        "indicadores_status": status_map,
        "plano_extracao": {
            "ordem": extracao.get("ordem_etl"),
            "abas": extracao.get("dashboard_nacional_abas"),
        },
        "qualidade": {
            "esavi_por_uf": esavi_uf,
            "sies_nota": sies.get("nota") or sies.get("erro"),
            "sinan_nota": sinan.get("nota"),
            "sih_nota": sih.get("nota"),
            "sim_nota": sim.get("nota"),
            "srag_nota": srag.get("nota"),
            "atraso_rnds_dias": qualidade_oferta.get("atraso_rnds_dias"),
            "regiao_saude_nota": (rs_src or {}).get("nota"),
            "regiao_saude_fonte": (rs_src or {}).get("fonte"),
        },
    }
    save_mart("nacional.json", nacional_payload)
    save_mart(
        "gap_regiao_saude.json",
        {
            "atualizado_em": nacional_payload["atualizado_em"],
            "nota": (rs_src or {}).get("nota"),
            "linhas": gap_rs_rows,
        },
    )

    # espelhar indicadores no public
    save_mart("indicadores_nacionais.json", indicadores)
    return nacional_payload


if __name__ == "__main__":
    # garantir extrações
    try:
        import extract_nacional

        extract_nacional.run(max_pages_aux=2)
    except Exception as exc:  # noqa: BLE001
        print(f"extract parcial: {exc}")
    out = build()
    print("KPIs", json.dumps(out["kpis"], ensure_ascii=False, indent=2))
    print("status", [(s["id"], s["status"]) for s in out.get("indicadores_status") or []])
