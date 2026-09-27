# PREVNAR — Onboarding de vacinas de rotina, resgate e resposta 2026

**Versão:** 1.0  
**Data:** 26/09/2026

## Escopo

Este documento organiza o onboarding inicial de:

- HPV4;
- meningocócica ACWY;
- febre amarela;
- tríplice viral.

Nesta etapa, as entidades estão em estágios diferentes:

- **MenACWY:** regra nacional de rotina ativa e mapeamento PNI parcial confirmado;
- **Febre amarela:** regra nacional de rotina ativa e código PNI confirmado;
- **Tríplice viral:** regra nacional de rotina ativa; mapeamento parcial para bloqueio/intensificação; dose zero e estratégias territoriais permanecem separadas;
- **HPV4:** regra nacional de rotina ativa para 9–14 anos; código PNI permanece pendente de confirmação nacional inequívoca.

O objetivo é registrar corretamente:
- atos normativos;
- vigência;
- tipo de estratégia;
- contexto territorial;
- limites de interpretação.

## HPV4

Fontes iniciais:
- Calendário Nacional de Vacinação 2026;
- NT nº 32/2026-CGICI/DPNI/SVSA/MS.

A NT nº 32/2026 trata da inclusão de mulheres com NIC 2+ e AIS submetidas a procedimento excisional como grupo prioritário.

Antes de ativar regras:
- separar rotina;
- resgate;
- PrEP;
- grupos prioritários;
- esquema por grupo;
- faixa etária;
- confirmar o código PNI no sistema nacional de registro vacinal;
- vigência específica.

Código SIES/estoque não deve ser reaproveitado como se fosse código PNI.

### Regra nacional ativa — HPV4

A regra `hpv4_routine_2026` estrutura:
- meninas e meninos de 9 anos a 14 anos, 11 meses e 29 dias;
- uma dose para não vacinados;
- histórico desconhecido → verificar antes de recomendar;
- gestação → não vacinar durante a gestação.

O resgate de 15 a 19 anos e os grupos especiais (imunodeprimidos, vítimas de violência sexual, PrEP, PRR e outros grupos previstos em normas específicas) permanecem em regras separadas.

## MenACWY

Fontes iniciais:
- Calendário Nacional de Vacinação 2026;
- NT nº 77/2025-CGICI/DPNI/SVSA/MS;
- NT nº 50/2026-CGICI/DPNI/SVSA/MS.

A NT nº 50/2026 descreve metodologia para avaliação de indicadores da população de 11 a 14 anos por coorte de nascimento.

**Não utilizar a NT nº 50/2026 como se fosse, isoladamente, regra de elegibilidade clínica.**

O PREVNAR separa:
- regra de vacinação;
- cálculo de cobertura;
- coorte de nascimento;
- reforço;
- resgate.

### Regra nacional ativa

A regra `menacwy_routine_2026` cobre:
- reforço infantil preferencialmente aos 12 meses e oportunamente até 4 anos, 11 meses e 29 dias;
- intervalo mínimo de 60 dias após a última dose do esquema básico MenC;
- uma dose ou reforço entre 11 e 14 anos, conforme situação vacinal.

Mapeamento confirmado:
- código PNI 74;
- estratégia 1 — Rotina;
- dose 38 — Reforço para o cenário descrito na NT 77/2025.

## Febre amarela

Fontes iniciais:
- Calendário Nacional de Vacinação 2026;
- NT nº 6/2026-CGICI/DPNI/SVSA/MS.

A NT nº 6/2026 orienta a necessidade de dose padrão para pessoas que receberam dose fracionada na estratégia excepcional de 2018.

### Regra nacional ativa

A regra `febre_amarela_routine_2026` estrutura:
- 9 meses a 4 anos: agenda pediátrica com dose e reforço;
- a partir de 5 anos: decisão por histórico vacinal;
- 5 a 59 anos sem histórico: uma dose padrão;
- dose fracionada 2018 isolada: uma dose padrão de reforço;
- >=60 anos: revisão individual de risco-benefício;
- 6–8 meses: exceção condicionada a avaliação de risco-benefício.

Mapeamento confirmado:
- código PNI 14;
- códigos de dose conhecidos para cobertura: 1, 9 e 36.

A regra de 2018 não é generalizada para outras situações.

## Tríplice viral / sarampo

Fontes iniciais:
- Calendário Nacional de Vacinação 2026;
- NT nº 98/2026-CGICI/DPNI/SVSA/MS;
- NT Conjunta nº 116/2026-DPNI/SVSA/MS.

A NT nº 98/2026 orienta dose zero em crianças.

O PREVNAR deve representar separadamente:
- rotina;
- dose zero;
- bloqueio;
- varredura;
- recomendação para viajantes;
- estratégias territoriais temporárias.

### Regra nacional ativa — Tríplice viral

A regra `triplice_viral_routine_2026` estrutura:
- primeira dose pediátrica aos 12 meses;
- segundo componente aos 15 meses;
- até 29 anos: duas doses por histórico, intervalo mínimo de 30 dias;
- 30 a 59 anos: pelo menos uma dose;
- profissionais de saúde: duas doses independentemente da idade;
- gestação: contraindicação;
- imunossupressão grave: revisão especializada.

A rotina nacional não absorve:
- dose zero;
- bloqueio;
- varredura;
- intensificação;
- regras de viajantes;
- ações territoriais.

### Regra territorial obrigatória

Notas específicas para município/território **não podem** ser convertidas em regra nacional.

Campos futuros obrigatórios:

```json
{
  "geographic_scope": {
    "type": "national|state|municipality|polygon|facility",
    "codes": []
  }
}
```

### Regra temporal obrigatória

Estratégias temporárias devem possuir:

```json
{
  "effective_from": "YYYY-MM-DD",
  "effective_until": "YYYY-MM-DD"
}
```

Quando não houver data final explícita, a regra permanece sob revisão periódica e não deve ser assumida como permanente.

## Próxima etapa

1. mapear códigos oficiais PNI;
2. separar estratégia/rotina/campanha/bloqueio;
3. criar `data_plan`;
4. estruturar regras inequívocas;
5. testar limites de idade e vigência;
6. criar indicadores;
7. manter ações territoriais parametrizadas;
8. passar pelo Release Guardian.


## Modelo de escopo territorial

Todas as regras agora possuem:
- `rule_context`;
- `geographic_scope`;
- vigência.

Ver `docs/RULE_SCOPE_MODEL.md`.

Essa camada é obrigatória antes de ativar:
- bloqueio;
- intensificação;
- campanha;
- resposta municipal/estadual;
- regra de viajantes.


## Estado do mapeamento PNI

### Tríplice viral

Mapeamento parcial oficial incorporado:
- código de imunobiológico: `24`;
- bloqueio: estratégia `3`;
- intensificação: estratégia `4`;
- dose zero em bloqueio: código `57`;
- demais códigos de dose do contexto específico conforme NT de registro.

Este mapeamento **não representa toda a rotina do Calendário 2026**.

### HPV4, MenACWY e febre amarela

Os códigos PNI permanecem vazios neste momento.

Motivo:
- a página federal de Atualização das Regras de Entrada publica a versão 4 em planilha;
- o conteúdo da planilha não está disponível de forma indexável na consulta automatizada realizada nesta etapa;
- o PREVNAR não deve inferir código a partir de tabelas secundárias quando a fonte federal de registro ainda precisa ser lida/validada.

Pendência:
1. obter/ler a planilha oficial vigente;
2. registrar código, estratégia, dose e grupo de atendimento;
3. adicionar teste de regressão;
4. somente então alterar o status para `data_mapping_structured`.
