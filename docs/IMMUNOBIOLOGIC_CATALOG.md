# PREVNAR — Catálogo de imunobiológicos

## Finalidade

A rota `/imunobiologicos` apresenta o estado de cada imunobiológico em três dimensões independentes:

1. **Regra normativa**
   - active;
   - draft;
   - ausente.

2. **Mapeamento de dados**
   - mapped;
   - partial;
   - pending.

3. **Monitoramento**
   - sim;
   - não.

## Por que não existe um status único

Uma vacina pode:
- ter regra nacional ativa, mas ainda não possuir coleta automatizada;
- ter código PNI confirmado, mas regra clínica ainda em draft;
- estar monitorada em dados observados sem possuir denominador suficiente para cobertura decisória.

O PREVNAR evita condensar essas situações em um único selo de "pronto".

## Fonte

O catálogo é derivado em tempo de build de:

- `data/reference/immunobiologic_registry.json`;
- `data/reference/normative_rules.json`.

A interface não mantém uma cópia própria da configuração.

## Conteúdo exibido

Por imunobiológico:
- id canônico;
- tipo;
- nome;
- códigos PNI;
- onboarding_status;
- monitored;
- número de regras ativas;
- número de drafts;
- contexto das regras ativas;
- escopo territorial;
- vigência.

## Uso pelos agentes

### Legal & Privacy Agent
Confere atos, vigência e escopo.

### Epidemiology Agent
Confere se a regra ativa é adequada ao contexto.

### Data Agent
Confere código PNI e status de mapeamento.

### Data Quality Agent
Confere se `monitored=true` possui fonte/proveniência válida.

### Release Guardian
Mantém a validação estrutural das referências.

## Interpretação

`data_mapping=mapped` não significa automaticamente:
- cobertura válida;
- denominador deduplicado;
- decision-grade;
- recomendação clínica completa.

Essas dimensões continuam sendo controladas pelos respectivos catálogos e gates.


## Escopo das regras no catálogo

O catálogo exibe o `geographic_scope` de cada regra ativa.

Isso significa que:
- uma regra municipal continua identificada como municipal;
- uma regra estadual não é resumida como regra nacional;
- uma regra por polígono/facility mantém esse contexto;
- a existência de uma regra territorial ativa não implica que ela se aplique fora do território.

O catálogo descreve **maturidade e existência da regra**. A resolução de aplicabilidade para uma pessoa/território é responsabilidade do motor normativo com `geographic_context`.


## Relação entre regra e dados

O catálogo deve tornar visíveis situações como:

- regra ativa + dados pendentes — exemplo de maturidade clínica maior que maturidade de ingestão;
- regra ativa + mapeamento parcial — indicador observado possível, mas cobertura completa ainda não garantida;
- regra draft + dados conhecidos — existência de código não autoriza ativação clínica;
- regra territorial ativa — maturidade da regra não altera seu `geographic_scope`.

Essas combinações são intencionais e impedem que "código conhecido" seja interpretado como "produto pronto para decisão".
