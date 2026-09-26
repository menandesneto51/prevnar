# PREVNAR — Registro de vacinas e motor normativo

**Versão:** 1.0  
**Data:** 26/09/2026

## Objetivo

Separar regra clínica/normativa da implementação de software.

O PREVNAR passa a utilizar três registros complementares:

1. `data/reference/vaccine_registry.json` — identidade da vacina, códigos PNI e metadados operacionais;
2. `data/reference/normative_rules.json` — elegibilidade, esquema, transição e vigência;
3. `docs/legal_register.json` — ato normativo oficial e URL de origem.

O código não deve reproduzir uma regra vacinal sem referência a esses registros.

## Fonte canônica

### vaccine_registry.json

Campos principais:

```json
{
  "vaccine_id": "vpc20",
  "pni_codes": ["107"],
  "normative_acts": ["..."],
  "pni_registration": {},
  "monitoring": {}
}
```

### normative_rules.json

Cada regra deve possuir:

- `rule_id`;
- `vaccine_id`;
- `rule_type`;
- `status`;
- `effective_from`;
- `effective_until`;
- `normative_acts`;
- população;
- esquema ou metodologia;
- exceções;
- histórico vacinal quando aplicável.

## Vigência

O motor `etl/vaccine_rules.py` só retorna regras ativas cuja vigência inclua a data avaliada.

Uma norma nova não deve sobrescrever silenciosamente a regra anterior. O fluxo é:

1. registrar o novo ato;
2. encerrar a vigência anterior quando necessário;
3. criar ou versionar a regra;
4. testar a transição;
5. reconstruir os marts afetados.

## VPC20 — regras estruturadas iniciais

### RIE

Base normativa:
- Nota Técnica nº 52/2026-CGICI/DPNI/SVSA/MS;
- Nota Técnica nº 64/2026-DPNI/SVSA/MS, que atualiza a NT 52/2026.

O motor estrutura:
- indicação a partir de 2 meses nas condições cadastradas;
- esquemas por faixa etária;
- dose única a partir de 5 anos no caminho genérico;
- exceção estruturada para TCTH;
- CAR-T como `requires_review` enquanto não houver regra detalhada validada no registro;
- regras de transição quando o histórico estiver explicitamente configurado.

### Pessoas a partir de 85 anos

Base:
- Nota Técnica Conjunta nº 310/2026-DPNI/SVSA-DESF/SAPS/MS.

O motor estrutura o caminho conforme idade e histórico pneumocócico, mantendo `requires_review` quando o histórico for desconhecido ou não estiver contemplado.

A meta de cobertura e os parâmetros populacionais da norma são metadados de monitoramento, não regra de elegibilidade individual.

### Cobertura

A Nota Técnica nº 69/2026-CGICI/DPNI/SVSA/MS é registrada como regra do tipo `monitoring_methodology`, separada das regras clínicas.

## Regra de segurança

O motor é de **suporte operacional e de vigilância**.

Ele:
- não prescreve;
- não substitui avaliação clínica;
- não resolve conflitos clínicos complexos por suposição;
- retorna `requires_review` quando a informação estruturada é insuficiente;
- registra o `rule_id` que sustentou o resultado.

## API Python

```python
from datetime import date
from vaccine_rules import evaluate_operational

result = evaluate_operational(
    "vpc20",
    age_months=90 * 12,
    condition_ids=[],
    pneumococcal_history="one_vpp23",
    on_date=date(2026, 9, 26),
)
```

## Integridade

`validate_registry_integrity()` verifica:
- vacina existente;
- `rule_id` único;
- referências a atos normativos existentes;
- atos normativos das vacinas existentes.

O Release Guardian transforma falhas de referência em erro bloqueante.

## Compatibilidade

`data/reference/vacinas_pni.json` é legado.

Novas implementações devem utilizar:
- `vaccine_registry.json`;
- `normative_rules.json`;
- `vaccine_rules.py`.

O arquivo legado só deve ser removido quando nenhum pipeline restante depender dele.

## Inclusão de nova vacina

Checklist mínimo:

1. cadastrar `vaccine_id`;
2. cadastrar códigos oficiais da fonte;
3. registrar os atos normativos;
4. criar regras com vigência;
5. estruturar população-alvo;
6. estruturar esquema apenas quando inequivocamente suportado;
7. marcar exceções como revisão;
8. criar testes;
9. integrar ao ETL;
10. passar pelo Release Guardian.
