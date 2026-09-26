# PREVNAR v2.0 — Roadmap técnico

## Objetivo

Evoluir o Radar VPC20 para plataforma reutilizável de inteligência em imunização, preservando o painel atual e removendo dependências hard-coded de uma única vacina ou tipo de imunobiológico.

## P0 — Fundação

- [x] substituir conceito de gap nacional por oportunidades estimadas quando não houver deduplicação;
- [x] adicionar `evidence_level` aos indicadores;
- [x] adicionar registro de proveniência;
- [x] adicionar freshness por fonte;
- [x] implantar testes Python e validação TypeScript por lint/build;
- [x] criar legal/privacy gate;
- [x] remover `verify=False` como fallback silencioso;
- [x] tornar execução Python portável;
- [x] autenticar rotas server-side antes de qualquer exposição externa.

## P1 — Motor configurável

- [x] `vaccine_registry.json`;
- [x] `normative_rules.json`;
- [x] motor de elegibilidade versionado;
- [x] motor de esquema vacinal;
- [x] versionamento de população-alvo;
- [x] separação observado/proxy/estimado/manual/demonstrativo.

## P2 — Generalização e agentes

- [x] criar `immunobiologic_registry.json`;
- [x] suportar `vaccine | monoclonal_antibody | immunoglobulin | other`;
- [x] manter compatibilidade com `vaccine_registry.json`;
- [x] generalizar o motor normativo para `immunobiologic_id`;
- [x] impedir regras `draft` de gerar recomendação automática;

### Agentes

- [ ] Data Agent;
- [ ] Epidemiology Agent;
- [ ] Data Quality Agent;
- [ ] Legal & Privacy Agent;
- [ ] Intelligence Agent;
- [ ] Action Agent;
- [x] Release Guardian.

## P3 — Inteligência

- [ ] detecção de anomalias;
- [ ] nowcast;
- [ ] forecast;
- [ ] priorização territorial;
- [ ] oportunidade por serviço/território;
- [ ] recomendações operacionais explicáveis;
- [ ] cards municipais.

## P4 — Novos imunobiológicos

A entrada de novo imunobiológico deverá exigir configuração e documentação, não duplicação do sistema.

Candidatos:
- VSR;
- influenza;
- HPV;
- febre amarela;
- tríplice viral;
- meningocócicas;
- covid-19;
- outras estratégias especiais do CRIE/RIE.

## Definition of Done

Uma feature só está concluída se:
1. código implementado;
2. testes passando;
3. documentação atualizada;
4. fonte e método versionados;
5. avaliação LGPD realizada quando aplicável;
6. Cursor rules respeitadas;
7. Release Guardian aprovado.
