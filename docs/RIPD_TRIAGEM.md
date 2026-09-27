# PREVNAR — Pré-triagem de RIPD

**Objetivo:** apoiar a decisão institucional sobre elaboração/atualização de Relatório de Impacto à Proteção de Dados Pessoais (RIPD).

> A triagem não substitui decisão do controlador, encarregado, Comitê Setorial de Proteção de Dados ou instância jurídica competente.

## Identificação

- Projeto/feature:
- Responsável:
- Data:
- Ambiente:
- Sistemas/fontes envolvidos:
- Finalidade pública:
- Base normativa:
- Hipótese legal proposta:

## Perguntas de triagem

Marcar **sim/não/não se aplica**.

1. Há dados pessoais?
2. Há dados pessoais sensíveis de saúde?
3. Há grande volume de registros?
4. Há cruzamento entre duas ou mais bases individualizadas?
5. Há pseudonimização reversível?
6. Há compartilhamento com outro órgão ou entidade?
7. Há novo fluxo envolvendo RNDS/Plataformas SUS Digital?
8. Há uso de IA/modelo sobre dados pessoais?
9. Há perfilização, classificação ou priorização de indivíduos?
10. Há possibilidade de efeito relevante sobre direitos/interesses do titular?
11. Há dados de crianças/adolescentes?
12. Há células pequenas ou risco de reidentificação?
13. Há transferência internacional ou uso de serviço externo?
14. Há alteração importante de finalidade?
15. Há tecnologia ou tratamento novo com risco ainda não avaliado?

## Resultado preliminar

**Abrir avaliação formal de RIPD** quando houver exigência normativa expressa ou combinação de fatores de alto risco.

Para compartilhamentos abrangidos pelo Decreto Federal nº 12.560/2025, o compartilhamento deve ser precedido de RIPD conforme o Decreto.

## Gatilhos de abertura obrigatória ou fortemente recomendada

### Obrigatória pelo fluxo normativo identificado
- compartilhamento de dados pessoais abrangido pelo Decreto Federal nº 12.560/2025.

### Fortemente recomendada para decisão institucional
- linkage nominal de múltiplas bases de saúde;
- grande volume de dados sensíveis;
- uso de IA/modelos sobre dados pessoais ou pseudonimizados;
- priorização/classificação de indivíduos com potencial efeito relevante;
- nova API nominal;
- novo compartilhamento interinstitucional;
- uso de serviço externo/cloud não previamente avaliado;
- tratamento envolvendo crianças/adolescentes em escala;
- dados geográficos muito granulares combinados com condições clínicas;
- mudança substancial de finalidade;
- nova tecnologia de identificação ou vinculação.

A classificação final deve ser realizada pelo controlador/encarregado/Comitê Setorial competente.

No Executivo de Mato Grosso, seguir também o Decreto nº 1.427/2025 e o fluxo institucional do Comitê Setorial de Proteção de Dados.

## Conteúdo mínimo a encaminhar

- descrição do tratamento;
- finalidade;
- necessidade/proporcionalidade;
- categorias de titulares;
- categorias de dados;
- origem;
- compartilhamentos;
- retenção;
- acessos;
- riscos aos direitos/liberdades;
- medidas de mitigação;
- segurança;
- governança;
- responsável;
- revisão periódica.

## Referências

- Decreto Federal nº 12.560/2025
- Lei nº 13.709/2018
- Guia ANPD para tratamento de dados pelo Poder Público
- Decreto MT nº 1.427/2025


## Decisão documentada

A triagem deve terminar com um dos estados:

```text
RIPD_REQUIRED
RIPD_RECOMMENDED
RIPD_NOT_REQUIRED_WITH_JUSTIFICATION
PENDING_PRIVACY_REVIEW
```

Registrar:
- decisor institucional;
- data;
- justificativa;
- controles exigidos;
- prazo de revisão;
- link/identificador do RIPD quando elaborado.

## Evidências técnicas anexáveis

O PREVNAR pode fornecer ao processo institucional:
- data flow;
- source registry;
- campos utilizados;
- manifests;
- matriz de acesso;
- retenção;
- small-cell policy;
- logs de processamento;
- relatório do Release Guardian;
- análise de riscos;
- diagrama DEV/HML/PRD.

Esses artefatos apoiam o RIPD, mas não o substituem.
