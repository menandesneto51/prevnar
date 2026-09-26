# PREVNAR — Onboarding de novo imunobiológico

## Objetivo

Permitir a inclusão de uma nova vacina sem criar um novo sistema e sem duplicar regras em código.

## Gate 0 — Evidência e norma

Antes de qualquer implementação:

- [ ] identificar o ato normativo oficial vigente;
- [ ] registrar o ato em `docs/legal_register.json`;
- [ ] registrar data de publicação e vigência;
- [ ] identificar se o ato substitui/atualiza norma anterior;
- [ ] identificar população-alvo;
- [ ] identificar esquema, intervalos e exceções;
- [ ] identificar códigos da fonte PNI/OpenDataSUS;
- [ ] distinguir regra clínica de metodologia de monitoramento;
- [ ] definir o que **não pode ser automatizado**.

## Gate 1 — Registry

Adicionar a vacina em:

`data/reference/vaccine_registry.json`

Mínimo:

```json
{
  "vaccine_id": "id_estavel",
  "name": "Nome completo",
  "display": "SIGLA",
  "pni_codes": [],
  "active": true,
  "monitored": true,
  "normative_acts": []
}
```

Não reutilizar `vaccine_id` para vacina diferente.

## Gate 2 — Regras normativas

Adicionar uma ou mais regras em:

`data/reference/normative_rules.json`

Separar, quando necessário:

- elegibilidade;
- esquema;
- transição;
- resgate;
- reforço;
- grupos especiais;
- campanha;
- metodologia de cobertura/monitoramento.

Uma única regra gigante deve ser evitada quando houver vigências ou finalidades diferentes.

## Gate 3 — Incerteza

Quando a norma não estiver suficientemente estruturada para uma decisão automática:

```json
{
  "requires_review": true
}
```

O PREVNAR deve ser conservador. A ausência de regra não autoriza inferência clínica.

## Gate 4 — Dados

Registrar as fontes em `source_registry.json` quando novas fontes forem necessárias.

Definir:

- source_id;
- período de referência;
- grain;
- freshness;
- evidence_level;
- proveniência;
- schema;
- limitações.

## Gate 5 — Indicadores

Todo novo indicador precisa:

- `id`;
- nome;
- definição;
- fórmula;
- numerador;
- denominador;
- período;
- população;
- evidence_level;
- decision_grade;
- limitações.

Não criar "cobertura" se numerador e denominador não forem compatíveis.

## Gate 6 — Testes

Testar, no mínimo:

1. vigência antes/depois da norma;
2. limite etário inferior;
3. limite etário superior quando existir;
4. cada exceção;
5. histórico vacinal;
6. esquema;
7. situação não reconhecida → revisão;
8. integridade das referências legais;
9. ausência de E5 como decision-grade.

## Gate 7 — Interface

A interface deve exibir:

- vacina;
- regra vigente;
- evidência;
- período;
- fonte;
- limitações;
- `requires_review` quando aplicável.

## Gate 8 — Cursor e agentes

Fluxo obrigatório:

```
Legal & Privacy Agent
→ Epidemiology Agent
→ Data Agent
→ Data Quality Agent
→ Intelligence Agent
→ Action Agent
→ Release Guardian
```

### Legal & Privacy Agent
Confere norma, vigência, LGPD e governança.

### Epidemiology Agent
Confere definição clínica/epidemiológica e compatibilidade dos indicadores.

### Data Agent
Integra os códigos e fontes.

### Data Quality Agent
Valida qualidade e freshness.

### Release Guardian
Bloqueia inconsistências estruturais antes da publicação.

## Gate 9 — Release

Executar:

```bash
python -m pytest tests -q
python etl/release_guardian.py --mode release
```

Em deploy server-side:

```bash
PREVNAR_SERVER_SIDE_DEPLOY=1 python etl/release_guardian.py --mode release
```

## Definition of Done

Um imunobiológico está integrado quando:

- norma versionada;
- registry completo;
- regras estruturadas;
- fontes rastreáveis;
- indicadores definidos;
- testes passando;
- documentação pronta;
- limites expostos;
- CI aprovado;
- Release Guardian aprovado.
