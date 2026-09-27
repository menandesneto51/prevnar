# PREVNAR — Cobertura MenACWY por coorte

## Base metodológica

A implementação segue a Nota Técnica nº 50/2026-CGICI/DPNI/SVSA/MS.

O Ministério da Saúde orienta:
- numerador com pessoas vacinadas entre 11 e 14 anos, a partir de 2020;
- pelo menos uma dose MenACWY por indivíduo;
- dados nominais RNDS;
- acompanhamento da mesma coorte ao longo dos anos;
- denominador do Censo Demográfico 2022 por idade simples;
- apresentação por idade e pela faixa 11–14 anos.

## Exemplo

Para a coorte que possui 14 anos em 2026:

- 11 anos em 2023;
- 12 anos em 2024;
- 13 anos em 2025;
- 14 anos em 2026.

O numerador é a união de pessoas únicas com pelo menos um registro MenACWY nesses pontos da trajetória.

## Denominador

Arquivo normalizado esperado:

`data/manual/denominators/censo2022_age_simple.csv`

Schema:

```text
geography_type
geography_code
age
population
census_year
```

A cobertura fica indisponível se o denominador não estiver carregado.

Não existe fallback para população total, projeção genérica ou rateio.

## Saída

`data/mart/mart_menacwy_cohort_coverage.json`

## Limitações

A própria metodologia oficial reconhece:
- não exclusão exata de pessoas que foram a óbito;
- impossibilidade de considerar exatamente a migração.

O PREVNAR também sinaliza possível sobreposição entre coortes quando um mesmo identificador aparece de forma inconsistente em mais de uma coorte derivada.

## Evidência

Quando:
- numerador nominal está disponível;
- denominador Censo 2022 normalizado está completo;

a cobertura calculada pode ser classificada como decision-grade para a metodologia específica da NT 50/2026.

Na ausência de qualquer uma dessas condições, a cobertura permanece indisponível.


## Extração automática do Censo 2022

Quando o arquivo normalizado não existe, o pipeline consulta a tabela SIDRA 9606 com:
- sexo = total;
- cor/raça = total;
- 11 anos = categoria 6568;
- 12 anos = categoria 6569;
- 13 anos = categoria 6570;
- 14 anos = categoria 6571;
- níveis BR, UF e Município.

A conexão mantém validação TLS ativa. Em rede institucional com inspeção TLS, utilizar `PREVNAR_CA_BUNDLE`.

Após a extração, o arquivo é normalizado em:
`data/manual/denominators/censo2022_age_simple.csv`.
