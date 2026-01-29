<# Quick QA tests for the new top-header navigation and mock data endpoints #>
<# This script assumes the dev server is started via `python start.py` and available at http://localhost:8000 
   It performs simple HTTP checks to validate routes and mock data endpoints. It does NOT perform UI automation.
   It is designed for quick smoke checks after Patch A (UI) and Patch B (mock data) were applied. #>

param(
  [switch]$Verbose
)

Write-Host "Running Quick QA Tests for Facturacion OCR - UI + Mock" -ForegroundColor Cyan

$base = 'http://localhost:8000'

function Test-BodyContains {
  param(
    [string]$url,
    [string]$expected
  )
  try {
    $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -ErrorAction Stop
    $body = $resp.Content
    if ($body -and $body -like "*" + $expected + "*") {
      if ($Verbose) { Write-Host "[OK] $url contains '$expected'" -ForegroundColor Green }
      return $true
    } else {
      Write-Host "[FAIL] $url missing expected text '$expected'" -ForegroundColor Yellow
      return $false
    }
  } catch {
    Write-Host "[ERROR] Failed to fetch $url: $_" -ForegroundColor Red
    return $false
  }
}

function Test-Json {
  param(
    [string]$url,
    [string]$key,
    [string]$subpath = ''
  )
  try {
    $resp = Invoke-RestMethod -Uri $url -ErrorAction Stop
    if ($null -eq $resp) { Write-Host "[ERROR] Empty json from $url" -ForegroundColor Red; return $false }
    $obj = $resp
    if ($subpath) {
      foreach ($p in $subpath -split '/') { if ($obj.$p -ne $null) { $obj = $obj.$p } else { $obj = $null; break } }
    }
    if ($null -eq $obj) { Write-Host "[ERROR] Path not found in json from $url"; return $false }
    if ($key -and $obj.$key -ne $null) { Write-Host "[OK] $url contains $key"; return $true } else { Write-Host "[WARN] $url missing key $key"; return $false }
  } catch {
    Write-Host "[ERROR] JSON fetch failed for $url: $_" -ForegroundColor Red
    return $false
  }
}

Write-Host "1) Verifica rutas principales (texto de la página)" -ForegroundColor Magenta
Test-BodyContains -url "$base/negocio/emitir-factura" -expected "Emitir Factura" | Out-Null
Test-BodyContains -url "$base/negocio/facturar-gastos" -expected "Facturar Gastos" | Out-Null
Test-BodyContains -url "$base/negocio/mis-facturas" -expected "Mis Facturas" | Out-Null
Test-BodyContains -url "$base/negocio/mis-clientes" -expected "Mis Clientes" | Out-Null
Test-BodyContains -url "$base/configuracion/perfil" -expected "Mi Perfil" | Out-Null

Write-Host "2) Validación de datos mock (endpoints)" -ForegroundColor Magenta
$jsonCheck1 = Test-Json -url "$base/api/mock/business-clients" -key 'clients'
$jsonCheck2 = Test-Json -url "$base/api/mock/business-invoices" -key 'invoices'
$jsonCheck3 = Test-Json -url "$base/api/mock/client-invoices" -key 'invoices'
$jsonCheck4 = Test-Json -url "$base/api/mock/profile" -key 'username'
Write-Host "Tests de datos mock realizados" -ForegroundColor Green

Write-Host "3) Notificaciones placeholder" -ForegroundColor Magenta
Test-BodyContains -url "$base/api/notifications" -expected "\{" -ErrorAction SilentlyContinue | Out-Null

Write-Host "4) Notificaciones en UI (campanita)" -ForegroundColor Magenta
# Este paso se verifica visualmente; se recomienda abrir la UI y hacer clic en la campana para confirmar el dropdown.

Write-Host "Todos los checks básicos han finalizado. Revisa los resultados arriba." -ForegroundColor Cyan
