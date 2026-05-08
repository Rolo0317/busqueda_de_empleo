Set-Location -LiteralPath $PSScriptRoot
Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force
npm run bot
