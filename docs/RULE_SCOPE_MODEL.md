# PREVNAR — Escopo territorial e temporal de regras

## Objetivo

Impedir que regras de campanha, bloqueio, intensificação ou resposta local sejam aplicadas como regra nacional.

## Campos obrigatórios

Toda regra normativa possui:

```json
{
  "rule_context": "routine | special_population | maternal | passive_immunization | monitoring | campaign | blockade | intensification | travel | rescue | onboarding",
  "geographic_scope": {
    "type": "national | state | municipality | polygon | facility",
    "codes": []
  },
  "effective_from": "YYYY-MM-DD",
  "effective_until": null
}
```

## Escopo nacional

Usar:

```json
"geographic_scope": {
  "type": "national",
  "codes": ["BR"]
}
```

## Regras territoriais

Para estados e municípios, usar códigos oficiais:

```json
"geographic_scope": {
  "type": "municipality",
  "codes": ["3550308", "3518800"]
}
```

Para polígonos de bloqueio em torno de caso suspeito/confirmado, a regra não deve inventar uma lista fixa de municípios. O escopo deve ser resolvido operacionalmente a partir do evento/território e manter referência ao ato normativo.

## Vigência

Ações temporárias devem preferir `effective_until`.

Quando a norma não define encerramento:
- manter revisão periódica;
- não presumir permanência;
- registrar condição de desativação quando conhecida.

## Sarampo

O modelo deve separar:
- rotina;
- dose zero;
- bloqueio;
- varredura;
- intensificação;
- vacinação de viajantes;
- ações municipais/regionais.

Uma nota para São Paulo, Guarulhos, Santo André ou qualquer outro território não pode alterar a regra nacional de rotina.

## Release Guardian

O validador considera erro:
- regra sem `rule_context`;
- regra sem `geographic_scope`;
- tipo de escopo inválido;
- escopo não nacional sem códigos/território;
- regra nacional com códigos diferentes de `BR`.

## Cursor

Ao criar nova regra territorial:
1. localizar ato oficial;
2. registrar no legal register;
3. definir contexto;
4. definir território;
5. definir vigência;
6. adicionar teste de escopo;
7. somente então considerar ativação.
