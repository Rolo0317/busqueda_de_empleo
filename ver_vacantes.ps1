# Levanta el panel: backend en 8001 y frontend en 5173.
Start-Process powershell -ArgumentList "-NoExit", "-Command",
  "cd '$PSScriptRoot\backend'; ..\job_bot\.venv\Scripts\python.exe manage.py runserver 8001"
Start-Sleep -Seconds 3
Start-Process powershell -ArgumentList "-NoExit", "-Command",
  "cd '$PSScriptRoot\frontend'; npm run dev"
Start-Sleep -Seconds 6
Start-Process "http://localhost:5173"
Write-Host "  Panel abriendo en http://localhost:5173" -ForegroundColor Green
