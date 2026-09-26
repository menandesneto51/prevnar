# PREVNAR — Agentes

O Cursor é o ambiente padrão de implementação do PREVNAR. Todos os agentes devem respeitar a documentação em `docs/`.

## 1. PREVNAR Data Agent
Responsável por ingestão, manifestos, schema, proveniência, freshness e reconciliação de fontes.

Não altera dados-fonte. Não mascara falhas de extração com seed sem sinalização E5.

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
- small-cell checks.

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

## 7. PREVNAR Release Guardian
Bloqueia release quando houver:
- teste falhando;
- dado E5 em KPI decisório;
- fonte vencida sem aviso;
- norma sem referência;
- segredo versionado;
- dado pessoal no repositório;
- alteração metodológica sem versionamento;
- endpoint mutável exposto sem autenticação.

## Ordem recomendada
Data → Epidemiology → Quality → Legal/Privacy → Intelligence → Action → Release Guardian.


## Onboarding de imunobiológico

Antes de incorporar nova vacina, seguir `docs/ONBOARDING_IMUNOBIOLOGICO.md`.

Regras:
- Legal & Privacy Agent registra e valida os atos;
- Epidemiology Agent valida população, esquema, vigência e exceções;
- Data Agent vincula códigos e fontes;
- Data Quality Agent valida proveniência/freshness;
- Intelligence Agent só utiliza indicadores aprovados;
- Release Guardian valida referências cruzadas e bloqueia inconsistências.

Nenhum agente pode inserir regra clínica diretamente no código sem `rule_id` e `normative_acts`.
