# Radar Vacinal · VPC20 CRIE

Painel de **oportunidade** de vacinação VPC20 nos CRIEs (NT 52/2026): elegíveis estimados, pessoas vacinadas e gap absoluto por condição e UF.

## Estrutura

- `etl/` — Python + DuckDB (numerador RNDS, denominadores, mart)
- `web/` — Next.js (dashboard)
- `data/reference/` — CID map, taxas, estimativas, CNES CRIE
- `data/raw/` — CSVs OpenDataSUS PNI (gitignored)
- `data/manual/situacao1/` — CSVs de cadastro (Situação 1)
- `data/mart/` — agregados JSON consumidos pelo painel

## Setup

```bash
python -m venv .venv
.venv\Scripts\pip install -r etl\requirements.txt
.venv\Scripts\python etl\build_mart.py

cd web
npm install
npm run dev
```

Abra http://localhost:3000

## Numerador (OpenDataSUS)

Ordem automática: **CSV** em `data/raw/` → senão **API** PNI 2026 → senão fixture.

```bash
# API (padrão sem CSV) — código vacina 107 = VPC20 (NT 64/2026)
.\.venv\Scripts\python etl\numerador.py --source api
.\.venv\Scripts\python etl\numerador.py --source api --max-pages 50   # amostra

# CSV local
# coloque o arquivo em data/raw/ e:
.\.venv\Scripts\python etl\numerador.py --source csv

# Mart completo
.\.venv\Scripts\python etl\build_mart.py
```

Env: `RADAR_API_MAX_PAGES`, `RADAR_NUMERADOR_SOURCE=api|csv|fixture`.

Catálogo da API: `data/reference/OPENDATASUS_API.md`.

A API **não traz CID** — o breakdown por condição só existe via CSV com `motivo_indicacao_CID`.

## Dashboard nacional — novos indicadores

```bash
.\.venv\Scripts\python etl\extract_nacional.py
.\.venv\Scripts\python etl\build_nacional.py
```

Abas: `/serie` · `/monitoramento` · `/estoque` · `/custo`  
Catálogo: `data/reference/indicadores_nacionais.json`  
Plano de extração: `data/reference/EXTRACAO_NACIONAL.md`
