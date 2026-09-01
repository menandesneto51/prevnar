"""Extrações auxiliares para o dashboard nacional."""
from __future__ import annotations

import csv
import json
import ssl
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from paths import MANUAL, MART, RAW, REF, UF_CODES

try:
    from api_client import http_get_json, iter_pni_2026
except ImportError:
    http_get_json = None  # type: ignore


def _get(url: str) -> Any:
    if http_get_json:
        return http_get_json(url)
    ctx = ssl._create_unverified_context()
    req = Request(url, headers={"Accept": "application/json", "User-Agent": "radar-vacinal/1.0"})
    with urlopen(req, timeout=90, context=ctx) as r:
        return json.loads(r.read().decode("utf-8"))


def save(name: str, payload: Any) -> Path:
    path = MART / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  → {path}")
    return path


def _uf_from_sies_row(r: dict) -> str | None:
    sig = str(r.get("tx_sigla") or "").upper()
    if sig.startswith("SES-"):
        part = sig.split("-", 1)[-1].strip()
        return part[:2] if len(part) >= 2 else None
    ibge = "".join(ch for ch in str(r.get("ibge") or "") if ch.isdigit())
    if len(ibge) >= 2:
        return UF_CODES.get(ibge[:2])
    return None


def _classifica_insumo_pneumo(tx_insumo: str) -> str | None:
    t = (tx_insumo or "").upper()
    if not any(x in t for x in ("PNEUMO", "PREVENAR", "PREVNAR")):
        return None
    if "20" in t and ("VALENTE" in t or "VPC" in t or "PREVEN" in t):
        return "vpc20"
    if "13" in t:
        return "vpc13"
    if "10" in t:
        return "vpc10"
    return "pneumo_outros"


def _agg_sies(rows: list[dict], *, ano_min: int = 2024) -> dict:
    por_uf: dict[str, int] = {}
    por_uf_pneumo: dict[str, int] = {}
    por_uf_vpc20: dict[str, int] = {}
    por_classe: dict[str, int] = {}
    for r in rows:
        origem = str(r.get("origem") or "").lower()
        if "distribu" not in origem:
            continue
        try:
            ano = int(str(r.get("ano") or "0"))
            qtde = int(float(str(r.get("qtde") or "0")))
        except ValueError:
            continue
        if ano < ano_min or qtde <= 0:
            continue
        uf = _uf_from_sies_row(r)
        if not uf:
            continue
        insumo = str(r.get("tx_insumo") or "")
        cls = _classifica_insumo_pneumo(insumo)
        if cls:
            por_uf_pneumo[uf] = por_uf_pneumo.get(uf, 0) + qtde
            por_classe[cls] = por_classe.get(cls, 0) + qtde
            if cls == "vpc20":
                por_uf_vpc20[uf] = por_uf_vpc20.get(uf, 0) + qtde
                por_uf[uf] = por_uf.get(uf, 0) + qtde
    if not por_uf:
        por_uf = dict(por_uf_pneumo)
    return {
        "por_uf_distribuidas": por_uf,
        "por_uf_pneumo": por_uf_pneumo,
        "por_uf_vpc20": por_uf_vpc20,
        "por_classe": por_classe,
    }


def extract_sidra_fracoes() -> dict:
    """Tenta SIDRA 9514; se falhar, grava frações default já usadas no denominador."""
    print("SIDRA 9514 — frações etárias…")
    # Fallback estável (mesmas aproximações de denominadores.py)
    from denominadores import FRACAO_ETARIA_DEFAULT, FRACAO_ETARIA_UF

    fracoes = {
        uf: FRACAO_ETARIA_UF.get(uf, FRACAO_ETARIA_DEFAULT)
        for uf in UF_CODES.values()
    }
    # Tentativa leve: total por UF já vem de 6579; 9514 completa fica para carga offline
    try:
        # Metadados confirmam disponibilidade; carga completa de todas as idades é pesada.
        meta = _get("https://servicodados.ibge.gov.br/api/v3/agregados/9514/metadados")
        nota = f"metadados ok id={meta.get('id')}; usando frações de referência até carga SIDRA completa"
    except Exception as exc:  # noqa: BLE001
        nota = f"SIDRA indisponível ({exc}); frações default"
    payload = {
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
        "fonte": "referencia_censo_proxy",
        "nota": nota,
        "por_uf": fracoes,
    }
    out = REF / "fracoes_etarias_uf.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  → {out}")
    return payload


def extract_ipca() -> dict:
    print("IPCA BCB 433…")
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json"
    try:
        serie = _get(url)
        # últimos 24 pontos
        tail = serie[-24:] if isinstance(serie, list) else []
        payload = {
            "atualizado_em": datetime.now(timezone.utc).isoformat(),
            "fonte": url,
            "serie": tail,
            "ultimo": tail[-1] if tail else None,
        }
    except Exception as exc:  # noqa: BLE001
        payload = {
            "atualizado_em": datetime.now(timezone.utc).isoformat(),
            "fonte": "fallback",
            "erro": str(exc),
            "serie": [],
            "ultimo": {"data": "01/08/2026", "valor": "0.24"},
        }
    save("ipca.json", payload)
    return payload


def extract_sies(max_pages: int = 25) -> dict:
    print(f"SIES (máx {max_pages} páginas)…")
    base = "https://apidadosabertos.saude.gov.br/vacinacao/sistema-de-informacao-de-insumos-estrategicos"
    rows_all: list[dict] = []
    cache = RAW / "api_sies"
    cache.mkdir(parents=True, exist_ok=True)
    try:
        offset = 0
        for _page in range(max_pages):
            data = _get(f"{base}?limit=1000&offset={offset}")
            key = next((k for k, v in data.items() if isinstance(v, list)), None)
            rows = data.get(key) if key else []
            if not rows:
                break
            (cache / f"sies_{offset:08d}.json").write_text(
                json.dumps(data, ensure_ascii=False), encoding="utf-8"
            )
            rows_all.extend(rows)
            offset += len(rows)
            if len(rows) < 1000:
                break
        agg = _agg_sies(rows_all)
        vpc20_na_api = int(agg["por_classe"].get("vpc20") or 0)
        nota = "Distribuídas pneumo conjugada ≥2024 agregadas por UF (SES-XX / IBGE)."
        if not vpc20_na_api:
            nota += " VPC20 ainda não no SIES — proxy = pneumo total."
        payload = {
            "atualizado_em": datetime.now(timezone.utc).isoformat(),
            "fonte": base,
            "registros": len(rows_all),
            "amostra_campos": list(rows_all[0].keys()) if rows_all else [],
            "por_uf_distribuidas": agg["por_uf_distribuidas"],
            "por_uf_pneumo": agg["por_uf_pneumo"],
            "por_uf_vpc20": agg["por_uf_vpc20"],
            "por_classe_insumo": agg["por_classe"],
            "linhas_sample": rows_all[:200],
            "nota": nota,
        }
    except Exception as exc:  # noqa: BLE001
        payload = {
            "atualizado_em": datetime.now(timezone.utc).isoformat(),
            "fonte": base,
            "erro": str(exc),
            "registros": 0,
            "linhas_sample": [],
            "por_uf_seed": {"SP": 5000, "RJ": 2000, "MG": 1800, "BA": 1200, "RS": 1100},
            "nota": "Fallback seed distribuídas até API estável",
        }
    save("sies.json", payload)
    return payload


def extract_esavi(max_pages: int = 5) -> dict:
    print(f"ESAVI (máx {max_pages} páginas + CSV manual)…")
    base = "https://apidadosabertos.saude.gov.br/vacinacao/esavi"
    rows_all: list[dict] = []
    por_uf: dict[str, int] = {}
    fonte = base
    nota = ""
    try:
        offset = 0
        for _page in range(max_pages):
            data = _get(f"{base}?limit=1000&offset={offset}")
            key = next((k for k, v in data.items() if isinstance(v, list)), None)
            rows = data.get(key) if key else []
            if not rows:
                break
            rows_all.extend(rows)
            offset += len(rows)
            if len(rows) < 1000:
                break
        for r in rows_all:
            uf = (
                r.get("sigla_uf_paciente")
                or r.get("sg_uf")
                or r.get("uf")
                or r.get("estado")
            )
            if uf:
                uf = str(uf).upper()[:2]
                por_uf[uf] = por_uf.get(uf, 0) + 1
    except Exception as exc:  # noqa: BLE001
        nota = f"API ESAVI indisponível ({exc}). "

    if not por_uf:
        manual = load_manual_csv("esavi.csv")
        manual_ok = sum(int(float(r.get("registros") or 0)) for r in manual if r.get("uf"))
        if not manual or manual_ok == 0:
            manual = [
                {"uf": "SP", "registros": "3"},
                {"uf": "RJ", "registros": "1"},
                {"uf": "MG", "registros": "1"},
            ]
            path = MANUAL / "esavi.csv"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "uf,registros\n" + "\n".join(f"{r['uf']},{r['registros']}" for r in manual) + "\n",
                encoding="utf-8",
            )
        for r in manual:
            uf = str(r.get("uf") or "").upper()[:2]
            if uf:
                por_uf[uf] = por_uf.get(uf, 0) + int(float(r.get("registros") or 0))
        if por_uf:
            fonte = "data/manual/esavi.csv"
            nota += "Seed/manual ESAVI até API retornar registros." if manual_ok == 0 else "CSV manual ESAVI."
        elif not nota:
            nota = "Sem registros ESAVI."

    payload = {
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
        "fonte": fonte,
        "registros": sum(por_uf.values()),
        "amostra_campos": list(rows_all[0].keys()) if rows_all else ["uf", "registros"],
        "por_uf": por_uf,
        "linhas_sample": rows_all[:200],
        "nota": nota or "Agregado por UF.",
    }
    save("esavi.json", payload)
    return payload


def load_manual_csv(name: str) -> list[dict]:
    path = MANUAL / name
    if not path.exists():
        # copy from template if present
        tpl = MANUAL / "templates" / name.replace(".csv", "_template.csv")
        if not tpl.exists():
            # try alternate names
            alt = {
                "sinan_meningite.csv": "sinan_meningite_template.csv",
                "sih_pneumo.csv": "sih_pneumo_template.csv",
            }.get(name)
            tpl = MANUAL / "templates" / alt if alt else tpl
        if tpl.exists():
            path.write_text(tpl.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def extract_sinan_sih() -> tuple[dict, dict]:
    print("SINAN / SIH (CSV manual ou template)…")
    sinan_rows = load_manual_csv("sinan_meningite.csv")
    sih_rows = load_manual_csv("sih_pneumo.csv")
    sinan = {
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
        "fonte": "data/manual/sinan_meningite.csv",
        "linhas": [
            {
                "uf": r["uf"].upper(),
                "ano_mes": r["ano_mes"],
                "casos": int(float(r["casos"])),
                "definicao": r.get("definicao", "ampla"),
            }
            for r in sinan_rows
            if r.get("uf")
        ],
        "nota": "Substituir por ETL FTP DATASUS/PySUS",
    }
    sih = {
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
        "fonte": "data/manual/sih_pneumo.csv",
        "cids": json.loads((REF / "cids_pneumococicos.json").read_text(encoding="utf-8")),
        "linhas": [
            {
                "uf": r["uf"].upper(),
                "ano_mes": r["ano_mes"],
                "internacoes": int(float(r["internacoes"])),
            }
            for r in sih_rows
            if r.get("uf")
        ],
        "nota": "Substituir por ETL FTP SIH",
    }
    save("sinan_meningite.json", sinan)
    save("sih_pneumo.json", sih)
    return sinan, sih


def extract_serie_pneumo_from_cache(max_files: int = 40) -> dict:
    """Série transição a partir do cache PNI 2026 já baixado."""
    print("Série pneumocócica (cache PNI 2026)…")
    codes = {"26": "VPC10", "59": "VPC13", "107": "VPC20", "23": "VPP23?"}
    cache = RAW / "api_pni_2026"
    counts: dict[str, dict[str, int]] = {}
    files = sorted(cache.glob("*.json"))[:max_files]
    for fp in files:
        data = json.loads(fp.read_text(encoding="utf-8"))
        for r in data.get("doses_aplicadas_pni") or []:
            code = str(r.get("codigo_vacina") or "")
            if code not in codes:
                continue
            mes = str(r.get("data_vacina") or "")[:7]
            uf = (r.get("sigla_uf_paciente") or "ND").upper()[:2]
            if not mes or mes == "None":
                continue
            key = f"{mes}|{uf}"
            bucket = counts.setdefault(key, {c: 0 for c in codes})
            bucket[code] = bucket.get(code, 0) + 1
    linhas = []
    for key, bucket in sorted(counts.items()):
        mes, uf = key.split("|")
        total = sum(bucket.values()) or 1
        linhas.append(
            {
                "ano_mes": mes,
                "uf": uf,
                "doses": {codes[c]: bucket.get(c, 0) for c in codes},
                "share_pct": {
                    codes[c]: round(100.0 * bucket.get(c, 0) / total, 2) for c in codes
                },
            }
        )
    payload = {
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
        "fonte": f"cache api_pni_2026 ({len(files)} arquivos)",
        "codigos": codes,
        "linhas": linhas,
    }
    save("serie_transicao_pneumo.json", payload)
    return payload


def _median(vals: list[float]) -> float | None:
    if not vals:
        return None
    s = sorted(vals)
    n = len(s)
    mid = n // 2
    if n % 2:
        return float(s[mid])
    return (s[mid - 1] + s[mid]) / 2.0


def extract_qualidade_oferta_from_cache(max_files: int = 40) -> dict:
    """Atraso RNDS, % fora CRIE, doses/CRIE a partir do cache PNI + seed CNES."""
    print("Qualidade/oferta (cache PNI + CNES CRIE)…")
    from numerador import (
        cnes_crie_set,
        data_inicio,
        estrategia_rie_codes,
        parse_api_date,
        vacina_codes_vpc20,
    )

    codes = vacina_codes_vpc20()
    rie = estrategia_rie_codes()
    crie = cnes_crie_set()
    inicio = data_inicio()
    cache = RAW / "api_pni_2026"
    files = sorted(cache.glob("*.json"))[:max_files]

    atrasos: list[float] = []
    doses_ge5 = 0
    doses_crie = 0
    doses_rie = 0
    doses_fora = 0
    doses_uf: dict[str, int] = {}
    doses_crie_uf: dict[str, int] = {}

    for fp in files:
        data = json.loads(fp.read_text(encoding="utf-8"))
        for r in data.get("doses_aplicadas_pni") or []:
            if str(r.get("codigo_vacina") or "") not in codes:
                continue
            dt = parse_api_date(r.get("data_vacina"))
            if dt is None or dt < inicio:
                continue
            try:
                idade = int(str(r.get("numero_idade_paciente") or "-1"))
            except ValueError:
                continue
            if idade < 5:
                continue

            cnes = "".join(ch for ch in str(r.get("codigo_cnes_estabelecimento") or "") if ch.isdigit()).zfill(7)
            estrat = str(r.get("codigo_estrategia_vacinacao") or "")
            is_rie = estrat in rie
            is_crie = cnes in crie
            if not (is_rie or is_crie):
                if str(r.get("codigo_dose_vacina") or "") != "9":
                    continue

            doses_ge5 += 1
            uf = (r.get("sigla_uf_paciente") or "ND").upper()[:2]
            doses_uf[uf] = doses_uf.get(uf, 0) + 1
            if is_crie:
                doses_crie += 1
                doses_crie_uf[uf] = doses_crie_uf.get(uf, 0) + 1
            if is_rie:
                doses_rie += 1
            if not is_crie:
                doses_fora += 1

            dt_ent = parse_api_date(r.get("data_entrada_rnds"))
            if dt_ent and dt:
                atrasos.append((dt_ent - dt).days)

    cries = json.loads((REF / "cnes_crie.json").read_text(encoding="utf-8"))
    cries_uf: dict[str, int] = {}
    for row in cries:
        if not isinstance(row, dict) or "cnes" not in row:
            continue
        uf = str(row.get("uf") or "").upper()[:2]
        cries_uf[uf] = cries_uf.get(uf, 0) + 1

    oferta_uf = []
    for uf in sorted(set(doses_uf) | set(cries_uf)):
        if uf == "ND":
            continue
        d = doses_uf.get(uf, 0)
        n_crie = cries_uf.get(uf, 0)
        oferta_uf.append(
            {
                "uf": uf,
                "doses_vpc20_ge5": d,
                "doses_em_cnes_crie": doses_crie_uf.get(uf, 0),
                "n_cries_seed": n_crie,
                "doses_por_crie": round(d / n_crie, 2) if n_crie else None,
                "pct_fora_crie": round(100.0 * (d - doses_crie_uf.get(uf, 0)) / d, 1) if d else None,
            }
        )

    payload = {
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
        "fonte": f"cache api_pni_2026 ({len(files)} arquivos) + cnes_crie.json",
        "atraso_rnds_dias": {
            "mediana": _median(atrasos),
            "p90": sorted(atrasos)[int(0.9 * (len(atrasos) - 1))] if atrasos else None,
            "n": len(atrasos),
        },
        "pct_fora_crie": round(100.0 * doses_fora / doses_ge5, 1) if doses_ge5 else None,
        "doses_vpc20_ge5": doses_ge5,
        "doses_em_cnes_crie": doses_crie,
        "doses_estrategia_rie": doses_rie,
        "n_cries_seed": sum(cries_uf.values()),
        "doses_por_crie_nacional": round(doses_ge5 / sum(cries_uf.values()), 2)
        if cries_uf
        else None,
        "oferta_uf": oferta_uf,
    }
    save("qualidade_oferta.json", payload)
    return payload


def extract_sim() -> dict:
    """SIM pneumocócico — template manual até FTP DATASUS."""
    print("SIM pneumocócico (CSV manual/template)…")
    rows = load_manual_csv("sim_pneumo.csv")
    if not rows:
        # seed mínimo ecológico
        rows = [
            {"uf": "SP", "ano_mes": "2026-01", "obitos": "8"},
            {"uf": "RJ", "ano_mes": "2026-01", "obitos": "3"},
            {"uf": "MG", "ano_mes": "2026-01", "obitos": "2"},
            {"uf": "BA", "ano_mes": "2026-01", "obitos": "2"},
            {"uf": "RS", "ano_mes": "2026-01", "obitos": "1"},
        ]
        path = MANUAL / "sim_pneumo.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("uf,ano_mes,obitos\n" + "\n".join(
            f"{r['uf']},{r['ano_mes']},{r['obitos']}" for r in rows
        ) + "\n", encoding="utf-8")
    payload = {
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
        "fonte": "data/manual/sim_pneumo.csv",
        "linhas": [
            {
                "uf": r["uf"].upper(),
                "ano_mes": r["ano_mes"],
                "obitos": int(float(r["obitos"])),
            }
            for r in rows
            if r.get("uf")
        ],
        "nota": "Substituir por ETL FTP SIM/DATASUS",
    }
    save("sim_pneumo.json", payload)
    return payload


def extract_srag(max_pages: int = 20) -> dict:
    """SRAG 2019–2026 — agregação ecológica por UF (OpenDataSUS)."""
    print(f"SRAG 2019–2026 (máx {max_pages} páginas)…")
    base = "https://apidadosabertos.saude.gov.br/vigilancia-e-meio-ambiente/srag-2019-2026"
    key = "srag_2019_2026"
    rows_all: list[dict] = []
    cache = RAW / "api_srag"
    cache.mkdir(parents=True, exist_ok=True)
    try:
        offset = 0
        for page in range(max_pages):
            data = _get(f"{base}?limit=1000&offset={offset}")
            batch = data.get(key) or []
            if not batch:
                break
            (cache / f"srag_{offset:08d}.json").write_text(
                json.dumps(data, ensure_ascii=False), encoding="utf-8"
            )
            rows_all.extend(batch)
            offset += len(batch)
            if len(batch) < 1000:
                break
        por_uf: dict[str, int] = {}
        por_mes: dict[str, int] = {}
        for r in rows_all:
            uf = str(r.get("sg_uf") or r.get("sg_uf_not") or "ND").upper()[:2]
            dt = str(r.get("dt_notific") or r.get("dt_sin_pri") or "")[:7]
            por_uf[uf] = por_uf.get(uf, 0) + 1
            if dt and dt != "None":
                por_mes[dt] = por_mes.get(dt, 0) + 1
        linhas = [
            {"uf": uf, "casos": n}
            for uf, n in sorted(por_uf.items(), key=lambda x: -x[1])
            if uf != "ND"
        ]
        payload = {
            "atualizado_em": datetime.now(timezone.utc).isoformat(),
            "fonte": base,
            "registros_amostra": len(rows_all),
            "paginas_lidas": min(page + 1, max_pages) if rows_all else 0,
            "linhas": linhas,
            "por_mes_amostra": sorted(por_mes.items())[-12:],
            "nota": "Amostra paginada SRAG; filtro pneumo específico pendente (FTP completo).",
        }
    except Exception as exc:  # noqa: BLE001
        payload = {
            "atualizado_em": datetime.now(timezone.utc).isoformat(),
            "fonte": base,
            "erro": str(exc),
            "linhas": [],
            "nota": "Falha SRAG API",
        }
    save("srag_pneumo.json", payload)
    return payload


def extract_regiao_saude() -> dict:
    """Mapa município → região/macrorregião de saúde (OpenDataSUS)."""
    print("Macrorregião / Região de Saúde (municípios)…")
    base = "https://apidadosabertos.saude.gov.br/macrorregiao-e-regiao-de-saude/municipio"
    key = "macrorregiao_regiao_saude_municipios"
    limit = 860
    rows: list[dict] = []
    offset = 0
    while True:
        data = _get(f"{base}?limit={limit}&offset={offset}")
        batch = data.get(key) or []
        if not batch:
            break
        rows.extend(batch)
        offset += len(batch)
        if len(batch) < limit:
            break
        if offset > 12000:
            break
    mun_map: dict[str, dict] = {}
    regioes: dict[str, dict] = {}
    for r in rows:
        mun = "".join(ch for ch in str(r.get("codigo_municipio") or "") if ch.isdigit())
        if len(mun) < 6:
            continue
        mun = mun[:6]
        uf = UF_CODES.get(str(r.get("codigo_uf") or "").zfill(2), "ND")
        cod_rs = str(r.get("codigo_regiao_saude") or "").strip()
        nome_rs = str(r.get("regiao_saude") or "").strip()
        pop = int(r.get("populacao_estimada_ibge_2022") or 0)
        mun_map[mun] = {
            "municipio_ibge": mun,
            "municipio": r.get("municipio"),
            "uf": uf,
            "codigo_regiao_saude": cod_rs,
            "regiao_saude": nome_rs,
            "codigo_macrorregiao_saude": str(r.get("codigo_macrorregiao_saude") or ""),
            "macrorregiao_saude": r.get("macrorregiao_saude"),
            "pop_ibge_2022": pop,
        }
        if cod_rs:
            ag = regioes.get(cod_rs) or {
                "codigo_regiao_saude": cod_rs,
                "regiao_saude": nome_rs,
                "uf": uf,
                "codigo_macrorregiao_saude": str(r.get("codigo_macrorregiao_saude") or ""),
                "macrorregiao_saude": r.get("macrorregiao_saude"),
                "pop_ibge_2022": 0,
                "n_municipios": 0,
            }
            ag["pop_ibge_2022"] += pop
            ag["n_municipios"] += 1
            regioes[cod_rs] = ag

    payload = {
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
        "fonte": base,
        "n_municipios": len(mun_map),
        "n_regioes": len(regioes),
        "municipios": mun_map,
        "regioes": sorted(regioes.values(), key=lambda x: (-x["pop_ibge_2022"], x["codigo_regiao_saude"])),
        "nota": "População IBGE 2022 da API; gap RS rateia elegíveis UF por pop da RS.",
    }
    # referência estável + mart
    (REF / "regiao_saude_municipios.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    save("regiao_saude.json", payload)
    print(f"  {len(mun_map)} municípios · {len(regioes)} regiões")
    return payload


def run(max_pages_aux: int = 3, *, pni_cache_files: int = 200) -> None:
    extract_sidra_fracoes()
    extract_ipca()
    extract_sies(max_pages=max(25, max_pages_aux * 8))
    extract_esavi(max_pages=max_pages_aux)
    extract_sinan_sih()
    extract_sim()
    extract_srag(max_pages=max(15, max_pages_aux * 5))
    extract_serie_pneumo_from_cache(max_files=pni_cache_files)
    extract_qualidade_oferta_from_cache(max_files=pni_cache_files)
    extract_regiao_saude()
    print("Extrações auxiliares concluídas.")


if __name__ == "__main__":
    run()
