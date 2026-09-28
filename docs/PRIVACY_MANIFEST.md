# PREVNAR — Privacy Manifest v2

## Objetivo

O `data/reference/privacy_manifest.json` transforma a governança de privacidade em um contrato executável por `source_id`.

A política é conservadora: classifica o maior risco plausível da fonte de origem e separa claramente processamento restrito de publicação agregada. Ela não substitui parecer jurídico, autorização institucional, registro de tratamento ou RIPD.

## Regras obrigatórias

1. Nenhuma fonte do `source_registry.json` pode ficar sem classificação.
2. Dado identificável, pseudonimizado, confidencial ou de saúde sensível não pode ser processado em `public_static`.
3. CPF e CNS nunca podem ser versionados no GitHub.
4. Linkage individual só pode ocorrer em `institutional_restricted`, com finalidade explícita.
5. Saída pública de fonte sensível exige `aggregate_only` e `disclosure_risk_review`.
6. Toda `legal_basis_refs` deve existir em `docs/legal_register.json`.
7. Fonte de saúde não agregada exige gate de RIPD.
8. O Release Guardian bloqueia qualquer violação estrutural.

## Ambientes

- `public_static`: artefatos públicos, documentação e marts agregados aprovados.
- `institutional_restricted`: HML/PRD ou ambiente institucional autorizado, com controle de acesso, trilha de auditoria e custódia adequada.

## Classificações

- `public`: dados públicos/agregados.
- `internal`: dados institucionais sem autorização automática para publicação.
- `confidential`: dados que exigem controle reforçado.
- `sensitive_health`: dados pessoais sensíveis de saúde ou fonte com capacidade de individualização.

## Relação com LGPD

O manifesto aplica por design os princípios de finalidade, adequação, necessidade, segurança, prevenção e responsabilização. Bases e atos utilizados devem ser referenciados por ID no registro legal do projeto.

Para dados sensíveis, o PREVNAR mantém postura fail-closed: ausência de base, finalidade, ambiente ou decisão de RIPD impede release.

## Cursor e agentes

Antes de criar ETL, linkage, mart ou endpoint:
- Data Agent identifica `source_id`;
- Evidence Agent valida autoridade e escopo;
- Legal & Privacy Agent valida o privacy manifest;
- Data Quality Agent verifica granularidade e risco de divulgação;
- Release Guardian executa o gate final.

A regra persistente do Cursor é `.cursor/rules/04-privacy-manifest.mdc`.

## Limite

Este documento é governança técnica do PREVNAR e não constitui parecer jurídico.
