# PREVNAR — Registration Readiness Gate

## Objetivo

Separar explicitamente duas perguntas diferentes:

1. **A regra clínica/normativa está estruturada?**
2. **O mapeamento transacional está completo o suficiente para ativar o ETL?**

Uma resposta positiva à primeira pergunta **não** implica resposta positiva à segunda.

## Fonte canônica

`data/reference/registration_mapping_registry.json`

Esse arquivo registra evidência de mapeamento por imunobiológico e por dimensão.

## Dimensões

Dimensões atualmente suportadas:

- `immunobiologic_code`;
- `strategy`;
- `dose`;
- `attendance_group`.

Cada imunobiológico define quais dimensões são obrigatórias para seu ETL.

## Estados

### confirmed

A dimensão foi confirmada por fonte oficial adequada.

### partial

Parte do mapeamento está confirmada, mas o contexto completo ainda não está consolidado.

### pending

A dimensão necessária ainda não foi extraída/confirmada.

### not_required

A dimensão não é exigida como gate mínimo para aquele ETL específico.

## Tipos de evidência

- `official_rules_entry`;
- `official_technical_note`;
- `official_calendar`;
- `official_terminology`;
- `official_coverage_rule`;
- `official_specific_guidance`.

Terminologia oficial confirma identidade/código, mas não substitui automaticamente estratégia, dose, grupo ou regra clínica.

## Regra de prontidão

```text
etl_ready = todas as required_dimensions com status = confirmed
```

Qualquer dimensão obrigatória em:
- `partial`;
- `pending`;

bloqueia `etl_ready`.

## Motor

`etl/registration_readiness.py`

Saídas:

- `data/mart/registration_readiness.json`;
- `web/public/data/registration_readiness.json`.

O motor cruza:
- registration mapping registry;
- immunobiologic registry.

Também verifica se algum imunobiológico está:

```text
monitored = true
etl_ready = false
```

Esse estado é bloqueante.

## Estado atual

### ETL ready

- VPC20;
- VVSR materna;
- nirsevimabe;
- influenza.

### Bloqueados

#### Covid-19

Confirmado:
- código 87.

Bloqueios:
- strategy;
- dose;
- attendance_group.

#### HPV4

Confirmado:
- código 67.

Bloqueios:
- strategy;
- dose;
- attendance_group.

#### MenACWY

Confirmado:
- código 74.

Parcial:
- estratégia 1;
- dose 38.

Bloqueio:
- attendance_group;
- demais combinações necessárias da Regra de Entrada.

#### Febre amarela

Confirmado:
- código 14.

Parcial:
- doses 1, 9 e 36 em regra oficial de cobertura.

Bloqueio:
- strategy;
- consolidação da Regra de Entrada por contexto.

#### Tríplice viral

Confirmado:
- código 24.

Parcial:
- estratégias 3 e 4;
- doses 1, 2, 8 e 57 em contextos documentados.

Bloqueio:
- rotina nacional e combinações de registro ainda não consolidadas.

## Release Guardian

O Release Guardian executa `check_registration_readiness`.

Release deve falhar se:

```text
monitored = true
etl_ready = false
```

Isso impede que:
- código isolado seja tratado como regra completa;
- cobertura seja calculada a partir de combinações incompletas;
- um contexto parcial seja promovido a monitoramento nacional.

## Frontend

A rota `/normas` apresenta:

- número de imunobiológicos avaliados;
- quantos estão ETL ready;
- quantos estão bloqueados;
- monitorados sem readiness;
- percentual de prontidão;
- dimensões bloqueantes.

## Pipeline

Gerado automaticamente em:

- CI;
- GitHub Pages;
- `etl/run_all.py`.

## Cursor

Toda nova implementação deve:

1. confirmar o código do imunobiológico;
2. identificar dimensões obrigatórias;
3. registrar evidência oficial por dimensão;
4. marcar `partial` ou `pending` quando incompleto;
5. não usar texto livre como substituto do readiness registry;
6. não alterar `monitored=true` antes de `etl_ready=true`;
7. criar testes;
8. passar Release Guardian.

## Princípio

**Readiness transacional não é prontidão clínica.**

O PREVNAR pode possuir uma regra clínica válida e, ao mesmo tempo, manter o ETL bloqueado por mapeamento de registro incompleto.
