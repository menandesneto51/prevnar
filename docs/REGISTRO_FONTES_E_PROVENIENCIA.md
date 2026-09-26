# PREVNAR — Registro de fontes e proveniência

**Versão:** 1.0  
**Data:** 26/09/2026

## Regra

Todo valor exibido no painel deve ser rastreável até:
**fonte → arquivo/lote → transformação → regra → mart → indicador**.

## Registro atual

| Fonte | Domínio | Natureza | Evidência esperada | Situação |
|---|---|---|---|---|
| OpenDataSUS/PNI | vacinação | observado | E1/E2 | ativo; sem CID na carga atual |
| CKAN PNI | vacinação | observado | E1/E2 | ativo |
| IBGE 6579 | população | observado/estimativa oficial | E1 | ativo |
| SIDRA estrutura etária | população | observado oficial | E1 | parcial/proxy em pontos |
| CNES | oferta/CRIE | cadastro | E1/E4 | requer lista definitiva |
| SIES | estoque | observado | E1/E2 | parcial para VPC20 |
| ESAVI | segurança | observado | E1 | carga atual incompleta |
| SINAN | desfechos | observado | E1 | automatização pendente |
| SIH | internações | observado | E1 | automatização pendente |
| SIM | mortalidade | observado | E1 | automatização pendente |
| SRAG | respiratório | observado/amostra | E1/E2 | amostra paginada |
| BPS | custos | observado | E1/E4 | validar atualização |
| SIOPS | gasto | observado | E1/E4 | validar atualização |
| cadastros Situação 1 | elegibilidade | administrativo | E4 | cargas institucionais necessárias |

## Metadados obrigatórios

Cada artefato de ingestão deverá gerar manifesto:

```json
{
  "run_id": "...",
  "source_id": "...",
  "source_url": "...",
  "retrieved_at": "...",
  "reference_period": "...",
  "file_hash": "...",
  "record_count": 0,
  "schema_version": "...",
  "pipeline_version": "...",
  "status": "success",
  "warnings": []
}
```

## Proveniência dos marts

Todo mart deve registrar:
- `generated_at`;
- `run_ids`;
- `source_ids`;
- `method_version`;
- `normative_rule_versions`;
- `quality_status`;
- `freshness_status`.

## Proibição

Não usar no painel de produção valor que não possa ser rastreado a uma fonte e método identificáveis.


## Registro operacional de fontes

O arquivo `data/reference/source_registry.json` é o registro estruturado consumido pelo pipeline.

Ele define, por `source_id`:
- domínio;
- cadência operacional esperada;
- limite interno de atenção;
- limite interno de desatualização;
- criticidade para decisão.

**Esses limites são política operacional interna do PREVNAR e não SLA oficial das instituições de origem.**

## Freshness

Estados:

- `atual` — dentro da janela operacional esperada;
- `atencao` — ultrapassou a janela de atenção;
- `desatualizado` — ultrapassou o limite de uso corrente definido para a fonte;
- `desconhecido` — período ou política não puderam ser determinados.

O status deve usar o **período de referência do dado**, e não apenas a data em que o ETL foi executado.

Exemplo: reconstruir hoje um mart com PNI de junho não torna junho um dado atual.

## Manifestos de execução

O módulo `etl/provenance.py` grava:

- `data/mart/_meta/runs/<source>-<timestamp>-<run>.json`;
- `data/mart/_meta/latest/<source>.json`.

Cada manifesto contém:
- run_id;
- source_id;
- retrieved_at;
- reference_period;
- record_count;
- status;
- schema_version;
- pipeline_version;
- warnings;
- hashes SHA-256 dos arquivos disponíveis;
- freshness.

O `run_id` e a freshness devem ser propagados aos marts que utilizam a fonte.
