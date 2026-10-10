#!/usr/bin/env powershell
# Restablece la clave del usuario root de MySQL en Windows.
# Debe ejecutarse como ADMINISTRADOR. Pide la clave nueva: no hay ninguna escrita aqui.
param(
  [string]$Version = "9.7",
  [string]$ServiceName = ""
)

#Requires -RunAsAdministrator

$MySQLPath = "C:\Program Files\MySQL\MySQL Server $Version\bin"
$dataPath = "C:\ProgramData\MySQL\MySQL Server $Version\Data"
if (-not $ServiceName) { $ServiceName = "MySQL" + $Version.Replace(".", "") }

if (-not (Test-Path $MySQLPath)) {
  Write-Host "No existe $MySQLPath. Indica tu version:  .\reset_mysql.ps1 -Version 8.0" -ForegroundColor Red
  exit 1
}

$segura = Read-Host "Clave nueva para root" -AsSecureString
$clave = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
  [Runtime.InteropServices.Marshal]::SecureStringToBSTR($segura))
if (-not $clave) {
  Write-Host "La clave no puede quedar vacia." -ForegroundColor Red
  exit 1
}
$claveSql = $clave.Replace("'", "''")

Write-Host "`n[1/4] Deteniendo el servicio $ServiceName..." -ForegroundColor Yellow
Stop-Service $ServiceName -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host "[2/4] Iniciando MySQL sin validar claves..." -ForegroundColor Yellow
$process = Start-Process -FilePath (Join-Path $MySQLPath "mysqld.exe") `
  -ArgumentList @("--skip-grant-tables", "--datadir=`"$dataPath`"") -PassThru -NoNewWindow
Start-Sleep -Seconds 3

Write-Host "[3/4] Cambiando la clave..." -ForegroundColor Yellow
@"
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED BY '$claveSql';
QUIT;
"@ | & (Join-Path $MySQLPath "mysql.exe") -u root -h localhost

Write-Host "[4/4] Reiniciando MySQL normal..." -ForegroundColor Yellow
Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Start-Service $ServiceName

Write-Host "`nListo. Pon la misma clave en DB_PASSWORD dentro de .env" -ForegroundColor Green
