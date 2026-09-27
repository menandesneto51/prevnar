# PREVNAR — Governança de dados, privacidade e LGPD

**Versão:** 1.0  
**Data:** 26/09/2026

## Princípio

**Mínimo dado necessário, máximo valor epidemiológico possível.**

O PREVNAR prioriza dados agregados. Dados identificáveis ou pseudonimizados só devem ser processados quando necessários à finalidade sanitária e em ambiente institucional autorizado.

## Classificação

| Classe | Exemplo | GitHub público | Painel público |
|---|---|---:|---:|
| público | normas, metadados | sim | sim |
| agregado publicável | indicadores sem risco relevante de reidentificação | sim após validação | sim |
| agregado restrito | small cells / combinações reidentificáveis | não | somente após tratamento |
| pessoal | nome, CPF, CNS | nunca | nunca |
| sensível | diagnóstico, vacinação individual | nunca | nunca |
| segredo | tokens, senhas, chaves | nunca | nunca |

## Ambientes

### DEV
- dados sintéticos, anonimizados ou agregados;
- segredos fora do código;
- `data/raw/` nominal fora do Git;
- logs sem identificadores pessoais.

### HML
- acesso autenticado;
- dados minimizados;
- trilha de auditoria;
- validação funcional e de privacidade.

### PRD
- custódia institucional;
- RBAC;
- autenticação forte;
- segregação de funções;
- backup;
- observabilidade;
- gestão de incidentes.

## Registro de tratamento

Cada dataset deverá possuir:

```yaml
dataset_id:
sistema_origem:
controlador:
operador:
finalidade:
base_legal:
dados_pessoais:
dados_sensiveis:
granularidade:
identificadores:
retencao:
ambiente:
responsavel:
fonte_oficial:
frequencia:
publicacao:
supressao:
riscos:
ripd_requerido:
```

## Base legal

A hipótese legal deve ser identificada **por operação de tratamento** e validada institucionalmente.

Para dados sensíveis, observar especialmente o art. 11 da LGPD. Entre as hipóteses que podem ser pertinentes ao contexto sanitário estão:
- cumprimento de obrigação legal ou regulatória pelo controlador;
- tratamento compartilhado necessário à execução, pela Administração Pública, de políticas públicas previstas em leis ou regulamentos;
- tutela da saúde, em procedimento realizado por profissionais de saúde, serviços de saúde ou autoridade sanitária.

Essas hipóteses **não são selecionadas automaticamente pelo PREVNAR**. A finalidade, necessidade, atores, fluxo e base normativa concreta devem ser documentados.

O consentimento não deve ser adotado por padrão quando a atividade decorre de atribuição legal, política pública ou tutela da saúde.

## Matriz de hipótese legal

| Operação | Dado | Avaliação mínima |
|---|---|---|
| painel público agregado | não pessoal/anônimo efetivo | validar risco de reidentificação |
| processamento institucional de vacinação nominal | sensível | finalidade pública + hipótese do art. 11 + necessidade |
| linkage nominal entre bases | sensível | finalidade específica + minimização + RIPD/risco |
| compartilhamento no escopo do Decreto 12.560/2025 | pessoal/sensível | RIPD prévio + proporcionalidade + direitos do titular |
| uso de IA externa | potencialmente sensível | proibir identificadores por padrão; revisar transferência/operador/finalidade |

## Minimização

Proibido por padrão:
- trazer CPF/CNS quando um identificador técnico pseudônimo resolve;
- enviar dados pessoais/sensíveis para prompts externos;
- publicar microdados de saúde;
- manter cópia nominal fora do ambiente autorizado;
- armazenar segredo em código, JSON versionado ou frontend.

## Small-cell suppression

A política deve ser parametrizável e aprovada institucionalmente.

O pipeline deve:
- identificar células pequenas;
- avaliar reidentificação por combinação ou diferença;
- suprimir/agrupá-las quando necessário;
- registrar o motivo da supressão.

## RIPD

Abrir avaliação para RIPD quando houver, entre outros:
- grande volume de dados sensíveis;
- cruzamento nominal de múltiplas bases;
- perfilização de indivíduos;
- IA sobre dados pessoais/sensíveis;
- novo compartilhamento institucional;
- alto risco de reidentificação;
- operação abrangida por exigência normativa específica.

## Agentes de IA

Agentes PREVNAR:
- não recebem identificadores sem necessidade;
- não geram decisão clínica individual;
- não alteram dado-fonte;
- distinguem fato, inferência e recomendação;
- registram fonte e versão metodológica;
- não publicam externamente sem gate de validação.

## Incidentes

O PREVNAR deverá registrar:
- detecção;
- contenção;
- escopo;
- tipos de dados;
- titulares potencialmente afetados;
- avaliação de risco/dano;
- decisão de comunicação;
- medidas corretivas.

Seguir LGPD, Resolução CD/ANPD nº 15/2024 e normas estaduais aplicáveis.

## Referências
- LGPD: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm
- ANPD Poder Público: https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes/guia_orientativo_tratamento_de_dados_pessoais_pelo_poder_publico
- Decreto Federal nº 12.560/2025: https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/decreto/d12560.htm
- Decreto MT nº 1.427/2025: https://iomat.mt.gov.br/apifront/portal/edicoes/imprimir_materia/1702926/18430?find=1.427


## Ciclo de vida do dado

Cada fluxo deve declarar:
1. coleta/extração;
2. uso;
3. acesso;
4. compartilhamento;
5. publicação;
6. retenção;
7. descarte.

Retenção não deve ser indefinida por padrão. Dados brutos nominais devem permanecer apenas pelo período necessário à finalidade e às obrigações institucionais aplicáveis.

## Compartilhamento e Decreto nº 12.560/2025

Para compartilhamentos abrangidos pelo Decreto nº 12.560/2025:
- observar LGPD;
- demonstrar proporcionalidade e necessidade;
- garantir direitos dos titulares;
- realizar RIPD prévio nos termos do Decreto;
- documentar controlador, destinatários, finalidade, categorias de dados e salvaguardas.

## Atualização ANPD

A página institucional da ANPD sobre RIPD foi atualizada em setembro de 2026 e reforça que o relatório descreve tratamentos que possam gerar alto risco às liberdades civis e aos direitos fundamentais. O PREVNAR deve acompanhar futuras regulamentações adicionais sobre alto risco.
