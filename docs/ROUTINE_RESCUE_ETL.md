# PREVNAR — ETL de rotina, resgate e resposta

## Módulo

`etl/routine_rescue_etl.py`

## Escopo

Nesta versão o ETL coleta:

- MenACWY;
- febre amarela;
- tríplice viral.

HPV4 permanece **não coletado**, embora o código nacional `67` já esteja confirmado, porque estratégia/dose/grupos da regra de entrada vigente ainda estão incompletos no registry.

## Princípio central

O ETL separa:

- `observed_code_hits`: todos os registros cujo código de imunobiológico corresponde;
- `confirmed_context_doses`: somente registros cuja combinação estratégia/dose está explicitamente mapeada nesta versão.

Isso impede que um código correto, porém em contexto ainda não estruturado, seja tratado como indicador decisório.

## MenACWY

Contexto confirmado atual:

- imunobiológico `74`;
- estratégia `1`;
- dose `38`;
- interpretação: reforço de rotina documentado.

Outros registros de código 74 permanecem observados, mas entram como `code_hit_outside_confirmed_context`.

## Febre amarela

Código:

- `14`.

Códigos de dose conhecidos para cobertura nesta etapa:

- `1`;
- `9`;
- `36`.

A aceitação desses códigos para agregação não substitui a avaliação clínica por idade/histórico.

## Tríplice viral

Código:

- `24`.

Contextos confirmados:

### Bloqueio
- estratégia `3`;
- doses `1,2,8,57`.

### Intensificação
- estratégia `4`;
- doses `1,2`.

Rotina nacional permanece governada pelo motor normativo e não é inferida a partir desses contextos parciais.

## Privacidade

O identificador individual é utilizado somente em memória para deduplicação.

Não é persistido em:
- marts;
- manifests;
- logs;
- frontend.

## Saídas

- `data/mart/mart_menacwy.json`;
- `data/mart/mart_febre_amarela.json`;
- `data/mart/mart_triplice_viral.json`;
- `data/mart/routine_rescue_dashboard.json`.

O dashboard também é copiado para `web/public/data` para compatibilidade com export estático.

## Execução

```bash
python etl/routine_rescue_etl.py
```

Para desenvolvimento:

```bash
python etl/routine_rescue_etl.py --max-pages 20
```

## Próxima etapa

- validar estratégia/dose/grupos HPV4;
- ampliar contextos MenACWY/VFA/SCR apenas quando houver fonte oficial;
- criar frontend específico;
- adicionar denominadores compatíveis;
- integrar indicadores ao catálogo principal;
- executar Release Guardian.
