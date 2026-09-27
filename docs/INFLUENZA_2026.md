# PREVNAR — Influenza 2026

## Base normativa

Nota Técnica nº 24/2026-DPNI/SVSA/MS.

A regra clínica geral permanece em `draft` até a conclusão do onboarding de grupos, esquema e calendário.

Esta etapa implementa **registro e monitoramento de dados**, não decisão clínica.

## Códigos confirmados

### SUS — Influenza Trivalente

Código:
- `33`.

Rotina:
- estratégia `1`;
- doses `1`, `2`, `9`.

Especial:
- estratégia `2`;
- doses `1`, `2`, `9`;
- motivo de indicação documentado: CID-10 `Z251`;
- especialidade documentada: Enfermeiro.

### Serviço privado — Influenza Tetravalente

Código:
- `77`.

Estratégia:
- `8` — Serviço Privado.

Doses:
- `1`;
- `2`;
- `9`.

### Serviço privado — alta dosagem

Código:
- `110`.

Estratégia:
- `8`.

Dose:
- `9` — Dose Única.

## Vacinação escolar

A NT 24/2026 determina que vacinação em escola para pessoas <=14 anos seja registrada na Estratégia Vacinação Escolar.

O código dessa estratégia **não foi inferido** nesta versão.

Esses registros devem aparecer como contexto pendente/mismatch até validação oficial.

## ETL

`etl/influenza_etl.py`

## Saída

- `data/mart/influenza_2026_dashboard.json`;
- `web/public/data/influenza_2026_dashboard.json`.

## Indicadores observáveis

- registros com códigos 33/77/110;
- pessoas distintas;
- contextos confirmados;
- SUS x privado;
- apresentação;
- dose;
- estratégia;
- UF;
- série temporal;
- mismatches;
- freshness/proveniência.

## Cobertura

A NT 24/2026 informa que a cobertura é apresentada para:
- crianças;
- gestantes;
- idosos com 60 anos e mais.

Os demais grupos são tratados como doses aplicadas.

O PREVNAR não deve gerar cobertura sem:
1. grupo de atendimento corretamente identificado;
2. denominador compatível;
3. metodologia explicitamente registrada;
4. validação do indicador.

## Execução

```bash
python etl/influenza_etl.py
```

Desenvolvimento:

```bash
python etl/influenza_etl.py --max-pages 20
```
