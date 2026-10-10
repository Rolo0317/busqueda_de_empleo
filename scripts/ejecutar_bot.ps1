# Lanza el bot sobre el navegador ya abierto con sesion iniciada.
# Los scripts viven en scripts\; el proyecto es la carpeta padre.
$raiz = Split-Path $PSScriptRoot -Parent
$ErrorActionPreference = "Stop"

try {
  $null = Invoke-WebRequest "http://127.0.0.1:9222/json/version" -UseBasicParsing -TimeoutSec 5
} catch {
  Write-Host ""
  Write-Host "  No hay navegador escuchando en el puerto 9222." -ForegroundColor Red
  Write-Host "  Corre primero:  .\abrir_navegador_bot.ps1" -ForegroundColor Yellow
  Write-Host ""
  exit 1
}

Write-Host ""
Write-Host "  Navegador detectado. Lanzando el bot..." -ForegroundColor Green
Write-Host ""
& "$raiz\job_bot\.venv\Scripts\python.exe" "$raiz\job_bot\main.py"
