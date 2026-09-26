# PREVNAR — Immunobiologic Registry

**Versão:** 1.0  
**Data:** 26/09/2026

## Motivação

O PREVNAR deixa de modelar somente vacinas.

O PNI e a rede de imunização trabalham também com outros imunobiológicos, como:
- anticorpos monoclonais;
- imunoglobulinas;
- outros produtos de prevenção/imunização passiva.

Por isso, a entidade canônica passa a ser **imunobiológico**.

## Fonte canônica

`data/reference/immunobiologic_registry.json`

Tipos suportados:

```text
vaccine
monoclonal_antibody
immunoglobulin
other
```

Identificador canônico:

```text
immunobiologic_id
```

## Compatibilidade

Durante a migração:

- `vaccine_registry.json` permanece como view específica de vacinas;
- `vaccine_id` continua aceito nas regras antigas;
- cada regra nova deve usar `immunobiologic_id`;
- wrappers como `get_vaccine()` e `vaccine_codes()` continuam funcionando.

A VPC20 é preservada integralmente como:

```json
{
  "immunobiologic_id": "vpc20",
  "type": "vaccine",
  "vaccine_id": "vpc20"
}
```

## Nirsevimabe

O nirsevimabe entra inicialmente como:

```json
{
  "immunobiologic_id": "nirsevimab",
  "type": "monoclonal_antibody",
  "onboarding_status": "normative_discovery"
}
```

A entidade referencia os atos normativos já identificados, mas **não possui regra clínica ativa** nesta etapa.

A regra `nirsevimab_onboarding_2026` possui:

```text
status = draft
rule_type = onboarding_metadata
```

Consequência:

- `active_rules("nirsevimab")` retorna vazio;
- o motor não declara elegibilidade;
- o motor não recomenda dose;
- nenhuma regra clínica é inferida antes da conclusão do onboarding específico.

## Motor

O módulo histórico `etl/vaccine_rules.py` permanece com esse nome temporariamente por compatibilidade, mas opera sobre o Immunobiologic Registry.

Novos consumidores devem preferir:

- `get_immunobiologic()`;
- `immunobiologic_codes()`;
- `active_rules()`;
- `evaluate_operational()`.

## Integridade

O Release Guardian verifica:

- `immunobiologic_id` existente;
- tipo permitido;
- referência normativa existente;
- rule_id único;
- compatibilidade entre vaccine registry e immunobiologic registry;
- ausência de regra ativa sem entidade registrada.

## Princípio de ativação

Cadastrar uma entidade não significa ativar uma recomendação.

Estados possíveis de onboarding devem ser tratados separadamente, por exemplo:

```text
normative_discovery
data_mapping
methodology_review
testing
ready_for_activation
active
deprecated
```

Somente regras explicitamente marcadas como `active` e dentro de sua vigência entram no motor.

## Próxima etapa

A issue #13 deve fazer o onboarding respiratório com:
- nirsevimabe;
- vacina contra VSR em gestantes;
- influenza;
- covid-19.

Nenhuma dessas regras deve ser ativada antes da validação normativa, epidemiológica e dos testes correspondentes.
