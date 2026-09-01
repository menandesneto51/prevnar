# Pipeline CKAN jun/jul — download em pasta local (evita OneDrive) → filtrar → mart
$ErrorActionPreference = "Stop"
$Root = "C:\Users\Menandesneto\OneDrive\Área de Trabalho\prevnar"
$Raw = Join-Path $Root "data\raw\ckan_pni"
$Cache = Join-Path $env:LOCALAPPDATA "prevnar_ckan"
$Py = Join-Path $Root ".venv\Scripts\python.exe"
$Etl = Join-Path $Root "etl"
New-Item -ItemType Directory -Force -Path $Raw, $Cache | Out-Null

$JunUrl = "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/PNI/csv/vacinacao_jun_2026_csv.zip"
$JulUrl = "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/PNI/csv/vacinacao_jul_2026_csv.zip"
$JunSize = 2751059346
$JulSize = 2266767355

function Download-Zip($url, $dest, $expected) {
  $tmp = Join-Path $Cache (Split-Path $dest -Leaf)
  if ((Test-Path $tmp) -and ((Get-Item $tmp).Length -ge $expected)) {
    Write-Host "cache ok: $tmp"
  } else {
    Write-Host "curl → $tmp"
    & curl.exe -L --retry 10 --retry-delay 5 -C - -o $tmp $url
    if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 18) { throw "curl exit $LASTEXITCODE" }
    $sz = (Get-Item $tmp).Length
    if ($sz -lt $expected) { throw "incompleto: $sz < $expected" }
  }
  Copy-Item -Force $tmp $dest
  Write-Host "copiado para $dest"
}

Write-Host "=== Jun/2026 ==="
Download-Zip $JunUrl (Join-Path $Raw "vacinacao_jun_2026_csv.zip") $JunSize
Set-Location $Etl
& $Py -u extract_ckan_pni.py --mes jun --ano 2026 --skip-download
if ($LASTEXITCODE -ne 0) { throw "filtro jun falhou" }

Write-Host "=== Jul/2026 ==="
Download-Zip $JulUrl (Join-Path $Raw "vacinacao_jul_2026_csv.zip") $JulSize
& $Py -u extract_ckan_pni.py --mes jul --ano 2026 --skip-download
if ($LASTEXITCODE -ne 0) { throw "filtro jul falhou" }

Write-Host "=== Numerador + mart (mai+jun+jul) ==="
$env:RADAR_NUMERADOR_SOURCE = "csv"
& $Py -u -c @"
import numerador, build_mart, build_nacional
n = numerador.run(source='csv')
print('pessoas', n.get('total_pessoas'), 'doses', n.get('total_doses'))
print('arquivos', n.get('fonte_arquivos'))
d = build_mart.run(refresh_sources=False)
print('dashboard vac', (d.get('nacional') or {}).get('pessoas_vacinadas'))
out = build_nacional.build()
print('kpis vac', out['kpis'].get('pessoas_vacinadas_vpc20'))
print('mun', out['kpis'].get('municipios_com_vacinado'))
print('status sit1', next(s for s in out['indicadores_status'] if s['id']=='cobertura_sit1')['status'])
"@
Write-Host "=== PIPELINE OK ==="
