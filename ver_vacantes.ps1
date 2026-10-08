# Levanta el panel en local (http://localhost:5173/panel/).
# El panel publicado vive en Vercel; este es para probar cambios del frontend.
# Lee las credenciales publicas de frontend\.env.local (copia de .env.example).
$frontend = "$PSScriptRoot\frontend"
if (-not (Test-Path "$frontend\.env.local")) { Copy-Item "$frontend\.env.example" "$frontend\.env.local" }
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontend'; npm run dev"
Start-Sleep -Seconds 6
Start-Process "http://localhost:5173/panel/"
Write-Host "  Panel abriendo en http://localhost:5173/panel/" -ForegroundColor Green
