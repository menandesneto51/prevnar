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
