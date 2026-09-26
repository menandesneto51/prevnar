# PREVNAR — Metodologia, evidência e indicadores

**Versão:** 2.0-draft  
**Data:** 26/09/2026

## 1. Finalidade

Evitar que observações, estimativas, proxies e dados demonstrativos sejam interpretados como medidas equivalentes.

## 2. Correção conceitual do gap

O cálculo atual soma elegíveis estimados de múltiplas condições e subtrai pessoas vacinadas únicas.

```
gap_aproximado = SUM(elegiveis_condicao) - pessoas_vacinadas_unicas
```

Esse valor não representa necessariamente pessoas únicas não vacinadas, pois uma pessoa pode pertencer simultaneamente a várias condições clínicas.

### Novas entidades

**Oportunidades estimadas**

```
oportunidades_estimadas = SUM(elegiveis_por_condicao)
```

Pode conter sobreposição entre indivíduos.

**Gap por condição**

```
gap_condicao = elegiveis_condicao - vacinados_compativeis_com_condicao
```

Só deve ser calculado quando numerador e denominador possuem definições compatíveis.

**Pessoas elegíveis únicas**

Só é calculável quando houver fonte individual que permita deduplicação válida das condições elegíveis.

**Gap de pessoas únicas**

```
gap_pessoas = pessoas_elegiveis_unicas - pessoas_vacinadas_elegiveis_unicas
```

Exige ambiente autorizado para processamento individual e publicação apenas em forma agregada.

## 3. Níveis de evidência

| Código | Nível | Uso |
|---|---|---|
| E1 | observado_confirmado | medida diretamente observada em fonte compatível com a definição |
| E2 | observado_proxy | variável substituta; não equivale ao conceito clínico |
| E3 | estimado | prevalência, rateio, projeção ou modelagem |
| E4 | manual_validado | carga administrativa versionada e validada |
| E5 | demonstrativo | seed, fixture ou mock; proibido para decisão operacional |

Campos obrigatórios por indicador:

```json
{
  "evidence_level": "E1",
  "source_id": "pni",
  "source_updated_at": "2026-09-01",
  "method_version": "2.0.0",
  "population_definition": "...",
  "numerator_definition": "...",
  "denominator_definition": "...",
  "limitations": [],
  "decision_grade": true
}
```

## 4. Regras para CID e condição clínica

Quando a fonte não contém CID/motivo de indicação:
- não declarar indicação clínica como confirmada;
- classificar mapeamento por grupo de atendimento como **E2 — proxy**;
- não calcular cobertura específica por condição como se fosse observada;
- exibir limitação no painel e no export.

## 5. Denominadores

### Situação 1
Cadastros administrativos específicos. Quando completos, podem permitir cobertura por condição, sujeito à compatibilidade temporal e populacional.

### Situação 2
Estimativas por prevalência × população. Classificar como E3.

### Situação 3
Estimativas nacionais rateadas ou seeds de referência. Classificar como E3 ou E5 conforme origem.

## 6. Compatibilidade temporal

Nenhum indicador deve combinar silenciosamente:
- numerador mensal com denominador de ano diferente;
- população de referência antiga sem identificação;
- fonte atual com regra normativa de vigência incompatível.

O mart deve registrar:
- período do numerador;
- período do denominador;
- data de extração;
- data da fonte;
- data de vigência da regra.

## 7. Freshness

Estados sugeridos:

- **atual**: dentro da janela esperada da fonte;
- **atenção**: atraso superior a uma competência esperada;
- **desatualizado**: atraso suficiente para comprometer decisão;
- **desconhecido**: fonte sem SLA definido.

O limite deve ser configurável por fonte.

## 8. Qualidade mínima para publicação

Um indicador pode ser publicado como decisório somente se:

- schema válido;
- fonte identificada;
- período identificado;
- regra normativa vigente;
- método versionado;
- evidência E1–E4;
- sem erro crítico de consistência;
- freshness dentro do limite;
- limitações expostas.

E5 nunca é decision-grade.

## 9. Inferência causal

Associações ecológicas entre vacinação e SINAN/SIH/SIM/SRAG devem ser descritas como monitoramento populacional. Não utilizar linguagem causal sem desenho e análise adequados.

## 10. Auditoria

Toda alteração em fórmula, população, filtro, fonte ou regra normativa deve gerar:
- incremento de versão metodológica;
- registro de alteração;
- testes;
- reconstrução do mart;
- comparação antes/depois.
