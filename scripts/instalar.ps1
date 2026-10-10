# Prepara el bot en un equipo nuevo. Se puede correr varias veces sin danar nada:
# solo crea lo que falta y nunca sobrescribe tu .env ni tu perfil.
$ErrorActionPreference = "Stop"
# Los scripts viven en scripts\; el proyecto es la carpeta padre.
$raiz = Split-Path $PSScriptRoot -Parent
$bot = Join-Path $raiz "job_bot"
$venv = Join-Path $bot ".venv"
$python = Join-Path $venv "Scripts\python.exe"

function Paso($texto) { Write-Host "`n>> $texto" -ForegroundColor Cyan }

function Copiar-SiFalta($origen, $destino) {
  if (Test-Path $destino) {
    Write-Host "   Ya existe $(Split-Path $destino -Leaf): se deja como esta."
  } else {
    Copy-Item $origen $destino
    Write-Host "   Creado $(Split-Path $destino -Leaf): rellenalo con tus datos." -ForegroundColor Yellow
  }
}

Paso "Comprobando Python"
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Host "   No se encontro Python. Instala Python 3.11 o superior desde python.org" -ForegroundColor Red
  exit 1
}
python --version

Paso "Creando el entorno virtual en job_bot\.venv"
if (-not (Test-Path $python)) { python -m venv $venv }

Paso "Instalando dependencias"
& $python -m pip install --upgrade pip --quiet
& $python -m pip install -r (Join-Path $bot "requirements.txt") --quiet
# Chromium solo lo usan las pruebas; el bot trabaja sobre tu Edge.
& $python -m playwright install chromium

Paso "Creando archivos de configuracion"
Copiar-SiFalta (Join-Path $raiz ".env.example") (Join-Path $raiz ".env")
Copiar-SiFalta (Join-Path $bot "candidate_profile.example.json") (Join-Path $bot "candidate_profile.json")

Paso "Corriendo las pruebas"
$fallidas = 0
Get-ChildItem (Join-Path $bot "tests\test_*.py") | ForEach-Object {
  & $python $_.FullName | Out-Null
  if ($LASTEXITCODE -ne 0) { $fallidas++; Write-Host "   FALLA: $($_.Name)" -ForegroundColor Red }
}
if ($fallidas -eq 0) { Write-Host "   Todas las pruebas pasan." -ForegroundColor Green }

Write-Host ""
Write-Host "Siguientes pasos:" -ForegroundColor Green
Write-Host "  1. Edita .env: SUPABASE_EMAIL y SUPABASE_PASSWORD, palabras clave y ruta de tu hoja de vida."
Write-Host "  2. Edita job_bot\candidate_profile.json con TUS datos reales."
Write-Host "  3. Corre .\scripts\iniciar_agente.ps1 -AlIniciar para usar el boton del panel web."
Write-Host "  4. Corre .\abrir_navegador_bot.ps1 e inicia sesion en Magneto y Computrabajo."
Write-Host "  5. Corre .\scripts\ejecutar_bot.ps1"
Write-Host ""
