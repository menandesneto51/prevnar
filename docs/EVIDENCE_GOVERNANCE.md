# PREVNAR — Governança de evidências

## Objetivo

Separar claramente:
- norma canônica;
- terminologia oficial;
- artefato oficial de registro;
- fonte operacional;
- evidência suplementar;
- fonte institucional;
- fonte secundária.

Nenhuma evidência pode ser promovida acima da autoridade que realmente possui.

## Hierarquia operacional

1. legislação;
2. ato normativo federal;
3. terminologia oficial;
4. artefato oficial de registro;
5. ato normativo estadual;
6. manual oficial;
7. fonte institucional autorizada;
8. evidência oficial suplementar;
9. fonte secundária.

## Regras

### Regra nacional

Somente fonte federal com atribuição normativa pode definir regra nacional.

Terminologia oficial pode confirmar:
- código;
- conceito;
- sistema de código.

Terminologia, isoladamente, não cria:
- população elegível;
- esquema;
- intervalo;
- contraindicação.

### Evidência estadual/municipal

Pode:
- esclarecer implementação local;
- apoiar descoberta;
- documentar operacionalização territorial.

Não pode:
- ser promovida automaticamente a regra nacional;
- sobrescrever ato federal vigente;
- preencher lacuna federal como se fosse fonte canônica.

### Fonte institucional

Pode ser decision-grade para o seu domínio quando:
- acesso é autorizado;
- schema validado;
- proveniência conhecida;
- freshness aceitável;
- governança aprovada.

Não cria regra normativa nacional.

## Registry

Arquivo:

`data/reference/evidence_registry.json`

Campos centrais:
- `evidence_id`;
- `evidence_class`;
- `authority_level`;
- `authority_scope`;
- `canonical`;
- `can_define_national_rule`;
- `can_confirm_registration_mapping`;
- `decision_grade`;
- `supports`;
- `limitations`.

## Validador

`etl/evidence_governance.py`

## Release Guardian

Bloqueia:
- evidência canônica não oficial;
- fonte suplementar definindo regra nacional;
- fonte não federal definindo regra nacional;
- classe inválida marcada como canônica;
- fonte institucional sem política de acesso.

## Exemplo covid-19

A NT 91/2026:
- é normativa federal;
- pode sustentar regra nacional;
- confirma o uso do código 87 no contexto da LP.8.1.

BRImunobiologico:
- é terminologia oficial;
- confirma `87 = COVID-19 PFIZER - COMIRNATY`;
- não define elegibilidade clínica isoladamente.

Regras de Entrada de Dados 4:
- é artefato oficial de registro;
- deve ser a fonte canônica para estratégia/dose/grupos;
- enquanto o conteúdo estruturado não for ingerido, o ETL permanece bloqueado.

Documentos estaduais:
- podem corroborar padrões de implementação;
- não substituem a Regra de Entrada federal.

## Agentes

O PREVNAR Evidence Agent:
- classifica a autoridade da fonte;
- resolve hierarquia;
- impede promoção indevida;
- registra conflitos;
- encaminha regras clínicas ao Epidemiology Agent apenas quando a evidência for adequada ao escopo.

## Cursor

Toda implementação futura deve consultar o Evidence Registry antes de:
- ativar regra;
- preencher mapping pendente;
- promover indicador a decision-grade;
- alterar escopo territorial.
