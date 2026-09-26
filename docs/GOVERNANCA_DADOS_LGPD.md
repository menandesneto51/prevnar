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

A hipótese legal deve ser identificada por operação de tratamento e validada institucionalmente.

Para dados sensíveis, observar especialmente art. 11 da LGPD e regras próprias do Poder Público. O consentimento não deve ser selecionado automaticamente quando a atividade decorre de obrigação legal, execução de política pública ou tutela da saúde.

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
