# Mapas e níveis territoriais — referência VIGIA VSR

Extraído de `OneDrive/Projeto VSR/Projeto VSR` para reuso no Radar Vacinal VPC20/CRIE.

## Bases oficiais de malha (geometria)

Fonte FTP IBGE (Malha Municipal Digital **2024**):

`https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2024/Brasil/`

| Camada | Arquivo bruto | GeoJSON no VSR | Nível |
|--------|---------------|----------------|-------|
| País | `BR_Pais_2024.zip` | `br-pais-2024.geojson` | nacional |
| Regiões | `BR_Regioes_2024.zip` | `br-regioes-2024.geojson` | N / NE / CO / SE / S |
| UF | `BR_UF_2024.zip` | `br-uf-2024.geojson` (+ `br-uf-simplified.geojson`) | 27 UFs |
| Municípios | `BR_Municipios_2024.zip` | `municipios/{UF}.geojson` | ~5.571 / UF |

- CRS: **EPSG:4674** (SIRGAS 2000)
- Pipeline: `python -m vigia_vsr.ingestion.ibge_malhas --download` · script `scripts/load-ibge-malhas.ps1`
- Raw fora do Git: `C:\vigia-raw\ibge\malhas_2024`
- Staging/web (VSR): `data/staging/ibge_malhas` → `apps/web/public/geo/`
- **Cópia no Prevnar:** `web/public/geo/` (país, regiões, UF, 27 UFs municipais, manifest)
- URLs estáticas: `/geo/br-uf-2024.geojson`, `/geo/municipios/SP.geojson`, `/geo/ibge-malhas-manifest.json`
- API VSR: `GET /v1/territories/ibge/manifest` · `GET /v1/territories/ibge/geojson?level=uf|municipio&uf=SP`
- UI VSR: Leaflet + coropléticos (`NationalUfMapClient`, `NationalMunicipalityMapClient`)

## Nível intramunicipal (piloto privado)

Malha de **setores censitários Censo 2022**:

`.../malhas_de_setores_censitarios__divisoes_intramunicipais/censo_2022/setores/shp/UF/{UF}_setores_CD2022.zip`

+ agregados demográficos: `Agregados_por_setores_demografia_BR.zip`  
Ingestão: `vigia_vsr.ingestion.censo_setores_2022` (piloto MT).

## Hierarquia de drill-down no painel VSR

```text
Brasil (país)
  → Região IBGE (5)
    → UF (27)          ← farol / gap nacional; clique
      → Município      ← mapa municipal da UF; ficha /municipios/[ibge]
        → Setor CD2022 ← só potencial privado / piloto
```

Pontos CNES (lat/lon) são **camada vetorial de estabelecimentos**, não malha poligonal.

## Atributos / densidades (não são malha, mas alimentam o mapa)

| Base | Papel no mapa |
|------|----------------|
| Universo IBGE municípios (5.571) | QLD-13 — com dado / sem dado |
| População IBGE / TABNET (zip MS) | Denominadores, porte, gap |
| ANS 60+ | Camada privada / sensibilidade |
| CNES (174/26 etc.) | Pontos no mapa; prioridade de rede |
| IPEA IVS | Equidade GEO-05 (quando staging) |
| SIVEP | GEO-08 cobertura × carga |
| SI-PNI / MS tabelas | Farol e gap oficiais |

## O que levar para o Prevnar / VPC20

**P0 mapas nacionais**

1. Reusar (ou rebaixar) malhas IBGE 2024: **UF + municípios** (e opcionalmente regiões).
2. Drill: Nacional → UF → Município (mesmo contrato `/geo` ou cópia em `web/public/geo`).
3. Atributos: gap VPC20, doses, elegíveis, SINAN/SIH ecológicos por UF (e muni quando houver IBGE 7 dígitos).

**P1**

4. Região de saúde MS (atributo tabular município→RS; malha própria se existir no DEMAS).
5. Pontos CNES CRIE sobre o mapa municipal.
6. Setores só se houver caso de uso intramunicipal (como no VSR privado).

**Não confundir**

- Tipo estabelecimento `15` na API PNI ≠ CRIE — validar CNES.
- Malha IBGE ≠ região de saúde (níveis diferentes).
