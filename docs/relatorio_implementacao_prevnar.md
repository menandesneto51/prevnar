# Radar Vacinal VPC20 · Relatório de implementação

Gerado em: 2026-09-01 15:49 UTC

## Documento baseline (início do projeto)

- Plano de extração: `data/reference/plano_extracao_nacional.json`
- Catálogo de indicadores: `data/reference/indicadores_nacionais.json`
- 13 fontes planejadas · 20 indicadores · 6 abas no plano inicial

## KPIs atuais (mart nacional)

| KPI | Valor |
|-----|-------|
| Elegíveis | 37.853.021 |
| Vacinados VPC20 | 46.726 |
| Gap | 37.806.295 |
| Custo gap (BRL) | 7015714163.15 |
| Fonte numerador | pni_vpc20_mai_2026.csv |

## Indicadores (baseline → status atual)

| ID | Nome | Família | Status | Valor |
|----|------|---------|--------|-------|
| elegiveis | Elegíveis estimados | oportunidade | **Implementado** | 37853021 |
| pessoas_vacinadas_municipio | Pessoas vacinadas VPC20 por município | oportunidade | **Implementado** | 0 |
| pessoas_vacinadas_vpc20 | Pessoas vacinadas VPC20 (RIE/CRIE) | oportunidade | **Implementado** | 46726 |
| gap_absoluto | Gap absoluto | oportunidade | **Implementado** | 37806295 |
| cobertura_sit1 | Cobertura % Situação 1 | oportunidade | **Parcial** | 5 itens |
| gap_regiao_saude | Gap por região de saúde | oportunidade | **Implementado** | 37853010 |
| share_transicao_pneumo | Share VPC10/VPC13/VPP23/VPC20 | transicao | **Implementado** | 56 |
| sies_distribuida_aplicada | Distribuídas ÷ aplicadas (VPC20) | oferta | **Parcial** | 7.27 |
| doses_por_crie | Doses VPC20 por CRIE ativo | oferta | **Implementado** | 13.4 |
| pct_fora_crie | % doses VPC20 ≥5a fora de CNES CRIE | oferta | **Implementado** | 100.0 |
| taxa_cid_preenchido | % CID de indicação preenchido | qualidade | **Implementado** | 0.0 |
| atraso_rnds | Atraso registro RNDS (dias) | qualidade | **Implementado** | 2.0 |
| esavi_por_100k | ESAVI por 100k doses VPC20 | qualidade | **Parcial** | 10.66 |
| sinan_meningite_100k | Meningite (SINAN) por 100 mil | desfecho | **Implementado** | 0.08 |
| sih_pneumo_100k | Internações pneumocócicas (SIH) por 100 mil | desfecho | **Implementado** | 0.26 |
| sim_pneumo_100k | Óbitos pneumocócicos (SIM) por 100 mil | desfecho | **Implementado** | 0.01 |
| srag_casos_100k | SRAG (amostra OpenDataSUS) por 100 mil | desfecho | **Implementado** | 7.06 |
| razao_doses_casos | Doses VPC20 RIE ÷ (SINAN+SIH) | desfecho | **Implementado** | 63.57 |
| custo_gap | Custo do gap | economia | **Implementado** | 7015714163.15 |
| pressao_fiscal_gap | Custo do gap / gasto SIOPS per capita | economia | **Implementado** | 0.04 |

**Resumo:** 17 ok · 3 parcial · 0 sem dado

## Páginas do painel (plano vs implementado)

- `/` — Nacional — KPIs oportunidade
- `/indicadores` — Catálogo 20 indicadores + status
- `/regioes` — Gap por região de saúde
- `/serie` — Transição pneumocócica VPC10/13/20
- `/monitoramento` — SINAN · SIH · SIM · SRAG
- `/estoque` — SIES distribuídas vs aplicadas
- `/custo` — Custo do gap BPS + IPCA
- `/qualidade` — Atraso RNDS · ESAVI · oferta CRIE
- `/condicoes` — Gap por condição NT52
- `/ufs` — Drill-down UF
- `/carga` — Upload cadastros Situação 1

## Pendências

- **CKAN jun/jul 2026**: Ampliar numerador além de mai/2026 (`etl/run_ckan_pipeline.py`)
- **Cadastros Situação 1 oficiais**: Substituir seeds por SICLOM/ABTO/SBN etc. (`data/manual/situacao1/`)
- **CNES CRIE definitivo**: Lista seed não bate API; % fora CRIE = 100% (`data/reference/cnes_crie.json`)
- **Mapa municipal vacinados**: por_municipio vazio no mart atual (`numerador CKAN multi-mês`)
- **SINAN/SIH/SIM FTP**: Automatizar PySUS/DATASUS (hoje seeds 27 UFs) (`etl/extract_nacional.py`)
- **SIES VPC20 na API**: API agrega pneumo 10/13; VPC20 não discrimina (`extract_sies`)
- **ESAVI completo**: API vazia; seed manual 5 registros (`data/manual/templates/esavi_template.csv`)

## Limitações / não alcançável com bases atuais

- **CID motivo_indicacao (PNI 2026)**: CSV CKAN 2026 não traz coluna CID; REST também não. Cobertura Sit.1 definitiva por condição clínica não é possível só com bases abertas atuais.
- **Cobertura Sit.1 para todas NT52**: Denominadores oficiais por condição (21 grupos) não existem em API única; requer cadastros manuais/parceiros por fonte (SICLOM, ABTO, REBRAFC…).
- **Inferência causal desfecho**: SINAN/SIH/SIM/SRAG × VPC20 são indicadores ecológicos; dashboard documenta limitação — não há desenho observacional individual.
- **Numerador 100% CRIE via PNI aberto**: Grande parte VPC20 mai/2026 é grupo 000210 (Faixa Etária / privado), fora do recorte CRIE/RIE estrito sem bases complementares.
- **SIES dose a dose VPC20**: OpenDataSUS SIES não expõe classe VPC20 de forma confiável; proxy pneumo total.

## Scripts ETL

`api_client.py`, `build_grupo_map.py`, `build_mart.py`, `build_nacional.py`, `catalog_opendatasus_api.py`, `denominadores.py`, `discover_ckan_pni.py`, `extract_ckan_pni.py`, `extract_nacional.py`, `generate_relatorio_pdf.py`, `numerador.py`, `paths.py`, `run.py`, `run_ckan_pipeline.py`, `seed_situacao1.py`, `situacao1.py`