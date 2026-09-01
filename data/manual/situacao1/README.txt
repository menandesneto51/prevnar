Coloque um CSV por condição Situação 1:
  1.csv  HIV/AIDS (SICLOM)
  2.csv  Oncológicos (SIA/APAC)
  3.csv  Transplantados órgãos sólidos (ABTO)
  4.csv  TCTH (ABTO)
  8.csv  Fibrose cística (REBRAFC)
  12_dialise.csv  Diálise crônica (SBN) — overlay em nefropatias

Colunas: uf,elegiveis

Seed provisório: rode `python -m etl.seed_situacao1` (ou etl/seed_situacao1.py)
para preencher totais nacionais rateados por UF. Substitua pelos extratos
oficiais assim que disponíveis; depois `build_mart.py` + `build_nacional.py`.
