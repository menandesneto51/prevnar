# PREVNAR — Agentes

O Cursor é o ambiente padrão de implementação do PREVNAR. Todos os agentes devem respeitar a documentação em `docs/`.

## 1. PREVNAR Data Agent
Responsável por ingestão, manifestos, schema, proveniência, freshness, reconciliação de fontes e evidência de mapeamento transacional.

Para imunobiológicos, mantém:
- código;
- estratégia;
- dose;
- grupo de atendimento;
- fonte oficial por dimensão

em `data/reference/registration_mapping_registry.json`.

Não altera dados-fonte. Não mascara falhas de extração com seed sem sinalização E5. Não promove mapeamento parcial a `confirmed`.

## 2. PREVNAR Epidemiology Agent
Valida:
- população;
- numerador;
- denominador;
- período;
- esquema vacinal;
- regra normativa;
- interpretação epidemiológica.

Deve bloquear cálculo de cobertura/gap quando numerador e denominador forem incompatíveis.

## 3. PREVNAR Data Quality Agent
Executa:
- completude;
- unicidade;
- validade;
- consistência;
- atraso;
- outliers;
- divergência entre fontes;
- small-cell checks;
- registration readiness.

Deve verificar se todas as dimensões obrigatórias estão `confirmed` antes de aceitar `etl_ready=true`.

## 4. PREVNAR Legal & Privacy Agent
Confere:
- finalidade;
- base normativa;
- hipótese LGPD;
- classificação do dado;
- necessidade;
- compartilhamento;
- RIPD;
- publicação;
- retenção;
- segurança.

Não substitui validação jurídica institucional.

## 5. PREVNAR Intelligence Agent
Produz insights somente a partir de indicadores aprovados pelo quality gate.

Toda saída deve diferenciar:
- fato observado;
- proxy;
- estimativa;
- inferência;
- recomendação operacional.

## 6. PREVNAR Action Agent
Traduz sinais aprovados em ações operacionais para gestão.

Não emite prescrição clínica individual nem substitui protocolo oficial.

## 7. PREVNAR Regulatory Watch Agent
Monitora mudanças oficiais que possam alterar regras clínicas, regras de registro, terminologias ou interoperabilidade.

Executa:
- identificação de nova publicação oficial;
- comparação com `legal_register.json`;
- cálculo do benchmark regulatório interno;
- associação com imunobiológicos e regras afetadas;
- abertura/atualização de backlog;
- sinalização de divergência entre orientação específica e servidor terminológico.

Não pode:
- ativar regra clínica por inferência;
- inventar estratégia/dose/grupo;
- definir `monitored=true` com mapeamento incompleto;
- declarar infração jurídica automaticamente.

Toda proposta de alteração deve seguir:
Regulatory Watch → Legal/Privacy → Epidemiology → Data → Quality → Release Guardian.

## 8. PREVNAR Release Guardian
Bloqueia release quando houver:
- teste falhando;
- dado E5 em KPI decisório;
- fonte vencida sem aviso;
- norma sem referência;
- segredo versionado;
- dado pessoal no repositório;
- alteração metodológica sem versionamento;
- endpoint mutável exposto sem autenticação;
- `monitored=true` com `etl_ready=false`;
- dimensão obrigatória de registro em `partial`/`pending` para imunobiológico monitorado.

## Ordem recomendada
Data → Epidemiology → Quality → Legal/Privacy → Regulatory Watch → Intelligence → Action → Release Guardian.


## Onboarding de imunobiológico

Antes de incorporar qualquer novo imunobiológico, seguir `docs/ONBOARDING_IMUNOBIOLOGICO.md`.

Regras:
- Legal & Privacy Agent registra e valida os atos;
- Epidemiology Agent valida população, estratégia, esquema/posologia operacional quando aplicável, vigência e exceções;
- Data Agent vincula códigos e fontes;
- Data Quality Agent valida proveniência/freshness;
- Intelligence Agent só utiliza indicadores aprovados;
- Release Guardian valida referências cruzadas e bloqueia inconsistências.

Nenhum agente pode inserir regra clínica diretamente no código sem `rule_id`, `immunobiologic_id` e `normative_acts`. Entidades em onboarding/draft não podem gerar recomendação automática.


## Escopo territorial e sistemas de código

Regras adicionais obrigatórias para todos os agentes:

- Legal & Privacy Agent deve validar `rule_context`, `geographic_scope`, vigência e ato normativo.
- Epidemiology Agent deve impedir que estratégia de bloqueio/intensificação local seja interpretada como rotina nacional.
- Data Agent deve identificar explicitamente o sistema de código de origem (PNI/RNDS, SIES, CNES etc.).
- Data Quality Agent deve sinalizar mapeamentos parciais e incompatibilidade entre sistemas de código.
- Intelligence Agent não pode agregar regra territorial fora de seu escopo.
- Release Guardian deve bloquear referências territoriais estruturalmente inválidas.

Ausência de contexto geográfico significa: somente regras nacionais podem ser resolvidas.


## Registration readiness entre agentes

Fluxo obrigatório:

1. Legal/Privacy Agent confirma fonte oficial e escopo.
2. Epidemiology Agent confirma que regra clínica e contexto estão corretamente separados.
3. Data Agent registra evidência de código/estratégia/dose/grupo.
4. Data Quality Agent executa `registration_readiness.py`.
5. Intelligence/Action Agents só usam ETL liberado.
6. Release Guardian bloqueia `monitored=true` sem `etl_ready=true`.

**Regra clínica completa e mapeamento transacional completo são estados independentes.**
