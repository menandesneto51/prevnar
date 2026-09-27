# PREVNAR — Governança regulatória de mudanças vacinais

## Objetivo

Manter o PREVNAR sincronizado com revisões oficiais de vacinação e regras de registro, sem transformar automaticamente um atraso técnico do projeto em conclusão jurídica.

## Base normativa principal

Portaria GM/MS nº 5.663, de 31 de outubro de 2024.

Publicação:
- 04/11/2024.

Entrada em vigor:
- 04/03/2025, após os 120 dias previstos no art. 4º.

O art. 312-A estabelece, entre outros pontos:

- sistemas de registro vacinal devem encaminhar doses aplicadas à RNDS conforme o RIA vigente;
- salas com conectividade: envio em até 24 horas;
- salas sem conectividade: envio em até 15 dias;
- após revisão das orientações técnicas de vacinação, responsáveis por sistemas que registram vacinação têm até 15 dias para adequação;
- após liberação de novo imunobiológico pela Anvisa, o DPNI/SVSA tem prazo de 15 dias para publicação das regras de novo registro, condicionado aos ajustes na RNDS.

## Aplicabilidade ao PREVNAR

O PREVNAR, no estado atual, é:

```text
analytical_monitoring
```

Ele não é o sistema transacional que registra a vacinação e transmite o RIA à RNDS.

Por isso:

- o prazo de 15 dias é usado como **benchmark interno de governança**;
- a classificação do painel não equivale a declaração de conformidade ou infração;
- se o PREVNAR passar a registrar/transmitir eventos vacinais, a análise de aplicabilidade deve ser revista.

## Política

Arquivo:

`data/reference/regulatory_compliance_policy.json`

Benchmark atual:

```text
technical_revision_adaptation_days = 15
```

## Motor

`etl/regulatory_compliance.py`

O motor cruza:

- legal register;
- normative rules;
- immunobiologic registry;
- política regulatória.

Somente atos oficiais referenciados pelas regras normativas são rastreados.

## Estados

### within_benchmark

A mudança oficial foi publicada há no máximo 15 dias.

### benchmark_exceeded_mapping_pending

O marco interno já passou e existe:
- mapeamento pendente/parcial; ou
- regra em draft.

É sinal de backlog regulatório prioritário, não declaração automática de infração.

### benchmark_exceeded_mapping_complete

O benchmark interno passou, mas o PREVNAR já possui regra/mapeamento estruturado.

Esse estado é retrospectivo e não prova que a adaptação ocorreu dentro do prazo legal.

### date_unavailable

O ato não possui data suficiente para cálculo.

## Exemplo atual

Em 26/09/2026:

### NT nº 91/2026 — covid-19

Publicada:
- 09/09/2026.

Benchmark interno:
- 24/09/2026.

Estado esperado:
- `benchmark_exceeded_mapping_pending`.

Motivo:
- código 87 confirmado;
- estratégia/dose/grupos da Regra de Entrada ainda pendentes;
- `monitored=false`.

### NT nº 98/2026 — tríplice viral / dose zero

Publicada:
- 18/09/2026.

Benchmark interno:
- 03/10/2026.

Estado esperado em 26/09:
- `within_benchmark`.

## Saída

Gerada automaticamente:

- `data/mart/regulatory_compliance.json`;
- `web/public/data/regulatory_compliance.json`.

## Frontend

Rota:

`/conformidade`

Exibe:

- atos rastreados;
- mudanças dentro do benchmark;
- mudanças com benchmark excedido e mapeamento pendente;
- datas;
- imunobiológicos associados;
- fonte oficial;
- ressalva de aplicabilidade.

## Build e deploy

CI e GitHub Pages executam:

```bash
python etl/regulatory_compliance.py
```

antes do build do Next.js.

Assim, o painel regulatório é recalculado a partir do código versionado, não mantido manualmente.

## Governança

O PREVNAR deve:

1. manter toda regra ligada ao ato oficial correspondente;
2. registrar `published_at` e `effective_from` quando disponíveis;
3. distinguir publicação, vigência e benchmark de atualização;
4. não declarar infração jurídica automaticamente;
5. não liberar monitoramento decisório com mapeamento de registro incompleto;
6. manter URLs oficiais auditáveis;
7. registrar divergências terminológicas explicitamente;
8. usar o Cursor e os agentes para revisar impactos de cada nova revisão oficial.

## Próxima evolução

Criar um **Regulatory Watch Agent** capaz de:

- verificar página oficial de Regras para Registros Vacinais;
- identificar nova versão da planilha de Regras de Entrada;
- identificar atualização do servidor terminológico;
- abrir/atualizar backlog;
- nunca alterar regra clínica automaticamente sem evidência estruturada e testes.
