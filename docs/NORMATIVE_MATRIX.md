# PREVNAR — Matriz normativa auditável

## Objetivo

A matriz normativa oferece uma visão única de rastreabilidade entre:

- imunobiológico;
- código nacional;
- regra estruturada;
- status da regra;
- vigência;
- contexto;
- escopo geográfico;
- ato normativo;
- URL oficial;
- maturidade do dado.

## Gerador

`etl/build_normative_matrix.py`

## Fontes canônicas

A matriz é derivada exclusivamente de:

- `data/reference/immunobiologic_registry.json`;
- `data/reference/normative_rules.json`;
- `docs/legal_register.json`.

Nenhuma norma deve ser cadastrada apenas na matriz.

## Saídas

- `data/mart/normative_matrix.json`;
- `web/public/data/normative_matrix.json`.

## Conceitos separados

### Entidade ativa

O imunobiológico existe e está habilitado no registry.

### Regra ativa

A regra possui:
- `status = active`;
- data de vigência compatível com `as_of`.

### Monitorado

O PREVNAR possui camada de monitoramento habilitada para a entidade.

### Mapeamento de dados

`onboarding_status` e `code_mapping_status` representam maturidade da integração de dados.

**Regra ativa não significa dado disponível.**

**Código confirmado não significa regra de entrada completa.**

## Escopo geográfico

Toda regra deve expor:

```json
{
  "geographic_scope": {
    "type": "national|state|municipality|polygon|facility",
    "codes": []
  }
}
```

Isso evita que:
- bloqueios locais;
- campanhas municipais;
- intensificações territoriais;
- recomendações temporárias

sejam interpretadas como regra nacional.

## Integridade legal

Toda referência em `normative_acts` deve resolver para `docs/legal_register.json`.

A matriz expõe:

`summary.unresolved_legal_references`

O valor esperado para release é:

```json
[]
```

## Uso no frontend

A rota `/normas` deve permitir:
- visualizar maturidade;
- distinguir regra ativa/draft;
- conferir vigência;
- conferir escopo;
- acessar URL oficial;
- verificar o estado do mapeamento de dados.

## Execução

```bash
python etl/build_normative_matrix.py
```

## Regra de governança

A matriz é uma ferramenta de rastreabilidade.

Ela não substitui:
- leitura da norma;
- avaliação clínica;
- governança de dados;
- revisão epidemiológica;
- Release Guardian.


## Backlog derivado

O módulo `etl/normative_backlog.py` deriva automaticamente pendências a partir da matriz.

Categorias atuais:
- `normative_rule_pending`;
- `normative_rule_partial` — há regras ativas, mas parte do escopo ainda permanece em draft;
- `data_mapping_incomplete`;
- `national_code_missing`;
- `monitoring_not_enabled`.

A prioridade P1/P2 é **técnica/metodológica**, não prioridade clínica.

Saídas:
- `data/mart/normative_backlog.json`;
- `web/public/data/normative_backlog.json`.

A rota `/normas` apresenta até 20 pendências prioritárias e o próximo gate esperado para cada uma.
