# PREVNAR — Mapeamento de dados respiratórios

**Versão:** 1.0  
**Data:** 26/09/2026

## VVSR materna

Parametrização oficial:
- imunobiológico: **108**;
- estratégia: **1 — Rotina**;
- dose: **9 — Única (DU)**;
- grupo de atendimento: **001801 — Gestante**.

O modelo RNDS aceita faixa etária >=9 anos para entrada do registro, mas isso **não substitui** a regra clínica: elegibilidade é gestante a partir da 28ª semana.

### O que pode ser medido diretamente no PNI/RNDS

- doses administradas;
- pessoas vacinadas distintas;
- distribuição por UF/município/CNES;
- série temporal;
- origem/sistema quando disponível;
- fabricante/lote quando disponível.

### O que exige linkage autorizado

- oportunidade a partir da 28ª semana;
- vacinação precoce (<28 semanas);
- tempo entre elegibilidade e vacinação;
- cobertura por gestação.

Esses indicadores exigem idade gestacional/gestação corrente em fonte compatível.

## Nirsevimabe

Parametrização oficial:
- código **115** — apresentação 0,5 mL;
- código **116** — apresentação 1,0 mL;
- estratégia **2 — Especial**;
- estratégia **8 — Serviço Privado**;
- dose **59 — P/T1**;
- dose **60 — P/T2**;
- fabricante **44329 — PATHEON MANUFATURING SERVICES LLC**.

Grupos de atendimento documentados:
- 000116 Doença Cardiovascular;
- 000104 Pneumopatias Crônicas Graves;
- 000117 Imunocomprometidos;
- 000115 Doença neurológica crônica;
- 000121 Anomalias das vias aéreas;
- 000110 Síndrome de Down;
- 000120 Prematuridade.

### Regra de interpretação

- código 59 representa uma unidade/seringa;
- código 60 representa duas unidades/seringas;
- apresentação e dose devem ser interpretadas conjuntamente;
- estratégia 8 (privado) não deve ser mesclada silenciosamente à estratégia SUS 2.

## Proveniência

Os mapeamentos estruturados ficam em:
- `data/reference/immunobiologic_registry.json`;
- `data/reference/respiratory_data_plan.json`;
- `data/reference/respiratory_indicators.json`;
- `data/reference/source_registry.json`.

## Próximo passo

Implementar coletores/transformações para:
- `pni_vvsr_maternal`;
- `pni_nirsevimab`.

Cada execução deve gerar manifesto, freshness e hashes conforme `etl/provenance.py`.
