# PREVNAR — Governança legal e regulatória

**Versão:** 1.0  
**Data de referência:** 26/09/2026  
**Escopo:** inteligência vacinal, imunização, vigilância em saúde, dados de saúde, interoperabilidade, privacidade e segurança.

> Documento técnico-regulatório para orientar desenvolvimento e governança. Não substitui manifestação jurídica da SES/MT, PGE/MT, encarregado de dados, Comitê Setorial de Proteção de Dados ou demais instâncias competentes.

## 1. Fundamentos sanitários

| Norma | Relação com o PREVNAR |
|---|---|
| Constituição Federal, art. 196 | Fundamenta políticas destinadas à redução do risco de doença e ao acesso universal e igualitário às ações e serviços de saúde. |
| Lei nº 6.259/1975 | Organiza as ações de vigilância epidemiológica e o Programa Nacional de Imunizações (PNI). |
| Decreto nº 78.231/1976 | Regulamenta a Lei nº 6.259/1975. |
| Lei nº 8.080/1990 | Organiza o SUS e, no art. 47, determina sistema nacional de informações em saúde integrado, incluindo informações epidemiológicas. |
| Decreto nº 7.508/2011 | Regulamenta a Lei nº 8.080/1990 e reforça organização regionalizada, planejamento e articulação interfederativa. |

### Fontes oficiais
- Lei nº 6.259/1975: https://planalto.gov.br/ccivil_03/leis/l6259.htm
- Lei nº 8.080/1990: https://www.planalto.gov.br/ccivil_03/leis/l8080.htm

## 2. PNI e regras de imunização

O PREVNAR deve tratar atos do Ministério da Saúde/PNI como fonte normativa primária para:
- população elegível;
- esquema e número de doses;
- intervalos;
- transição entre vacinas;
- situações especiais;
- registro;
- monitoramento;
- segurança da vacinação.

### VPC20

**Nota Técnica nº 52/2026-CGICI/DPNI/SVSA/MS**  
Define diretrizes para uso da VPC20 em estratégias especiais no SUS, no âmbito da RIE, e orienta transição dos esquemas previamente utilizados com VPC10, VPC13 e VPP23.

Fonte: https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/notas-tecnicas/2026/nota-tecnica-no-52-2026-cgici-dpni-svsa-ms.pdf/view

**Nota Técnica Conjunta nº 310/2026-DPNI/SVSA-DESF/SAPS/MS**  
Amplia o uso da VPC20 no SUS para pessoas a partir de 85 anos.

Fonte: https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/notas-tecnicas/2026/nota-tecnica-conjunta-no-310-2026.pdf/view

### Regra obrigatória de versionamento clínico

Nenhuma regra clínica deve existir somente hard-coded. Toda regra deverá registrar:

```yaml
rule_id:
vaccine_id:
normative_act:
issuer:
publication_date:
effective_from:
effective_until:
population:
eligibility_logic:
schedule:
exceptions:
official_url:
method_version:
validated_by:
validated_at:
```

Uma nova norma não entra automaticamente em produção. Exige validação epidemiológica e institucional.

## 3. Saúde digital e interoperabilidade

### Portaria nº 1.434/2020
Instituiu o Programa Conecte SUS, a RNDS e a adoção de padrões de interoperabilidade em saúde.

Fonte: https://bvsms.saude.gov.br/bvs/saudelegis/gm/2020/prt1434_01_06_2020_rep.html

### Portaria GM/MS nº 3.232/2024
Instituiu o Programa SUS Digital, abrangendo atenção, vigilância, gestão, planejamento, monitoramento, avaliação, pesquisa, desenvolvimento e inovação em saúde.

Fonte: https://bvsms.saude.gov.br/bvs/saudelegis/gm/2024/prt3232_04_03_2024.html

### Decreto Federal nº 12.560/2025
Dispõe sobre RNDS e Plataformas SUS Digital e regulamenta os arts. 47 e 47-A da Lei nº 8.080/1990.

Requisitos relevantes:
- compartilhamento e tratamento devem observar a LGPD;
- proporcionalidade e necessidade;
- direitos dos titulares;
- avaliação de impacto à proteção de dados nos compartilhamentos abrangidos pelo Decreto.

Fonte: https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/decreto/d12560.htm

## 4. LGPD e dados de saúde

A Lei nº 13.709/2018 classifica dados referentes à saúde como dados pessoais sensíveis.

O PREVNAR deve observar:
- finalidade;
- adequação;
- necessidade;
- qualidade;
- segurança;
- prevenção;
- não discriminação;
- responsabilização e prestação de contas.

No Poder Público, a hipótese legal deve ser identificada para cada operação de tratamento. Não utilizar consentimento como fundamento automático quando a operação decorre de atribuição legal, execução de política pública ou tutela da saúde.

Fontes:
- LGPD: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm
- Guia ANPD — Poder Público: https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes/guia_orientativo_tratamento_de_dados_pessoais_pelo_poder_publico

## 5. Incidentes de segurança

A Resolução CD/ANPD nº 15/2024 regulamenta a comunicação de incidentes de segurança. Quando o incidente puder acarretar risco ou dano relevante, o controlador deve observar os fluxos e prazos regulamentares.

Fonte: https://www.gov.br/anpd/pt-br/canais_atendimento/agente-de-tratamento/comunicado-de-incidente-de-seguranca-cis

## 6. Mato Grosso

### Decreto Estadual nº 1.427, de 30/04/2025
Regulamenta a proteção de dados pessoais no Poder Executivo do Estado de Mato Grosso.

Implicações para o PREVNAR:
- integração à governança institucional de proteção de dados;
- identificação de encarregado e Comitê Setorial;
- inventário dos tratamentos;
- avaliação de riscos;
- RIPD para atividades classificadas como de alto risco;
- controles de privacidade desde a concepção.

Fonte oficial IOMAT: https://iomat.mt.gov.br/apifront/portal/edicoes/imprimir_materia/1702926/18430?find=1.427

### Decreto Estadual nº 1.428, de 30/04/2025
Institui a Política de Segurança da Informação do Poder Executivo de Mato Grosso.

Requisitos a refletir no sistema:
- disponibilidade;
- integridade;
- confidencialidade;
- autenticidade;
- gestão de riscos;
- controles de acesso;
- continuidade;
- resposta a incidentes.

Fonte oficial: https://www.pm.mt.gov.br/documents/5342163/17318310/Decreto%2Bn%C2%BA%2B1.428%2Bde%2B30%2Bde%2Babril%2Bde%2B2025.pdf/19bc1943-b037-b6d9-272c-b6f496bcda68?t=1758220168706

## 7. Gate legal para novas fontes

Nenhuma nova fonte entra no pipeline institucional sem:

1. finalidade;
2. responsável institucional;
3. base normativa;
4. hipótese legal LGPD, quando aplicável;
5. classificação do dado;
6. granularidade necessária;
7. política de acesso;
8. regra de retenção;
9. avaliação de compartilhamento;
10. necessidade de RIPD;
11. controles de segurança;
12. regra de publicação;
13. proveniência;
14. plano de incidente;
15. aprovação institucional quando exigida.

## 8. Hierarquia operacional

Em divergência, prevalece:

1. legislação vigente;
2. atos normativos vigentes do Ministério da Saúde/PNI;
3. normas estaduais aplicáveis;
4. manuais oficiais vigentes;
5. documentação técnica do PREVNAR;
6. regras implementadas no código.

O código nunca prevalece sobre norma vigente.
