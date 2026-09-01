# OpenDataSUS API — catálogo consolidado

Fonte Swagger: https://apidadosabertos.saude.gov.br/static/swagger.json  
UI: https://apidadosabertos.saude.gov.br/v1/  
Versão: **DEMAS - API de Dados Abertos v1.8.32**  
Base: `https://apidadosabertos.saude.gov.br`

Arquivos gerados:
- [`data/reference/opendatasus_swagger.json`](data/reference/opendatasus_swagger.json) — spec completa
- [`data/reference/opendatasus_api_catalog.json`](data/reference/opendatasus_api_catalog.json) — 87 endpoints indexados
- [`data/reference/opendatasus_pni_2026_fields.json`](data/reference/opendatasus_pni_2026_fields.json) — campos do PNI 2026

## Resumo

| Métrica | Valor |
|--------|------:|
| Endpoints | 87 |
| Tags / temas | 17 |
| Vacinação | 9 |
| Página máx. PNI 2026 | 1000 |
| Filtros server-side PNI 2026 | só `limit` / `offset` (outros params ignorados) |

## Tags (todos os temas)

| Tag | Nº |
|-----|---:|
| Vacinação | 9 |
| SISAGUA | 14 |
| Saúde Indígena | 14 |
| Atenção Primária | 11 |
| Vigilância e Meio Ambiente | 11 |
| Ciência & Tecnologia | 6 |
| Agravo Arboviroses | 5 |
| CNES | 4 |
| Assistência à Saúde | 3 |
| Economia da Saúde | 2 |
| Ouvidoria | 2 |
| BNAFAR | 1 |
| Educação em Saúde | 1 |
| Macrorregião e Região de Saúde | 1 |
| Outros Temas | 1 |
| Prevenção e Promoção | 1 |
| SISVAN | 1 |

## Vacinação — endpoints

| Método | Path | Params documentados |
|--------|------|---------------------|
| GET | `/vacinacao/doses-aplicadas-pni-2020` | `uf_estabelecimento`, `uf_paciente`, `limit`, `offset` |
| GET | `/vacinacao/doses-aplicadas-pni-2021` | `uf_estabelecimento`, `limit`, `offset` |
| GET | `/vacinacao/doses-aplicadas-pni-2022` | `uf_paciente`, `limit`, `offset` |
| GET | `/vacinacao/doses-aplicadas-pni-2023` | `uf_estabelecimento`, `limit`, `offset` |
| GET | `/vacinacao/doses-aplicadas-pni-2024` | `limit`, `offset` |
| GET | `/vacinacao/doses-aplicadas-pni-2025` | `limit`, `offset` |
| GET | `/vacinacao/doses-aplicadas-pni-2026` | `limit`, `offset` |
| GET | `/vacinacao/esavi` | `limit`, `offset` |
| GET | `/vacinacao/sistema-de-informacao-de-insumos-estrategicos` | `limit`, `offset` |

### Exemplo PNI 2026

```
GET https://apidadosabertos.saude.gov.br/vacinacao/doses-aplicadas-pni-2026?limit=1000&offset=0
```

Resposta:

```json
{ "doses_aplicadas_pni": [ { "...49 campos..." } ] }
```

## Campos úteis para o Radar Vacinal VPC20/CRIE

| Campo API | Uso |
|-----------|-----|
| `codigo_vacina` | Identificar VPC20 (precisa dicionário de códigos — **não há nome da vacina**) |
| `descricao_vacina_fabricante` | Proxy (ex.: Pfizer) — insuficiente sozinho |
| `codigo_cnes_estabelecimento` | Cruzar com lista CRIE |
| `codigo_tipo_estabelecimento` / `descricao_tipo_estabelecimento` | Tipo CNES (código `15` na API = **UNIDADE MISTA**, não CRIE) |
| `codigo_paciente` | COUNT DISTINCT |
| `numero_idade_paciente` | Filtro ≥5 anos (sem data de nascimento) |
| `data_vacina` | Recorte ≥ jun/2026 |
| `sigla_uf_paciente` / `codigo_municipio_paciente` | Agregação por UF |
| `codigo_dose_vacina` | Tipo de dose |
| `codigo_estrategia_vacinacao` | Estratégia (RIE?) — a validar |

## Lacunas críticas vs NT 52 / guia técnico

1. **Sem `motivo_indicacao_CID`** — impossível classificar as 21 condições via esta API.
2. **Sem `vacina_nome` / descrição do imunobiológico** — só `codigo_vacina`.
3. **Sem filtros** em 2026 (`codigo_vacina`, UF, tipo estabelecimento são ignorados) → precisa varrer com paginação de 1000.
4. **Código tipo `15` ≠ CRIE** nesta API (`UNIDADE MISTA`). CRIE exige lista CNES estática ou outra fonte.
5. Volume nacional exige muitas páginas; CSV mensal do portal continua necessário para carga completa + campos extras.

## Implicação para o pipeline

- **API integrada** em `etl/numerador.py` (`--source api`):
  - `codigo_vacina=107` (VPC20)
  - idade ≥ 5, data ≥ `2026-05-01` (override `RADAR_DATA_INICIO`)
  - estratégia **2 ou 8** (RIE) **ou** CNES CRIE **ou** dose única `9`
  - paginação 1000 + cache em `data/raw/api_pni_2026/`
- **Sem CID** → totais nacional/UF apenas; breakdown por condição exige CSV.
- Amostra 40 páginas (40k regs): 241 VPC20 → **100 pessoas** ≥5a elegíveis ao filtro.

```bash
.\.venv\Scripts\python etl\numerador.py --source api
.\.venv\Scripts\python etl\numerador.py --source api --max-pages 100
.\.venv\Scripts\python etl\build_mart.py
```

