# Extração de bases — dashboard nacional

Fonte de verdade: [`plano_extracao_nacional.json`](plano_extracao_nacional.json) · indicadores: [`indicadores_nacionais.json`](indicadores_nacionais.json)

## Fluxo

```text
IBGE 6579 + SIDRA 9514 ─┐
CNES CRIE ──────────────┤
CSV CKAN / REST PNI ────┼─► DuckDB / JSON marts ─► web/public/data ─► Dashboard nacional
SIES + ESAVI ───────────┤
SINAN + SIH (+SIM/SRAG)─┤
BPS + IPCA + SIOPS ─────┘
```

## Comandos

```bash
.\.venv\Scripts\python etl\extract_nacional.py           # extrai o que for automático
.\.venv\Scripts\python etl\build_nacional.py             # monta marts do dashboard
cd web && npm run dev -- -p 3005
```

## Prioridade operacional

1. População (6579 + 9514) — leve, desbloqueia taxas  
2. CNES CRIE — corrige numerador  
3. PNI (CSV CKAN se houver CID; senão REST + proxy `grupo_atendimento`)  
4. SIES / ESAVI  
5. SINAN / SIH / SIM / SRAG (FTP ou CSV manual em `data/manual/`)  
6. Economia (BPS seed + IPCA API + SIOPS seed)

### CSV CKAN (CID definitivo)

API CKAN `package_show` costuma 404; download direto S3:

```text
https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/PNI/csv/vacinacao_mai_2026_csv.zip
```

(~3 GB/mês). Extrator streaming (filtra VPC20 `codigo_vacina=107`):

```bash
.\.venv\Scripts\python etl\extract_ckan_pni.py --mes mai --ano 2026
# gera data/raw/pni_vpc20_mai_2026.csv
$env:RADAR_NUMERADOR_SOURCE="csv"
.\.venv\Scripts\python etl\build_mart.py
.\.venv\Scripts\python etl\build_nacional.py
```

Enquanto o ZIP não for baixado, o numerador API usa **proxy** `grupo_atendimento` → condição NT52 (`data/reference/grupo_atendimento_condicao_map.json`). Cobertura Sit.1 permanece **parcial** (sem CID).

REST PNI **não** traz `motivo_indicacao_CID`.
