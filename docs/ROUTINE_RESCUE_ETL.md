# PREVNAR — ETL de rotina e resgate

## Escopo inicial

Produtos com código PNI confirmado:
- MenACWY — 74;
- febre amarela — 14;
- tríplice viral — 24.

HPV4 permanece bloqueado até confirmação inequívoca do código PNI.

## Execução

```bash
python etl/routine_rescue_etl.py
```

Desenvolvimento:

```bash
python etl/routine_rescue_etl.py --max-pages 20
```

## Saídas

- `data/mart/mart_routine_menacwy.json`;
- `data/mart/mart_routine_febre_amarela.json`;
- `data/mart/mart_routine_triplice_viral.json`;
- `data/mart/routine_rescue_dashboard.json`;
- cópia pública em `web/public/data/routine_rescue_dashboard.json`.

## Regras de classificação

### MenACWY

Total observado:
- todo registro válido com código 74.

Contexto confirmado:
- estratégia 1 + dose 38 = rotina/reforço conhecido.

A contagem de contexto é feita linha a linha.

### Febre amarela

Total observado:
- todo registro válido com código 14.

Códigos de dose conhecidos:
- 1;
- 9;
- 36.

Registros com outros códigos continuam no total observado, mas ficam separados como `unknown_dose_records`.

### Tríplice viral

Total observado:
- todo registro válido com código 24.

Bloqueio confirmado:
- estratégia 3;
- dose 1, 2, 8 ou 57.

Intensificação confirmada:
- estratégia 4;
- dose 1 ou 2.

As contagens são feitas linha a linha.

## Privacidade

O identificador individual é usado somente em memória para deduplicação e não é persistido.

## Limites

O ETL não transforma:
- dose observada em cobertura;
- registro em pessoa elegível;
- bloqueio/intensificação em rotina;
- histórico desconhecido em ausência de vacinação.

Cobertura, oportunidade e atualização do esquema exigem denominador/histórico compatível.

## HPV4

O ETL retorna explicitamente:

`blocked_pending_official_code`

Nenhum código SIES/estoque deve ser usado como substituto de código PNI.
