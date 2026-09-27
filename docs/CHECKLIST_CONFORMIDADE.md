# PREVNAR — Checklist de conformidade

## A. Nova fonte

- [ ] source_id único
- [ ] finalidade documentada
- [ ] fonte oficial identificada
- [ ] responsável institucional identificado
- [ ] período/frequência definidos
- [ ] classificação do dado
- [ ] hipótese LGPD avaliada quando aplicável
- [ ] compartilhamento avaliado
- [ ] triagem de RIPD concluída
- [ ] schema documentado
- [ ] manifesto/proveniência implantado
- [ ] freshness SLA definido
- [ ] retenção/descarte definidos
- [ ] política de publicação definida
- [ ] teste de qualidade criado

## B. Novo indicador

- [ ] numerator_definition
- [ ] denominator_definition
- [ ] population_definition
- [ ] temporal_grain
- [ ] geographic_grain
- [ ] source_id
- [ ] evidence_level
- [ ] method_version
- [ ] limitações
- [ ] regra de supressão
- [ ] regra normativa associada quando aplicável
- [ ] teste unitário
- [ ] teste de consistência
- [ ] decision_grade definido

## C. Nova regra clínica/vacinal

- [ ] ato normativo oficial
- [ ] vigência
- [ ] população
- [ ] vacina
- [ ] esquema
- [ ] intervalos
- [ ] exceções
- [ ] regra anterior identificada
- [ ] impacto calculado
- [ ] validação epidemiológica
- [ ] teste automatizado
- [ ] versão incrementada

## D. Release

- [ ] testes Python passando
- [ ] lint/build frontend passando
- [ ] nenhum segredo detectado
- [ ] nenhum dado pessoal/sensível versionado
- [ ] fontes dentro do SLA ou claramente sinalizadas
- [ ] E5 ausente de KPIs decisórios
- [ ] metodologia versionada
- [ ] legal register válido
- [ ] RIPD/privacidade revisado quando aplicável
- [ ] proveniência completa
- [ ] diff de indicadores revisado
- [ ] Release Guardian aprovado


## E. Mudança normativa/terminológica

- [ ] Regulatory Watch consultado
- [ ] fonte oficial confirmada
- [ ] data de publicação registrada
- [ ] vigência registrada quando disponível
- [ ] ato incluído no legal register
- [ ] normative_rules afetadas identificadas
- [ ] imunobiológicos afetados identificados
- [ ] benchmark de 15 dias calculado
- [ ] Regras de Entrada revisadas
- [ ] BRImunobiologico revisado
- [ ] BREstrategiaVacinacao revisado
- [ ] divergências terminológicas registradas
- [ ] nenhuma estratégia/dose/grupo inferida
- [ ] backlog aberto quando mapping permanecer parcial
- [ ] testes de regressão atualizados
- [ ] Release Guardian aprovado

## F. Integração RNDS / sistema de registro

Aplicável somente se a feature registrar ou transmitir eventos vacinais.

- [ ] modelo RIA vigente identificado
- [ ] sistema homologado/integrado à RNDS
- [ ] retorno de integração armazenado
- [ ] identificador do registro armazenado
- [ ] status sucesso/erro armazenado
- [ ] retry/idempotência definidos
- [ ] SLA 24h para salas com conectividade considerado
- [ ] fluxo de até 15 dias para ausência de conectividade considerado
- [ ] atualização em até 15 dias após revisão técnica considerada
- [ ] auditoria e rastreabilidade implantadas
- [ ] privacidade/RIPD revistos
- [ ] homologação institucional documentada

## G. Dados nominais e IA

- [ ] necessidade de dado nominal demonstrada
- [ ] minimização aplicada
- [ ] identificadores excluídos de Git/logs/frontend
- [ ] operador/serviço externo avaliado
- [ ] finalidade e base legal documentadas
- [ ] transferência/compartilhamento avaliados
- [ ] RIPD avaliado
- [ ] saída pública agregada/suprimida
- [ ] nenhum prompt externo recebe identificador sem autorização explícita
