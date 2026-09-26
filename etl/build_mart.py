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


def _denominator_evidence(row: dict) -> str:
    if row.get("carga_pendente"):
        return "E5"
    situacao = row.get("situacao_denominador")
    if situacao == 1:
        return "E4"
    if situacao in (2, 3):
        return "E3"
    return "E5"


def _numerator_evidence(row: dict | None, numerador: dict) -> str:
    if row and row.get("evidence_level"):
        return str(row["evidence_level"])
    if numerador.get("fixture"):
        return "E5"
    return str(numerador.get("evidence_level_clinical_breakdown") or ("E2" if numerador.get("sem_cid_na_fonte") else "E1"))


def build_gap(denoms: list[dict], numerador: dict, condicoes: list[dict]) -> list[dict]:
    vac_map: dict[tuple[int, str], dict] = {}
    for r in numerador.get("linhas", []):
        vac_map[(r["condicao_id"], r["uf"])] = r

    cond_meta = {c["condicao_id"]: c for c in condicoes if c.get("ativo_v1", True)}
    rows = []
    for d in denoms:
        cid = d["condicao_id"]
        if cid not in cond_meta:
            continue
        uf = d["uf"]
        meta = cond_meta[cid]
        eleg = d.get("elegiveis")
        vac_row = vac_map.get((cid, uf))
        vac = int((vac_row or {}).get("pessoas_vacinadas") or 0)
        pendente = bool(d.get("carga_pendente"))
        numerator_evidence = _numerator_evidence(vac_row, numerador)
        denominator_evidence = _denominator_evidence(d)
        clinical_match_confirmed = bool(
            (vac_row or {}).get("clinical_match_confirmed", numerator_evidence == "E1")
        )
        gap = None if eleg is None else max(0, int(eleg) - vac)
        gap_decision_grade = bool(
            gap is not None
            and not pendente
            and clinical_match_confirmed
            and numerator_evidence != "E5"
            and denominator_evidence != "E5"
        )
        coverage_allowed = bool(
            meta.get("exibe_cobertura")
            and eleg
            and not pendente
            and int(eleg) > 0
            and gap_decision_grade
        )
        cobertura = round(100.0 * vac / int(eleg), 2) if coverage_allowed else None
        if numerator_evidence == "E5" or denominator_evidence == "E5":
            gap_evidence = "E5"
        elif not clinical_match_confirmed:
            gap_evidence = "E2"
        elif denominator_evidence == "E3":
            gap_evidence = "E3"
        elif denominator_evidence == "E4":
            gap_evidence = "E4"
        else:
            gap_evidence = "E1"

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
                "exibe_cobertura": coverage_allowed,
                "numerator_evidence_level": numerator_evidence,
                "denominator_evidence_level": denominator_evidence,
                "gap_evidence_level": gap_evidence,
                "gap_decision_grade": gap_decision_grade,
                "clinical_match_confirmed": clinical_match_confirmed,
                "gap_interpretation": (
                    "gap_condicao" if gap_decision_grade else "estimativa_nao_decisoria"
                ),
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
    # Soma por condição representa oportunidades estimadas e pode conter a mesma pessoa mais de uma vez.
    oportunidades_total = sum(r["elegiveis"] or 0 for r in gap_rows if r["elegiveis"] is not None)
    # O numerador nacional é de pessoas únicas vacinadas; não é comparável diretamente à soma acima.
    vac_total = numerador.get("total_pessoas", 0)
    gap_aproximado_legado = max(0, oportunidades_total - vac_total) if oportunidades_total else None

    por_condicao = []
    for c in ativos:
        subset = [r for r in gap_rows if r["condicao_id"] == c["condicao_id"]]
        eleg = sum(r["elegiveis"] or 0 for r in subset if r["elegiveis"] is not None)
        vac = sum(r["pessoas_vacinadas"] for r in subset)
        pendente = all(r["carga_pendente"] for r in subset) if subset else True
        raro = bool(c.get("raro"))
        fmt = format_elegiveis(None if (c["situacao_denominador"] == 1 and pendente) else eleg, raro)
        valid_rows = [r for r in subset if r.get("gap_decision_grade")]
        all_decision_grade = bool(subset) and len(valid_rows) == len(subset)
        cobertura = None
        if c.get("exibe_cobertura") and not pendente and eleg > 0 and all_decision_grade:
            cobertura = round(100.0 * vac / eleg, 2)
        evidence_levels = sorted({str(r.get("gap_evidence_level") or "E5") for r in subset})
        gap_evidence = evidence_levels[0] if len(evidence_levels) == 1 else "/".join(evidence_levels)
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
                "exibe_cobertura": bool(c.get("exibe_cobertura")) and not pendente and all_decision_grade,
                "gap_evidence_level": gap_evidence,
                "gap_decision_grade": all_decision_grade and not pendente,
                "gap_interpretation": (
                    "gap_condicao" if all_decision_grade and not pendente else "estimativa_nao_decisoria"
                ),
                "carga_pendente": c["situacao_denominador"] == 1 and pendente,
                "raro": raro,
            }
        )

    por_uf: dict[str, dict] = {}
    for r in gap_rows:
        uf = r["uf"]
        bucket = por_uf.setdefault(
            uf,
            {
                "uf": uf,
                "elegiveis": 0,
                "oportunidades_estimadas": 0,
                "pessoas_vacinadas": 0,
                "gap": None,
                "gap_pessoas": None,
                "gap_aproximado_legado": 0,
                "pendencias": 0,
            },
        )
        if r["elegiveis"] is not None:
            bucket["elegiveis"] += r["elegiveis"]
            bucket["oportunidades_estimadas"] += r["elegiveis"]
            bucket["gap_aproximado_legado"] += r["gap"] or 0
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
            if por_uf[uf]["oportunidades_estimadas"]:
                por_uf[uf]["gap_aproximado_legado"] = max(
                    0, por_uf[uf]["oportunidades_estimadas"] - n
                )

    return {
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
        "nacional": {
            "elegiveis": oportunidades_total,
            "oportunidades_estimadas": oportunidades_total,
            "pessoas_vacinadas": vac_total,
            "gap": None,
            "gap_pessoas": None,
            "gap_aproximado_legado": gap_aproximado_legado,
            "gap_pessoas_disponivel": False,
            "nota_oportunidades": (
                "Soma de elegíveis por condição; pode conter sobreposição entre indivíduos. "
                "Não equivale a pessoas únicas elegíveis."
            ),
            "taxa_cid_preenchido": numerador.get("taxa_cid_preenchido"),
            "total_doses": numerador.get("total_doses"),
            "fixture": numerador.get("fixture", False),
            "fonte_numerador": numerador.get("fonte"),
            "fonte_tipo": numerador.get("fonte_tipo"),
            "sem_cid_na_fonte": numerador.get("sem_cid_na_fonte", False),
            "evidence_level_total": numerador.get("evidence_level_total", "E1"),
            "evidence_level_clinical_breakdown": numerador.get(
                "evidence_level_clinical_breakdown",
                "E2" if numerador.get("sem_cid_na_fonte") else "E1",
            ),
            "decision_grade_clinical_breakdown": numerador.get(
                "decision_grade_clinical_breakdown", False
            ),
        },
        "por_condicao": sorted(por_condicao, key=lambda x: -(x["gap"] or 0)),
        "por_uf": sorted(
            por_uf.values(), key=lambda x: -x["oportunidades_estimadas"]
        ),
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
    timeline = {
        "atualizado_em": summary["atualizado_em"],
        "fonte": numerador.get("fonte"),
        "fonte_arquivos": numerador.get("fonte_arquivos") or [],
        "periodo": numerador.get("periodo") or {},
        "linha_tempo": numerador.get("linha_tempo") or [],
        "total_doses": numerador.get("total_doses"),
        "total_pessoas": numerador.get("total_pessoas"),
        "nota": (
            "Doses VPC20 (co_vacina=107), idade≥5, data≥início campanha. "
            "Meses = dt_vacina (YYYY-MM). Acumulado = soma progressiva."
        ),
    }
    save_json(MART / "vpc20_timeline.json", timeline)
    save_json(web_public / "vpc20_timeline.json", timeline)
    save_json(MART / "por_municipio.json", {"linhas": summary.get("por_municipio") or []})

    print(f"Mart: {len(gap_rows)} linhas gap | dashboard.json gerado")
    return summary


if __name__ == "__main__":
    run()
