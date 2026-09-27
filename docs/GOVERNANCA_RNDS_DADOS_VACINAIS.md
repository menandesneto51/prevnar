# PREVNAR — Governança RNDS, LGPD e dados vacinais

**Versão:** 1.0  
**Data:** 26/09/2026  
**Escopo:** ingestão, processamento, linkage, marts, APIs, logs e publicação de dados de imunização.

## 1. Finalidade

Este documento estabelece a governança mínima para o tratamento de dados vacinais no PREVNAR.

O objetivo é conciliar:
- vigilância epidemiológica;
- monitoramento do Programa Nacional de Imunizações;
- inteligência para gestão;
- interoperabilidade com a RNDS;
- proteção de dados pessoais e dados de saúde;
- rastreabilidade metodológica;
- publicação segura de indicadores agregados.

## 2. Base normativa principal

### Lei nº 6.259/1975

Base legal do Programa Nacional de Imunizações e da vigilância epidemiológica.

Registro no PREVNAR:

`lei_6259_1975`

### Lei nº 8.080/1990

Fundamento da organização do SUS, planejamento, vigilância e utilização de informações em saúde.

Registro:

`lei_8080_1990`

### Lei nº 13.709/2018 — LGPD

Dados referentes à saúde são dados pessoais sensíveis.

O tratamento pelo PREVNAR deve observar, entre outros princípios:
- finalidade;
- adequação;
- necessidade;
- segurança;
- prevenção;
- transparência;
- responsabilização e prestação de contas.

Registro:

`lgpd`

### Portaria GM/MS nº 5.663/2024

Estabelece que os sistemas de registro de vacinação encaminhem os dados de doses aplicadas à Rede Nacional de Dados em Saúde — RNDS, conforme o modelo de Registro de Imunobiológico Aplicado — RIA vigente.

Registro:

`portaria_5663_2024_rnds_vacinacao`

Fonte oficial:

https://bvsms.saude.gov.br/bvs/saudelegis/gm/2024/prt5663_04_11_2024.html

#### Prazos e obrigações estruturadas

A Portaria estabelece:
- envio em até 24 horas para salas com conectividade;
- envio em até 15 dias para salas sem conectividade;
- armazenamento do retorno de integração, identificador do registro e status de sucesso/erro;
- até 15 dias para adequação de sistemas que registram vacinação após revisão das orientações técnicas;
- até 15 dias para o DPNI/SVSA publicar regras de novo registro de imunobiológico após liberação pela Anvisa, condicionado aos ajustes da RNDS.

#### Aplicabilidade ao PREVNAR

O PREVNAR atual é uma camada de **inteligência analítica**. Não deve se apresentar como sistema de registro vacinal ou emissor RIA sem que essa função seja explicitamente incorporada e homologada.

Enquanto permanecer analítico:
- os prazos de transmissão RIA não são tratados como SLA do PREVNAR;
- o prazo de 15 dias para adequação é usado como benchmark interno;
- a rota `/conformidade` não constitui parecer jurídico.

Se futuramente o PREVNAR registrar ou transmitir eventos vacinais, deverão ser adicionados:
- validação do modelo RIA vigente;
- controle de retorno da RNDS;
- idempotência;
- identificador de evento;
- fila/reprocessamento;
- SLA de envio;
- trilha de auditoria;
- homologação institucional.

### Nota Técnica nº 115/2024-DPNI/SVSA/MS

Orienta sistemas próprios e de terceiros na integração com a base nacional de imunização/RNDS.

Entre os controles descritos estão:
- envio de registros à RNDS;
- utilização do modelo RIA vigente;
- validação da identificação do cidadão;
- requisitos de identificação do estabelecimento/profissional;
- qualidade do registro.

Registro:

`nt_115_2024_rnds_registro_vacinal`

Fonte oficial:

https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/notas-tecnicas/2024/nota-tecnica-no-115-2024-dpni-svsa-ms/view

### Decreto Federal nº 12.560/2025

Integra a base federal de governança do SUS Digital/RNDS e compartilhamento de dados de saúde.

Registro:

`decreto_12560_2025`

### Mato Grosso

O ambiente institucional estadual deve observar também:
- Decreto Estadual nº 1.427/2025 — governança/LGPD;
- Decreto Estadual nº 1.428/2025 — segurança da informação.

Registros:

- `mt_decreto_1427_2025`;
- `mt_decreto_1428_2025`.

## 3. Modelo de ambientes

### 3.1 Repositório GitHub / aplicação pública

Permitido:
- código;
- regras normativas;
- catálogos;
- tabelas de referência públicas;
- indicadores agregados;
- manifests sem identificadores pessoais;
- estatísticas por território quando respeitados os critérios de divulgação.

Proibido:
- CPF;
- CNS;
- nome;
- endereço;
- telefone;
- e-mail do cidadão;
- data de nascimento nominal;
- identificadores de prontuário;
- chaves de linkage reversíveis;
- tokens;
- senhas;
- credenciais;
- arquivos brutos nominais.

### 3.2 Ambiente institucional restrito

Pode processar dados individualizados somente quando:
- houver finalidade institucional definida;
- acesso estiver autorizado;
- a fonte permitir o tratamento;
- a infraestrutura atender aos controles de segurança;
- o princípio da necessidade for respeitado;
- houver rastreabilidade de execução/acesso.

Linkages individualizados entre RNDS/PNI, SINASC, e-SUS APS, SISREG, SIH, SINAN ou outras bases devem ocorrer apenas nesse ambiente.

## 4. Camadas de dados

### Raw / Bronze

Pode conter informação individual somente no ambiente institucional autorizado.

Requisitos:
- nunca versionar no Git;
- criptografia em repouso quando suportada;
- controle de acesso;
- retenção definida;
- origem e data de extração;
- registro de execução.

### Silver

Preferir:
- pseudonimização;
- chaves técnicas;
- minimização de colunas;
- separação entre identidade e atributos analíticos.

A pseudonimização não transforma automaticamente o dado em dado anônimo.

### Gold / Marts

Por padrão devem ser:
- agregados;
- minimizados;
- sem CPF/CNS;
- sem identificador individual persistido;
- com grain explicitamente documentado;
- com provenance;
- com freshness;
- com evidence_level.

## 5. Deduplicação

Quando um identificador individual for necessário para `COUNT DISTINCT`:

1. processá-lo somente no ambiente autorizado;
2. preferir uso transitório em memória;
3. não persistir identificadores no mart quando não necessários;
4. nunca incluí-los no frontend público;
5. nunca incluí-los em logs/manifests.

O `respiratory_etl.py` segue esse padrão: identificadores são usados para deduplicação e descartados antes da persistência.

## 6. Linkage

Linkage individual é permitido apenas quando necessário para responder a uma finalidade definida.

Exemplos:
- VVSR + pré-natal para oportunidade >=28 semanas;
- nirsevimabe + prematuridade/comorbidade;
- vacinação + SINASC;
- vacinação + desfechos epidemiológicos em desenho de estudo aprovado.

Antes de implantar um novo linkage, documentar:
- finalidade;
- bases;
- variáveis utilizadas;
- método de vinculação;
- taxa de linkage;
- falso positivo/falso negativo quando aplicável;
- saída necessária;
- risco de reidentificação;
- política de retenção.

Quando o risco e a natureza do tratamento justificarem, submeter o fluxo à avaliação institucional de privacidade/RIPD.

## 7. Logs

Logs não devem registrar:
- CPF;
- CNS;
- nome;
- payload nominal;
- token;
- senha;
- segredo.

Logs devem privilegiar:
- run_id;
- source_id;
- contagem de registros;
- tempo de execução;
- período de referência;
- status;
- erro técnico sanitizado.

## 8. Proveniência

Cada carga deve registrar, quando aplicável:

- run_id;
- source_id;
- retrieved_at;
- reference_period;
- schema_version;
- pipeline_version;
- record_count;
- warnings;
- hashes de arquivos;
- freshness.

Ver:

`etl/provenance.py`

## 9. Publicação

Um indicador não deve ser publicado apenas porque foi calculado.

Antes da publicação:
1. validar grain;
2. validar denominador;
3. validar evidence_level;
4. validar decision_grade;
5. validar freshness;
6. validar risco de divulgação;
7. validar escopo territorial;
8. executar Release Guardian.

## 10. APIs administrativas

Rotas que alteram dados ou executam ETL são administrativas.

Em deploy server-side:
- exigir autenticação;
- usar `PREVNAR_API_TOKEN`;
- limitar upload;
- validar conteúdo;
- não devolver caminhos internos;
- não expor erros contendo dados sensíveis.

No GitHub Pages público, o PREVNAR deve permanecer somente leitura.

## 11. Segredos

Segredos devem existir somente em:
- variáveis de ambiente;
- secret stores;
- GitHub Actions Secrets quando aplicável.

Nunca versionar:
- `.env` com segredo;
- token OAuth;
- chave privada;
- credencial de banco;
- senha;
- certificado privado.

## 12. Release Guardian

O Release Guardian verifica automaticamente, entre outros controles:
- registro legal;
- domínios oficiais das fontes normativas;
- source registry;
- referências normativas;
- evidence/decision-grade;
- freshness crítica;
- fixtures;
- possíveis segredos;
- CPF/CNS versionados;
- rotas mutáveis sem proteção.

O Guardian é um gate técnico; não substitui análise jurídica ou de segurança institucional.

## 13. Regra de ouro

**Dado nominal entra no PREVNAR apenas quando necessário, em ambiente institucional autorizado, e deve sair do pipeline analítico tão cedo quanto possível.**

A aplicação pública deve operar com dados agregados, rastreáveis e metodologicamente classificados.
