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

A NT 24/2026 determina o uso da Estratégia Vacinação Escolar para ações em escola com pessoas <=14 anos.

A Nota Informativa nº 2/2025-CIMVAC/CGESCO/DESCO/SAPS/MS orienta explicitamente o registro como:

- estratégia `14`;
- descrição: `Vacinação escolar`.

A NT nº 56/2026 dá continuidade à estratégia em 2026.

### Divergência terminológica

O ValueSet publicado `BREstrategiaVacinacao` versão 1.1.0, ativo em 22/08/2026, ainda lista 13 conceitos e não apresenta o código 14.

No PREVNAR:
- o código 14 é aceito **somente** porque há orientação oficial específica de registro;
- a divergência com o ValueSet permanece registrada;
- uma atualização futura do servidor terminológico deve ser monitorada.

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
