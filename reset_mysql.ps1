#!/usr/bin/env powershell
# Script para resetear contraseña MySQL en Windows
# DEBE ejecutarse como ADMINISTRADOR

#Requires -RunAsAdministrator

$MySQLPath = "C:\Program Files\MySQL\MySQL Server 9.7\bin"
$ServiceName = "MySQL97"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "RESET CONTRASEÑA MYSQL - MODO SEGURO" -ForegroundColor Cyan  
Write-Host "========================================`n" -ForegroundColor Cyan

# Paso 1: Detener servicio
Write-Host "[1/4] Deteniendo servicio MySQL..." -ForegroundColor Yellow
Stop-Service $ServiceName -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-Host "✓ Servicio detenido" -ForegroundColor Green

# Paso 2: Iniciar MySQL sin validación de contraseña
Write-Host "`n[2/4] Iniciando MySQL en modo seguro (sin contraseña)..." -ForegroundColor Yellow
$mysqldPath = Join-Path $MySQLPath "mysqld.exe"
$dataPath = "C:\ProgramData\MySQL\MySQL Server 9.7\Data"

# Crear proceso en background
$processArgs = @(
    "--skip-grant-tables",
    "--datadir=$dataPath"
)

$process = Start-Process -FilePath $mysqldPath -ArgumentList $processArgs -PassThru -NoNewWindow
Start-Sleep -Seconds 3
Write-Host "✓ MySQL iniciado sin autenticación" -ForegroundColor Green

# Paso 3: Conectar y resetear contraseña
Write-Host "`n[3/4] Resetando contraseña..." -ForegroundColor Yellow

$mysqlPath = Join-Path $MySQLPath "mysql.exe"
$sqlCommands = @"
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED BY 'admin123';
QUIT;
"@

$sqlCommands | & $mysqlPath -u root -h localhost

Write-Host "✓ Contraseña reseteada a: 'admin123'" -ForegroundColor Green

# Paso 4: Reiniciar servicio normal
Write-Host "`n[4/4] Restarting MySQL con configuración normal..." -ForegroundColor Yellow
Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Start-Service $ServiceName
Start-Sleep -Seconds 3
Write-Host "✓ MySQL reiniciado" -ForegroundColor Green

# Verificar conexión
Write-Host "`n[VERIFICACIÓN] Probando conexión..." -ForegroundColor Yellow
try {
    python -c "import mysql.connector; conn = mysql.connector.connect(host='localhost', user='root', password='admin123'); print('EXITO: Conexion establecida'); conn.close()"
    Write-Host "✓ Conexión exitosa!" -ForegroundColor Green
} catch {
    Write-Host "✗ No se pudo conectar" -ForegroundColor Red
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "PASOS SIGUIENTES:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. Abre: job_bot/.env" -ForegroundColor White
Write-Host "2. Cambia: DB_PASSWORD=admin123" -ForegroundColor White
Write-Host "3. Guarda y ejecuta: .\run_bot.ps1" -ForegroundColor White
Write-Host "`n"
