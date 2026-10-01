# Abre el navegador que el bot va a controlar.
# Inicia sesion aqui y NO cierres la ventana: el bot trabaja dentro de ella.
$perfil = "$PSScriptRoot\job_bot\.edge-bot"
$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# Solo se cierra el Edge del bot (el que usa este perfil). Cerrar todos los
# procesos de Edge se llevaba por delante el navegador personal del usuario.
Get-CimInstance Win32_Process -Filter "Name='msedge.exe'" |
  Where-Object { $_.CommandLine -like "*$perfil*" } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 3

# La ruta lleva espacios ("hoja de vida"): sin comillas, Edge la partia en
# pedazos, guardaba el perfil en Downloads\hoja y abria "de" y "vida\..."
# como pestanas basura.
Start-Process -FilePath $edge -ArgumentList @(
  "--remote-debugging-port=9222",
  "--user-data-dir=`"$perfil`"",
  "--profile-directory=Default",
  "--no-first-run",
  "--no-default-browser-check",
  "--disable-features=msEdgeStartupBoost",
  "https://www.magneto365.com/co"
)
Start-Sleep -Seconds 6

try {
  $null = Invoke-WebRequest "http://127.0.0.1:9222/json/version" -UseBasicParsing -TimeoutSec 5
  Write-Host ""
  Write-Host "  Navegador listo en el puerto 9222." -ForegroundColor Green
  Write-Host "  1. Si no tienes sesion, inicia sesion en Magneto y en Computrabajo."
  Write-Host "  2. NO cierres esta ventana."
  Write-Host "  3. Corre:  .\ejecutar_bot.ps1"
  Write-Host ""
} catch {
  Write-Host "  El puerto 9222 no responde. Revisa que Edge haya abierto." -ForegroundColor Red
}
