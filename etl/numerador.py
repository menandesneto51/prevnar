"""Numerador VPC20 CRIE — OpenDataSUS API PNI 2026, CSV ou fixture."""
from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path

from api_client import iter_pni_2026
from paths import MART, RAW, REF, UF_CODES

try:
    import duckdb
except ImportError:  # pragma: no cover
    duckdb = None  # type: ignore

VACINA_PATTERNS = ["%VPC20%", "%Prevenar 20%", "%PREVENAR 20%", "%Prevnar 20%"]
API_CACHE = RAW / "api_pni_2026"


def data_inicio() -> date:
    env = os.environ.get("RADAR_DATA_INICIO", "").strip()
    if env:
        return date.fromisoformat(env)
    try:
        meta = load_json("vacinas_pni.json")
        return date.fromisoformat(meta.get("data_inicio_padrao", "2026-05-01"))
    except Exception:  # noqa: BLE001
        return date(2026, 5, 1)


def load_json(name: str):
    with open(REF / name, encoding="utf-8") as f:
        return json.load(f)


def save_numerador(payload: dict) -> dict:
    out = MART / "numerador.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Escrito {out}")
    return payload


def cnes_crie_set() -> set[str]:
    rows = load_json("cnes_crie.json")
    return {str(r["cnes"]).zfill(7) for r in rows if isinstance(r, dict) and "cnes" in r}


def vacina_codes_vpc20() -> set[str]:
    meta = load_json("vacinas_pni.json")
    return {str(c) for c in meta["vpc20"]["codigo_vacina"]}


def estrategia_rie_codes() -> set[str]:
    meta = load_json("vacinas_pni.json")
    return {str(c) for c in meta["estrategia_especial_rie"]["codigo_estrategia_vacinacao"]}


def normalize_cid(cid: str | None) -> str | None:
    if not cid:
        return None
    c = re.sub(r"[^A-Za-z0-9]", "", str(cid).upper())
    return c or None


def map_cid_to_condicao(cid: str, mapping: list[dict]) -> dict | None:
    cid_n = normalize_cid(cid)
    if not cid_n:
        return None
    best = None
    best_len = -1
    best_prio = -1
    for m in mapping:
        pref = re.sub(r"[^A-Za-z0-9]", "", m["cid_prefixo"].upper())
        if cid_n.startswith(pref):
            plen = len(pref)
            prio = m.get("prioridade", 0)
            if plen > best_len or (plen == best_len and prio > best_prio):
                best = m
                best_len = plen
                best_prio = prio
    return best


def uf_from_ibge_mun(codigo: str | None) -> str | None:
    if not codigo:
        return None
    c = str(codigo).strip()
    if len(c) >= 2:
        return UF_CODES.get(c[:2])
    return None


def normalize_mun_ibge(codigo: str | None) -> str | None:
    """IBGE município: API DEMAS costuma vir com 6 dígitos; malha usa 7."""
    if codigo is None:
        return None
    digits = re.sub(r"\D", "", str(codigo))
    if not digits:
        return None
    if len(digits) >= 7:
        return digits[:7]
    if len(digits) == 6:
        return digits
    return digits.zfill(6)


def parse_api_date(value: str | None) -> date | None:
    if not value:
        return None
    s = str(value).strip()
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


def discover_vacina_nomes(con, csv_path: Path) -> list[str]:
    # CKAN usa sg_imunobiologico / ds_nome; dumps antigos usam vacina_nome
    for col in ("sg_imunobiologico", "ds_nome", "vacina_nome"):
        q = f"""
        SELECT DISTINCT "{col}"
        FROM read_csv_auto('{csv_path.as_posix()}', delim=';', header=true, ignore_errors=true, sample_size=200000)
        WHERE CAST("{col}" AS VARCHAR) ILIKE '%VPC20%'
           OR CAST("{col}" AS VARCHAR) ILIKE '%Prevenar 20%'
           OR CAST("{col}" AS VARCHAR) ILIKE '%Prevnar 20%'
           OR CAST("{col}" AS VARCHAR) ILIKE '%pneumoc%'
        ORDER BY 1
        """
        try:
            rows = [r[0] for r in con.execute(q).fetchall() if r[0]]
            if rows:
                return rows
        except Exception as exc:  # noqa: BLE001
            print(f"Discovery parcial ({col}) falhou: {exc}")
            continue
    return []


def find_csv_paths() -> list[Path]:
    seen: set[str] = set()
    out: list[Path] = []
    for p in sorted(RAW.glob("pni_vpc20*.csv")) + sorted(RAW.glob("pni_vpc20*.CSV")):
        key = str(p.resolve()).lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    if out:
        return out
    candidates = sorted(RAW.glob("*.csv")) + sorted(RAW.glob("*.CSV"))
    return candidates[:1] if candidates else []


def find_csv() -> Path | None:
    paths = find_csv_paths()
    return paths[-1] if paths else None


def build_linha_tempo(df, *, col_data: str = "data_aplicacao") -> list[dict]:
    """Série mensal VPC20: doses no mês, pessoas no mês e acumulados."""
    doses_por_mes: dict[str, int] = {}
    pessoas_por_mes: dict[str, set[str]] = {}
    for _, row in df.iterrows():
        raw = row.get(col_data)
        mes = str(raw)[:7] if raw is not None and str(raw) not in ("", "nan", "None") else ""
        if len(mes) != 7 or mes[4] != "-":
            continue
        doses_por_mes[mes] = doses_por_mes.get(mes, 0) + 1
        pessoas_por_mes.setdefault(mes, set()).add(str(row["paciente_id"]))

    pessoas_acum: set[str] = set()
    doses_acum = 0
    out: list[dict] = []
    for mes in sorted(doses_por_mes):
        doses_mes = doses_por_mes[mes]
        doses_acum += doses_mes
        pessoas_mes = pessoas_por_mes.get(mes, set())
        pessoas_acum |= pessoas_mes
        out.append(
            {
                "ano_mes": mes,
                "doses_mes": doses_mes,
                "pessoas_mes": len(pessoas_mes),
                "doses_acumuladas": doses_acum,
                "pessoas_acumuladas": len(pessoas_acum),
            }
        )
    return out


# --- API path -----------------------------------------------------------------


def process_api(*, max_pages: int | None = None) -> dict:
    """
    Numerador via API DEMAS PNI 2026.
    Filtros locais: codigo_vacina=107 (VPC20), idade≥5, data≥2026-06-01,
    e (estratégia RIE=2 OU CNES na lista CRIE).
    Sem CID na API → sem breakdown por condição.
    """
    if max_pages is None:
        env = os.environ.get("RADAR_API_MAX_PAGES", "").strip()
        max_pages = int(env) if env.isdigit() else None

    codes = vacina_codes_vpc20()
    rie = estrategia_rie_codes()
    crie = cnes_crie_set()
    inicio = data_inicio()

    pessoas_uf: dict[str, set[str]] = {}
    pessoas_mun: dict[str, set[str]] = {}
    doses_mun: dict[str, int] = {}
    nome_mun: dict[str, str] = {}
    pessoas_all: set[str] = set()
    pessoas_cond_uf: dict[tuple[int, str], set[str]] = {}
    grupos_nao_mapeados: dict[str, int] = {}
    doses_por_mes: dict[str, int] = {}
    pessoas_por_mes: dict[str, set[str]] = {}
    doses = 0
    scanned = 0
    vpc20_raw = 0
    vpc20_pos_filtro_data_idade = 0
    rie_hits = 0
    crie_hits = 0
    grupo_map_hits = 0
    pages = 0
    vac_codes_seen: dict[str, int] = {}

    grupo_map_raw = load_json("grupo_atendimento_condicao_map.json")
    grupo_to_cond: dict[str, int] = {
        str(m["codigo_grupo_atendimento"]).zfill(6): int(m["condicao_id"])
        for m in (grupo_map_raw.get("mapeamentos") or [])
    }

    print(
        f"API PNI 2026 — VPC20 códigos={sorted(codes)} | "
        f"data>={inicio.isoformat()} | estrategia RIE={sorted(rie)} | "
        f"max_pages={max_pages or '∞'} | cache={API_CACHE}"
    )

    for offset, rows in iter_pni_2026(
        max_pages=max_pages,
        cache_dir=API_CACHE,
    ):
        pages += 1
        scanned += len(rows)
        for r in rows:
            code = str(r.get("codigo_vacina") or "")
            vac_codes_seen[code] = vac_codes_seen.get(code, 0) + 1
            if code not in codes:
                continue
            vpc20_raw += 1

            dt = parse_api_date(r.get("data_vacina"))
            if dt is None or dt < inicio:
                continue
            try:
                idade = int(str(r.get("numero_idade_paciente") or "-1"))
            except ValueError:
                continue
            if idade < 5:
                continue
            vpc20_pos_filtro_data_idade += 1

            cnes = re.sub(r"\D", "", str(r.get("codigo_cnes_estabelecimento") or "")).zfill(7)
            estrat = str(r.get("codigo_estrategia_vacinacao") or "")
            is_rie = estrat in rie
            is_crie = cnes in crie
            # Adultos VPC20 ≥5a: aceita RIE (2/8) OU CNES CRIE.
            # Se nenhum bater, ainda conta com flag (oportunidade ampla).
            if not (is_rie or is_crie):
                # fallback: dose única (9) em ≥5a também é tipicamente RIE adulta
                if str(r.get("codigo_dose_vacina") or "") != "9":
                    continue
            if is_rie:
                rie_hits += 1
            if is_crie:
                crie_hits += 1

            pid = str(r.get("codigo_paciente") or "").strip()
            if not pid:
                continue
            uf = (r.get("sigla_uf_paciente") or "").strip().upper() or "ND"
            if len(uf) != 2:
                uf = uf_from_ibge_mun(str(r.get("codigo_municipio_paciente") or "")) or "ND"

            doses += 1
            pessoas_all.add(pid)
            if dt:
                mes = dt.isoformat()[:7]
                doses_por_mes[mes] = doses_por_mes.get(mes, 0) + 1
                pessoas_por_mes.setdefault(mes, set()).add(pid)
            pessoas_uf.setdefault(uf, set()).add(pid)
            mun = normalize_mun_ibge(r.get("codigo_municipio_paciente")) or normalize_mun_ibge(
                r.get("codigo_municipio_estabelecimento")
            )
            if mun:
                pessoas_mun.setdefault(mun, set()).add(pid)
                doses_mun[mun] = doses_mun.get(mun, 0) + 1
                mun_nome = (
                    str(r.get("nome_municipio_paciente") or "").strip()
                    or str(r.get("nome_municipio_estabelecimento") or "").strip()
                )
                if mun_nome and mun not in nome_mun:
                    nome_mun[mun] = mun_nome

            g = re.sub(r"\D", "", str(r.get("codigo_vacina_grupo_atendimento") or "")).zfill(6)
            if g in grupo_to_cond:
                cid = grupo_to_cond[g]
                pessoas_cond_uf.setdefault((cid, uf), set()).add(pid)
                grupo_map_hits += 1
            elif g and g not in ("000000", "999999"):
                grupos_nao_mapeados[g] = grupos_nao_mapeados.get(g, 0) + 1

        print(
            f"  offset={offset} página={pages} scanned={scanned} "
            f"vpc20={vpc20_raw} ≥5a+data={vpc20_pos_filtro_data_idade} "
            f"doses={doses} pessoas={len(pessoas_all)}"
        )

    linha_tempo_api: list[dict] = []
    pessoas_acum: set[str] = set()
    doses_acum = 0
    for mes in sorted(doses_por_mes):
        doses_mes = doses_por_mes[mes]
        doses_acum += doses_mes
        pessoas_mes = pessoas_por_mes.get(mes, set())
        pessoas_acum |= pessoas_mes
        linha_tempo_api.append(
            {
                "ano_mes": mes,
                "doses_mes": doses_mes,
                "pessoas_mes": len(pessoas_mes),
                "doses_acumuladas": doses_acum,
                "pessoas_acumuladas": len(pessoas_acum),
            }
        )

    payload = {
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
        "fonte": "api:vacinacao/doses-aplicadas-pni-2026",
        "fonte_tipo": "api",
        "fixture": False,
        "vacina_nomes_descobertos": ["VPC20 (codigo_vacina=107)"],
        "codigo_vacina_filtro": sorted(codes),
        "data_inicio": inicio.isoformat(),
        "filtro_crie_aplicado": True,
        "filtro_estrategia_rie": sorted(rie),
        "filtro_detalhe": {
            "registros_lidos": scanned,
            "paginas": pages,
            "vpc20_qualquer": vpc20_raw,
            "vpc20_ge5_apos_inicio": vpc20_pos_filtro_data_idade,
            "doses_rie_crie_ou_du": doses,
            "hits_estrategia_rie": rie_hits,
            "hits_cnes_crie": crie_hits,
            "municipios_com_vacinado": len(pessoas_mun),
            "max_pages": max_pages,
            "grupo_atendimento_mapeados": grupo_map_hits,
            "grupos_nao_mapeados_top": dict(
                sorted(grupos_nao_mapeados.items(), key=lambda x: -x[1])[:15]
            ),
        },
        "total_doses": doses,
        "total_pessoas": len(pessoas_all),
        "taxa_cid_preenchido": 0.0,
        "sem_cid_na_fonte": True,
        "proxy_grupo_atendimento": True,
        "pessoas_por_uf": {uf: len(pids) for uf, pids in sorted(pessoas_uf.items())},
        "pessoas_por_municipio": {
            mun: len(pids) for mun, pids in sorted(pessoas_mun.items())
        },
        "por_municipio": [
            {
                "municipio_ibge": mun,
                "uf": uf_from_ibge_mun(mun) or "ND",
                "nome": nome_mun.get(mun),
                "pessoas_vacinadas": len(pids),
                "doses": doses_mun.get(mun, len(pids)),
            }
            for mun, pids in sorted(pessoas_mun.items(), key=lambda x: -len(x[1]))
        ],
        "linhas": [
            {
                "condicao_id": cid,
                "uf": uf,
                "pessoas_vacinadas": len(pids),
                "fonte_proxy": "grupo_atendimento",
            }
            for (cid, uf), pids in sorted(pessoas_cond_uf.items(), key=lambda x: (-len(x[1]), x[0]))
        ],
        "linha_tempo": linha_tempo_api,
        "periodo": {
            "inicio": inicio.isoformat(),
            "fim": linha_tempo_api[-1]["ano_mes"] + "-31" if linha_tempo_api else None,
            "meses": len(linha_tempo_api),
        },
        "cids_nao_mapeados": {},
        "grupos_nao_mapeados": dict(sorted(grupos_nao_mapeados.items(), key=lambda x: -x[1])[:50]),
        "sanity_referencia_doses": None,
        "sanity_divergencia_pct": None,
        "vacinas_vistas_amostra": dict(
            sorted(vac_codes_seen.items(), key=lambda x: -x[1])[:30]
        ),
        "nota": (
            "Numerador via API DEMAS. Sem CID — breakdown por condição via proxy "
            "codigo_vacina_grupo_atendimento (parcial). "
            f"Filtro: codigo_vacina=107 + idade≥5 + data≥{inicio.isoformat()} + "
            "(estratégia RIE 2|8 OU CNES CRIE OU dose única 9). "
            "Município: codigo_municipio_paciente (IBGE 6 dígitos na API; malha 7). "
            "RADAR_API_MAX_PAGES / RADAR_DATA_INICIO para overrides. "
            "CSV CKAN (S3 PNI/csv/*.zip) desbloqueia CID definitivo."
        ),
    }
    return save_numerador(payload)


# --- CSV path -----------------------------------------------------------------


def process_csv(csv_path: Path | list[Path]) -> dict:
    if duckdb is None:
        raise RuntimeError("duckdb não instalado. pip install -r etl/requirements.txt")

    paths = [csv_path] if isinstance(csv_path, Path) else list(csv_path)
    if not paths:
        raise FileNotFoundError("CSV não encontrado em data/raw/")
    paths = [p for p in paths if p.exists() and p.stat().st_size > 0]
    if not paths:
        raise FileNotFoundError("CSV vazio/inexistente em data/raw/")

    mapping = load_json("cid_condicao_map.json")
    crie = cnes_crie_set()
    con = duckdb.connect()

    names = ", ".join(p.name for p in paths)
    print(f"Discovery vacina_nome em {names}…")
    nomes: list[str] = []
    for p in paths:
        nomes.extend(discover_vacina_nomes(con, p))
    nomes = sorted(set(nomes))
    print(f"  encontrados: {nomes[:20]}")

    # Probe columns from first file (CKAN PNI schema is stable across months)
    probe = paths[0]
    cols_probe = con.execute(
        f"""
        SELECT * FROM read_csv_auto('{probe.as_posix()}', delim=';', header=true, ignore_errors=true, sample_size=100)
        LIMIT 0
        """
    ).description
    colnames = [c[0] for c in cols_probe]

    def pick(*candidates: str) -> str | None:
        lower = {c.lower(): c for c in colnames}
        for cand in candidates:
            if cand.lower() in lower:
                return lower[cand.lower()]
        return None

    col_vacina = pick("vacina_nome", "nm_vacina", "vacina", "descricao_vacina", "sg_imunobiologico")
    col_vac_code = pick("codigo_vacina", "co_vacina")
    col_cid = pick("motivo_indicacao_CID", "motivo_indicacao_cid", "cid", "co_cid")
    col_cnes = pick(
        "estabelecimento_valor",
        "co_cnes",
        "cnes",
        "estabelecimento_cnes",
        "codigo_cnes_estabelecimento",
        "co_cnes_estabelecimento",
    )
    col_nasc = pick("paciente_dataNascimento", "paciente_datanascimento", "dt_nascimento")
    col_idade = pick("numero_idade_paciente", "idade_paciente", "nu_idade_paciente")
    col_id = pick(
        "paciente_id",
        "id_paciente",
        "paciente_cpf",
        "codigo_paciente",
        "co_paciente",
        "co_documento",
    )
    col_mun = pick(
        "paciente_endereco_coIbgeMunicipio",
        "paciente_endereco_coibgemunicipio",
        "co_municipio_paciente",
        "codigo_municipio_paciente",
        "co_ibge",
    )
    col_uf = pick("sigla_uf_paciente", "paciente_uf", "uf_paciente", "sg_uf_paciente")
    col_grupo = pick("codigo_vacina_grupo_atendimento", "co_vacina_grupo_atendimento")
    col_data = pick(
        "vacina_dataAplicacao",
        "vacina_dataaplicacao",
        "dt_vacina",
        "data_aplicacao",
        "data_vacina",
    )

    if not col_data or not col_id:
        raise RuntimeError(f"Colunas obrigatórias ausentes. Disponíveis: {colnames}")

    vac_parts = []
    if col_vacina:
        vac_parts.append(
            " OR ".join([f"\"{col_vacina}\" ILIKE '{p}'" for p in VACINA_PATTERNS])
        )
    if col_vac_code:
        codes = ", ".join(f"'{c}'" for c in vacina_codes_vpc20())
        vac_parts.append(f"CAST(\"{col_vac_code}\" AS VARCHAR) IN ({codes})")
    if not vac_parts:
        raise RuntimeError("CSV sem coluna de vacina/nome ou codigo_vacina")

    idade_sql = "TRUE"
    if col_nasc:
        idade_sql = (
            f"date_diff('year', TRY_CAST(\"{col_nasc}\" AS DATE), "
            f"TRY_CAST(\"{col_data}\" AS DATE)) >= 5"
        )
    elif col_idade:
        idade_sql = f"TRY_CAST(\"{col_idade}\" AS INTEGER) >= 5"

    cid_expr = f"\"{col_cid}\"" if col_cid else "NULL"
    cnes_expr = f"CAST(\"{col_cnes}\" AS VARCHAR)" if col_cnes else "NULL"
    mun_expr = f"CAST(\"{col_mun}\" AS VARCHAR)" if col_mun else "NULL"
    uf_expr = f"CAST(\"{col_uf}\" AS VARCHAR)" if col_uf else "NULL"
    grupo_expr = f"CAST(\"{col_grupo}\" AS VARCHAR)" if col_grupo else "NULL"

    grupo_map_raw = load_json("grupo_atendimento_condicao_map.json")
    grupo_to_cond: dict[str, int] = {
        str(m["codigo_grupo_atendimento"]).zfill(6): int(m["condicao_id"])
        for m in (grupo_map_raw.get("mapeamentos") or [])
    }

    file_list = "[" + ", ".join(f"'{p.as_posix()}'" for p in paths) + "]"
    sql = f"""
    SELECT
      CAST("{col_id}" AS VARCHAR) AS paciente_id,
      {cid_expr} AS cid,
      {cnes_expr} AS cnes,
      {mun_expr} AS mun_ibge,
      {uf_expr} AS uf_sigla,
      {grupo_expr} AS grupo_atendimento,
      "{col_data}" AS data_aplicacao
    FROM read_csv_auto({file_list}, delim=';', header=true, ignore_errors=true, union_by_name=true)
    WHERE ({' OR '.join(f'({p})' for p in vac_parts)})
      AND TRY_CAST("{col_data}" AS DATE) >= DATE '{data_inicio().isoformat()}'
      AND ({idade_sql})
    """
    print(f"Executando filtro DuckDB em {len(paths)} arquivo(s)…")
    df = con.execute(sql).fetchdf()
    print(f"  linhas após filtro vacina/idade/data: {len(df)}")

    df["cnes_norm"] = (
        df["cnes"].astype(str).str.replace(r"\D", "", regex=True).str.zfill(7)
        if col_cnes
        else ""
    )
    if col_cnes:
        df_crie = df[df["cnes_norm"].isin(crie)].copy()
        used_crie = True
        min_crie = max(100, int(len(df) * 0.05))
        if len(df) > 0 and len(df_crie) < min_crie:
            print(
                f"  AVISO: só {len(df_crie)} de {len(df)} doses em CNES seed "
                f"(mín. {min_crie}) — mantendo todos VPC20 filtrados."
            )
            df_crie = df.copy()
            used_crie = False
    else:
        df_crie = df.copy()
        used_crie = False

    # Dedup paciente+data se vários meses CKAN forem mesclados
    if len(paths) > 1 and "data_aplicacao" in df_crie.columns:
        before = len(df_crie)
        df_crie = df_crie.drop_duplicates(subset=["paciente_id", "data_aplicacao"])
        if len(df_crie) < before:
            print(f"  dedup paciente+data: {before} → {len(df_crie)}")

    linha_tempo = build_linha_tempo(df_crie, col_data="data_aplicacao")

    total_doses = len(df_crie)
    total_pessoas = df_crie["paciente_id"].nunique()
    if col_cid:
        com_cid = df_crie["cid"].notna() & (df_crie["cid"].astype(str).str.strip() != "")
        taxa_cid = float(com_cid.mean()) if len(df_crie) else 0.0
    else:
        taxa_cid = 0.0

    counts: dict[tuple[int, str], set] = {}
    unmapped: dict[str, int] = {}
    grupos_nao_mapeados: dict[str, int] = {}
    grupo_map_hits = 0
    por_uf: dict[str, set] = {}
    pessoas_mun: dict[str, set] = {}
    doses_mun: dict[str, int] = {}
    nome_mun: dict[str, str] = {}

    for _, row in df_crie.iterrows():
        uf = (str(row.get("uf_sigla") or "").strip().upper() if row.get("uf_sigla") else None)
        if not uf or uf in ("NONE", "NAN", ""):
            uf = uf_from_ibge_mun(row.get("mun_ibge")) or "ND"
        por_uf.setdefault(uf, set()).add(str(row["paciente_id"]))
        mun = normalize_mun_ibge(row.get("mun_ibge"))
        if mun:
            pessoas_mun.setdefault(mun, set()).add(str(row["paciente_id"]))
            doses_mun[mun] = doses_mun.get(mun, 0) + 1
        cid = row.get("cid")
        mapped = False
        if col_cid and cid is not None and str(cid).strip() not in ("", "nan", "None"):
            m = map_cid_to_condicao(str(cid), mapping)
            if not m:
                key = normalize_cid(str(cid)) or str(cid)
                unmapped[key] = unmapped.get(key, 0) + 1
            elif m["condicao_id"] != 21:
                counts.setdefault((m["condicao_id"], uf), set()).add(str(row["paciente_id"]))
                mapped = True
        if not mapped and col_grupo:
            g = re.sub(r"\D", "", str(row.get("grupo_atendimento") or "")).zfill(6)
            if g in grupo_to_cond:
                counts.setdefault((grupo_to_cond[g], uf), set()).add(str(row["paciente_id"]))
                grupo_map_hits += 1
            elif g and g not in ("000000", "999999"):
                grupos_nao_mapeados[g] = grupos_nao_mapeados.get(g, 0) + 1

    linhas = [
        {
            "condicao_id": cid,
            "uf": uf,
            "pessoas_vacinadas": len(pids),
            **({"fonte_proxy": "grupo_atendimento"} if not col_cid else {}),
        }
        for (cid, uf), pids in sorted(counts.items())
    ]

    return save_numerador(
        {
            "atualizado_em": datetime.now(timezone.utc).isoformat(),
            "fonte": " + ".join(p.name for p in paths),
            "fonte_tipo": "csv",
            "fonte_arquivos": [p.name for p in paths],
            "fixture": False,
            "vacina_nomes_descobertos": nomes,
            "filtro_crie_aplicado": used_crie,
            "total_doses": int(total_doses),
            "total_pessoas": int(total_pessoas),
            "taxa_cid_preenchido": round(taxa_cid, 4),
            "sem_cid_na_fonte": not bool(col_cid),
            "proxy_grupo_atendimento": not bool(col_cid) and bool(col_grupo),
            "grupo_atendimento_mapeados": grupo_map_hits,
            "grupos_nao_mapeados": dict(
                sorted(grupos_nao_mapeados.items(), key=lambda x: -x[1])[:50]
            ),
            "pessoas_por_uf": {k: len(v) for k, v in sorted(por_uf.items())},
            "pessoas_por_municipio": {k: len(v) for k, v in sorted(pessoas_mun.items())},
            "por_municipio": [
                {
                    "municipio_ibge": mun,
                    "uf": uf_from_ibge_mun(mun) or "ND",
                    "nome": nome_mun.get(mun),
                    "pessoas_vacinadas": len(pids),
                    "doses": doses_mun.get(mun, len(pids)),
                }
                for mun, pids in sorted(pessoas_mun.items(), key=lambda x: -len(x[1]))
            ],
            "linhas": linhas,
            "linha_tempo": linha_tempo,
            "periodo": {
                "inicio": data_inicio().isoformat(),
                "fim": linha_tempo[-1]["ano_mes"] + "-31" if linha_tempo else None,
                "meses": len(linha_tempo),
                "arquivos": [p.name for p in paths],
            },
            "cids_nao_mapeados": dict(sorted(unmapped.items(), key=lambda x: -x[1])[:50]),
            "sanity_referencia_doses": None,
            "sanity_divergencia_pct": None,
            "nota": (
                f"CSV CKAN PNI 2026 ({len(paths)} mês(es)). "
                + (
                    "Sem motivo_indicacao_CID — breakdown via co_vacina_grupo_atendimento (proxy)."
                    if not col_cid
                    else "Com CID na fonte."
                )
            ),
        }
    )


def write_fixture() -> dict:
    demo = [
        {"condicao_id": 1, "uf": "SP", "pessoas_vacinadas": 42},
        {"condicao_id": 1, "uf": "RJ", "pessoas_vacinadas": 18},
        {"condicao_id": 2, "uf": "SP", "pessoas_vacinadas": 65},
        {"condicao_id": 2, "uf": "MG", "pessoas_vacinadas": 22},
        {"condicao_id": 19, "uf": "SP", "pessoas_vacinadas": 120},
        {"condicao_id": 19, "uf": "RJ", "pessoas_vacinadas": 55},
        {"condicao_id": 19, "uf": "MG", "pessoas_vacinadas": 40},
        {"condicao_id": 15, "uf": "SP", "pessoas_vacinadas": 33},
        {"condicao_id": 10, "uf": "SP", "pessoas_vacinadas": 28},
        {"condicao_id": 13, "uf": "RS", "pessoas_vacinadas": 15},
        {"condicao_id": 5, "uf": "SP", "pessoas_vacinadas": 3},
        {"condicao_id": 7, "uf": "SP", "pessoas_vacinadas": 5},
        {"condicao_id": 3, "uf": "SP", "pessoas_vacinadas": 8},
        {"condicao_id": 4, "uf": "SP", "pessoas_vacinadas": 4},
        {"condicao_id": 8, "uf": "SP", "pessoas_vacinadas": 6},
        {"condicao_id": 14, "uf": "PR", "pessoas_vacinadas": 12},
        {"condicao_id": 16, "uf": "BA", "pessoas_vacinadas": 9},
        {"condicao_id": 17, "uf": "PE", "pessoas_vacinadas": 7},
        {"condicao_id": 18, "uf": "SP", "pessoas_vacinadas": 11},
        {"condicao_id": 11, "uf": "SP", "pessoas_vacinadas": 2},
        {"condicao_id": 20, "uf": "RJ", "pessoas_vacinadas": 1},
        {"condicao_id": 6, "uf": "SP", "pessoas_vacinadas": 4},
        {"condicao_id": 9, "uf": "MG", "pessoas_vacinadas": 1},
        {"condicao_id": 12, "uf": "SP", "pessoas_vacinadas": 19},
    ]
    total_pessoas = sum(r["pessoas_vacinadas"] for r in demo)
    por_uf: dict[str, int] = {}
    for r in demo:
        por_uf[r["uf"]] = por_uf.get(r["uf"], 0) + r["pessoas_vacinadas"]
    return save_numerador(
        {
            "atualizado_em": datetime.now(timezone.utc).isoformat(),
            "fonte": "fixture_demo",
            "fonte_tipo": "fixture",
            "fixture": True,
            "vacina_nomes_descobertos": ["Pneumocócica 20-valente (VPC20)", "Prevenar 20"],
            "filtro_crie_aplicado": True,
            "total_doses": total_pessoas,
            "total_pessoas": total_pessoas,
            "taxa_cid_preenchido": 0.87,
            "pessoas_por_uf": por_uf,
            "linhas": demo,
            "cids_nao_mapeados": {"X99": 3, "Z00": 1},
            "sanity_referencia_doses": total_pessoas,
            "sanity_divergencia_pct": 0.0,
            "nota": "Fixture. Prefira API (padrão) ou CSV em data/raw/.",
        }
    )


def run(
    *,
    source: str | None = None,
    use_fixture_if_missing: bool = True,
    max_pages: int | None = None,
) -> dict:
    """
    Ordem padrão: CSV se existir → senão API → senão fixture.
    source: 'csv' | 'api' | 'fixture' para forçar.
    """
    src = (source or os.environ.get("RADAR_NUMERADOR_SOURCE") or "").strip().lower()

    if src == "fixture":
        return write_fixture()
    if src == "api":
        return process_api(max_pages=max_pages)
    if src == "csv":
        csv_paths = find_csv_paths()
        if not csv_paths:
            raise FileNotFoundError("CSV não encontrado em data/raw/")
        return process_csv(csv_paths)

    csv_paths = find_csv_paths()
    if csv_paths:
        print(f"Usando CSV: {', '.join(p.name for p in csv_paths)}")
        return process_csv(csv_paths)

    try:
        print("Sem CSV — tentando API OpenDataSUS PNI 2026…")
        return process_api(max_pages=max_pages)
    except Exception as exc:  # noqa: BLE001
        print(f"API falhou ({exc})")
        if use_fixture_if_missing:
            print("Gerando fixture demonstrativa.")
            return write_fixture()
        raise


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Numerador VPC20 CRIE")
    p.add_argument("--source", choices=["api", "csv", "fixture"], default=None)
    p.add_argument("--max-pages", type=int, default=None, help="Limite de páginas da API (1000 regs)")
    args = p.parse_args()
    run(source=args.source, max_pages=args.max_pages)
