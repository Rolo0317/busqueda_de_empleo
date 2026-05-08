Set-Location -LiteralPath $PSScriptRoot

Get-Process msedge -ErrorAction SilentlyContinue | Stop-Process -Force

if (-not (Test-Path -LiteralPath ".\.venv\Scripts\python.exe")) {
    python -m venv .venv
}

.\.venv\Scripts\python.exe -m ensurepip --upgrade
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
