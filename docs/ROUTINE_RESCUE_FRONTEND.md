# PREVNAR — Frontend de rotina, resgate e resposta

## Rota

`/rotina-resgate`

## Escopo

O painel apresenta:

- MenACWY;
- febre amarela;
- tríplice viral;
- HPV4 como mapeamento parcial.

## Regra visual principal

A interface separa explicitamente:

### Registros observados

Todo registro em que o código nacional do imunobiológico corresponde.

Isso responde:

> "Quantos registros com esse código existem na fonte?"

Não significa automaticamente:
- dose válida para a regra analisada;
- elegibilidade;
- cobertura;
- oportunidade;
- esquema completo.

### Contextos confirmados

Registros cuja combinação de estratégia/dose já foi explicitamente mapeada e validada na versão atual.

Isso responde:

> "Quantos registros pertencem aos contextos que o PREVNAR sabe interpretar com segurança nesta versão?"

## MenACWY

Mostra:
- código 74 observado;
- contexto confirmado de reforço estratégia 1 / dose 38;
- distribuição territorial;
- mismatches;
- freshness/proveniência.

## Febre amarela

Mostra:
- código 14 observado;
- doses de cobertura conhecidas 1/9/36 como contextos confirmados;
- distribuição territorial;
- mismatches;
- freshness/proveniência.

O painel não converte isso automaticamente em esquema completo por histórico.

## Tríplice viral

Mostra:
- código 24 observado;
- bloqueio estratégia 3;
- intensificação estratégia 4;
- contextos/doses já mapeados;
- distribuição territorial;
- mismatches;
- freshness/proveniência.

Rotina, dose zero, bloqueio e intensificação permanecem conceitualmente separados.

## HPV4

O código nacional 67 está confirmado.

O frontend, porém, mantém HPV4 como:
- mapeamento parcial;
- sem ETL decisório;
- sem KPIs de doses confirmadas.

Motivo:
- estratégia;
- dose;
- grupos de atendimento

ainda dependem da consolidação da regra de entrada vigente.

## Estado sem carga

Se `routine_rescue_dashboard.json` ainda não existir, a rota continua buildando e apresenta instrução explícita:

```bash
python etl/routine_rescue_etl.py
```

## Static export

O ETL publica:

`web/public/data/routine_rescue_dashboard.json`

permitindo uso no GitHub Pages.

## Guardrail

Nenhum card deve rotular `observed_code_hits` ou `confirmed_context_doses` como cobertura populacional sem um denominador compatível e um indicador metodologicamente aprovado.
