# PREVNAR — Privacy Manifest

## Objetivo

O arquivo `data/reference/privacy_manifest.json` classifica o risco de cada fonte e define onde ela pode ser processada e que tipo de saída pode chegar ao ambiente público.

A classificação é **operacional e conservadora**. Ela não substitui análise jurídica institucional, RIPD ou autorização de acesso.

## Princípio

A classificação considera o maior risco plausível da **fonte de origem**.

Por isso, uma fonte pode ser classificada como `sensitive_health` e, ao mesmo tempo, permitir um `public_mart_allowed=true`, desde que a saída seja agregada e minimizada.

Isso não significa que a fonte bruta possa existir no ambiente público.

## Campos principais

- `source_id`
- `data_classification`
- `identification_level`
- `contains_cpf`
- `contains_cns`
- `contains_health_data`
- `linkage_policy`
- `linkage_allowed_in_repo`
- `allowed_environments`
- `public_mart_allowed`
- `public_output_requirements`
- `retention_policy`
- `controller`
- `custodian`
- `legal_basis_refs`
- `ripd_required`

## Classificações

### public

Fonte pública e agregada, sem identificadores pessoais esperados na camada usada pelo PREVNAR.

### internal

Fonte administrativa ou institucional cujo acesso/tratamento não deve ser presumido como público.

### confidential

Fonte que exige controle reforçado de acesso e divulgação.

### sensitive_health

Fonte que contém ou pode derivar informação de saúde referente a pessoas.

## Nível de identificação

### aggregate

Sem granularidade individual na camada considerada.

### pseudonymized

Possui chave técnica/pseudônima que ainda pode permitir distinção ou linkage.

Pseudonimização **não equivale a anonimização**.

### identifiable

Pode conter identificadores diretos ou informações suficientes para identificação.

## Linkage

No repositório público:

```json
"linkage_allowed_in_repo": false
```

é obrigatório para todas as fontes.

Quando necessário, linkage individual só pode ocorrer em ambiente institucional autorizado e conforme a finalidade documentada.

## Saída pública

Fontes sensíveis só podem produzir mart público quando:
- `public_mart_allowed=true`;
- `aggregate_only` estiver nos requisitos;
- não houver identificador individual;
- o grain não crie risco indevido de divulgação;
- o Release Guardian e revisão metodológica forem aprovados.

## Release Guardian

O Guardian bloqueia:
- fonte sem privacy manifest;
- manifesto órfão;
- classificação inválida;
- ambiente inválido;
- linkage habilitado no repositório;
- base legal referenciada mas ausente;
- fonte sensível com saída pública sem agregação obrigatória.

## Relação com a governança RNDS

Ver também:

`docs/GOVERNANCA_RNDS_DADOS_VACINAIS.md`

O privacy manifest é a camada estruturada e executável dessa política.
