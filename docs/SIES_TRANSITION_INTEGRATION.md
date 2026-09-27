# PREVNAR — Integração SIES/DW para logística e transição covid-19

## Objetivo

Separar corretamente duas fontes que respondem a perguntas diferentes:

1. **SIES público / Dados Abertos** — doses distribuídas;
2. **SIES/DW institucional autorizado** — saldo de estoque, lote, validade, perdas e capacidade logística.

Essas fontes **não são intercambiáveis**.

## Fonte pública

Endpoint oficial:

`https://apidadosabertos.saude.gov.br/vacinacao/sistema-de-informacao-de-insumos-estrategicos`

Dataset:

`https://dadosabertos.saude.gov.br/dataset/sies`

Semântica no PREVNAR:

```text
source_id = sies
data_semantics = distributed_doses
```

Pode apoiar:
- análise de distribuição;
- razão distribuído/aplicado;
- distribuição territorial.

Não pode, isoladamente, responder:
- saldo atual;
- risco de vencimento por lote;
- perdas físicas/técnicas atuais;
- capacidade de cadeia de frio;
- necessidade imediata de reposição.

## Correções realizadas no legado

Foram removidos:

- fallback TLS sem verificação;
- seed de distribuição apresentado quando a API falhava;
- promoção automática de "pneumo total" para VPC20;
- linguagem de frontend que chamava distribuição de "estoque".

A rota histórica `/estoque` permanece por compatibilidade, mas apresenta a semântica correta de **Distribuição SIES**.

## Fonte institucional

Source registry:

`sies_institutional_inventory`

Aquisição prevista:

- exportação SIES autorizada; ou
- consulta ao DW institucional; ou
- camada Gold equivalente validada pela SES-MT.

### Schema

`data/reference/covid19_transition_inventory_schema.json`

Contrato de fonte:

`data/reference/sies_transition_source_contract.json`

Template:

`data/manual/templates/covid19_transition_inventory_template.csv`

Grão:

```text
reference_date
+ territory_code
+ facility_cnes
+ product_variant_id
+ lot
```

## Privacidade

A camada é exclusivamente logística e agregada.

Campos proibidos incluem:
- CPF;
- CNS;
- nome do paciente;
- identificador de paciente;
- hash de paciente.

O adaptador rejeita arquivos que contenham esses campos.

## Adaptador

`etl/sies_transition_adapter.py`

Entrada:

- CSV;
- JSON.

Aceita nomes canônicos e aliases controlados em português.

Exemplo:

```bash
python etl/sies_transition_adapter.py data/manual/covid19_estoque.csv
```

O arquivo real deve permanecer fora do versionamento quando contiver dados institucionais não públicos.

## Saída

- `data/mart/covid19_transition_dashboard.json`;
- `web/public/data/covid19_transition_dashboard.json`;
- manifest em `data/mart/_meta`.

O manifest registra:
- SHA-256 do arquivo de entrada;
- tamanho;
- horário de processamento;
- período de referência;
- freshness;
- warnings.

As linhas brutas **não são copiadas para o mart**.

## Alertas

O adaptador usa:

`etl/covid19_transition_alerts.py`

Alertas atuais:
- risco de vencimento;
- estoque alto com consumo baixo;
- aumento de perdas;
- capacidade de cadeia de frio;
- solicitação acima do consumo recente.

Os thresholds são parâmetros internos do PREVNAR e devem ser validados institucionalmente.

## Frontend

A rota `/respiratorio` apresenta, quando existir carga institucional:

- saldo disponível;
- doses aplicadas nos últimos 30 dias;
- perdas;
- alertas críticos;
- freshness;
- distribuição territorial;
- alertas por lote.

Sem carga institucional, o painel não fabrica números e informa que a integração está pendente.

## SIES público e VPC20

A classificação pública mantém:

- `por_uf_pneumo`: pneumocócicas identificadas;
- `por_uf_vpc20`: apenas VPC20 identificado diretamente;
- `por_uf_distribuidas`: VPC20 identificado diretamente para compatibilidade.

Se não houver VPC20 diretamente identificável, o PREVNAR retorna vazio em vez de substituir por VPC10/VPC13/pneumo total.

## Cursor

Regra persistente:

`.cursor/rules/02-sies-logistics.mdc`

Todo desenvolvimento futuro deve preservar:
- separação distribuição × estoque;
- ausência de seeds decisórios;
- TLS validado;
- privacidade;
- proveniência;
- semântica explícita.
