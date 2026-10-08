# Deja la PC escuchando el boton "Ejecutar" del panel web.
#   .\iniciar_agente.ps1             arranca el agente en esta ventana
#   .\iniciar_agente.ps1 -AlIniciar  ademas lo deja arrancando solo con Windows
param([switch]$AlIniciar)

$python = "$PSScriptRoot\job_bot\.venv\Scripts\python.exe"
$agente = "$PSScriptRoot\job_bot\agente.py"

if ($AlIniciar) {
  $inicio = [Environment]::GetFolderPath("Startup")
  $acceso = (New-Object -ComObject WScript.Shell).CreateShortcut("$inicio\Agente bot de empleo.lnk")
  $acceso.TargetPath = "powershell.exe"
  $acceso.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Minimized -File `"$PSCommandPath`""
  $acceso.WorkingDirectory = $PSScriptRoot
  $acceso.Save()
  Write-Host "  Listo: el agente arrancara solo al iniciar sesion en Windows." -ForegroundColor Green
}

Write-Host ""
Write-Host "  Agente del bot escuchando el panel web. No cierres esta ventana." -ForegroundColor Green
Write-Host ""
& $python $agente
