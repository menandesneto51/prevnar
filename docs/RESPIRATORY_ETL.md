# PREVNAR — ETL respiratório PNI

## Módulo

`etl/respiratory_etl.py`

## Objetivo

Extrair e agregar registros PNI/RNDS para:
- VVSR materna;
- nirsevimabe.

O módulo usa os códigos do `immunobiologic_registry.json`. Não mantém uma segunda lista hard-coded de imunobiológicos.

## Privacidade

O identificador do paciente é utilizado somente em memória para `COUNT DISTINCT`.

Ele não é gravado em:
- marts;
- logs;
- manifests;
- frontend.

As saídas são agregadas.

## Execução

```bash
python etl/respiratory_etl.py
```

Para limitar páginas durante desenvolvimento:

```bash
python etl/respiratory_etl.py --max-pages 20
```

ou:

```bash
PREVNAR_RESP_API_MAX_PAGES=20 python etl/respiratory_etl.py
```

## Saídas

- `data/mart/mart_respiratory_vvsr_maternal.json`;
- `data/mart/mart_respiratory_nirsevimab.json`;
- `data/mart/respiratory_dashboard.json`;
- manifestos em `data/mart/_meta/`.

## VVSR

Filtro estrito:
- código 108;
- estratégia 1;
- dose 9;
- grupo 001801.

Registros com código 108 que não satisfazem o conjunto oficial são contabilizados em `invalid_mapping`, não absorvidos silenciosamente.

## Nirsevimabe

Filtro:
- códigos 115/116;
- estratégia 2 ou 8;
- dose 59 ou 60.

A saída mantém estratégia 2 e 8 separadas e calcula:
- doses SUS;
- doses privadas;
- participação privada;
- P/T1;
- P/T2;
- apresentação 115/116;
- grupos de atendimento.

## Freshness

Cada mart recebe:
- run_id;
- source_id;
- reference_period;
- retrieved_at;
- freshness.

A referência é o último mês efetivamente observado no dado, não a data da execução do ETL.

## Limitação

O ETL atual mede administração/registro.

Ele não calcula automaticamente:
- cobertura gestacional VVSR;
- oportunidade ≥28 semanas;
- cobertura em elegíveis nirsevimabe;
- efetividade contra SRAG/internação.

Esses indicadores exigem denominadores ou linkage compatíveis e passam por gates específicos.
