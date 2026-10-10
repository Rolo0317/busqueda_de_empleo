# Deja el bot corriendo solo: una tarea de Windows arranca el supervisor al
# iniciar sesion y lo levanta de nuevo si muere. El supervisor abre el Edge
# del bot, lanza main.py y lo relanza si se cae o se cuelga.
#   .\scripts\instalar_supervisor.ps1             instala la tarea y la arranca
#   .\scripts\instalar_supervisor.ps1 -Quitar     la elimina (el bot deja de arrancar solo)
param([switch]$Quitar)
# Los scripts viven en scripts\; el proyecto es la carpeta padre.
$raiz = Split-Path $PSScriptRoot -Parent
$nombre = "Bot de empleo - supervisor"

if ($Quitar) {
  Unregister-ScheduledTask -TaskName $nombre -Confirm:$false -ErrorAction SilentlyContinue
  Write-Host "  Tarea eliminada. El bot ya no arranca solo con Windows." -ForegroundColor Yellow
  exit 0
}

# pythonw.exe no abre ventana: el supervisor escribe en job_bot\logs\supervisor.log.
$accion = New-ScheduledTaskAction `
  -Execute "$raiz\job_bot\.venv\Scripts\pythonw.exe" `
  -Argument "`"$raiz\job_bot\supervisor.py`"" `
  -WorkingDirectory "$raiz\job_bot"

# Al iniciar sesion: el Edge del bot necesita el escritorio del usuario.
$disparador = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

$ajustes = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
  -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) `
  -ExecutionTimeLimit (New-TimeSpan -Seconds 0) -MultipleInstances IgnoreNew

$usuario = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $nombre -Action $accion -Trigger $disparador `
  -Settings $ajustes -Principal $usuario -Force | Out-Null
Start-ScheduledTask -TaskName $nombre

Write-Host ""
Write-Host "  Listo: el supervisor del bot arranca con Windows y ya esta corriendo." -ForegroundColor Green
Write-Host "  Pausar o reanudar: boton del panel. Registro: job_bot\logs\supervisor.log"
Write-Host "  Quitarlo: .\scripts\instalar_supervisor.ps1 -Quitar"
Write-Host ""
