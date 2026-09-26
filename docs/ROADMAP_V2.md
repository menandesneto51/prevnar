# PREVNAR v2.0 — Roadmap técnico

## Objetivo

Evoluir o Radar VPC20 para plataforma reutilizável de inteligência vacinal, preservando o painel atual e removendo dependências hard-coded de uma única vacina.

## P0 — Fundação

- [ ] substituir conceito de gap nacional por oportunidades estimadas quando não houver deduplicação;
- [ ] adicionar `evidence_level` aos indicadores;
- [ ] adicionar registro de proveniência;
- [ ] adicionar freshness por fonte;
- [ ] implantar testes Python e TypeScript;
- [ ] criar legal/privacy gate;
- [ ] remover `verify=False` como fallback silencioso;
- [ ] tornar execução Python portável;
- [ ] autenticar rotas server-side antes de qualquer exposição externa.

## P1 — Motor configurável

- [ ] `vaccine_registry.json`;
- [ ] `normative_rules.json`;
- [ ] motor de elegibilidade versionado;
- [ ] motor de esquema vacinal;
- [ ] versionamento de população-alvo;
- [ ] separação observado/proxy/estimado/manual/demonstrativo.

## P2 — Agentes

- [ ] Data Agent;
- [ ] Epidemiology Agent;
- [ ] Data Quality Agent;
- [ ] Legal & Privacy Agent;
- [ ] Intelligence Agent;
- [ ] Action Agent;
- [ ] Release Guardian.

## P3 — Inteligência

- [ ] detecção de anomalias;
- [ ] nowcast;
- [ ] forecast;
- [ ] priorização territorial;
- [ ] oportunidade por serviço/território;
- [ ] recomendações operacionais explicáveis;
- [ ] cards municipais.

## P4 — Novos imunobiológicos

A entrada de nova vacina deverá exigir configuração e documentação, não duplicação do sistema.

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
