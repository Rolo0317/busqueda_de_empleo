#!/usr/bin/env pwsh

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════╗"
Write-Host "║  🚀 DESPLEGAR A GITHUB - Bot de Búsqueda de Empleo   ║"
Write-Host "╚════════════════════════════════════════════════════════╝"
Write-Host ""

$projectPath = Get-Location
Write-Host "📁 Proyecto: $projectPath"
Write-Host ""

# Verificar estructura
if (-not (Test-Path "job_bot") -or -not (Test-Path "magneto_job_system")) {
    Write-Host "❌ Error: Estructura incompleta"
    Write-Host "📍 Ve a: C:\Users\millo\Downloads\hoja de vida"
    exit 1
}
Write-Host "✅ Estructura validada"
Write-Host ""

# Verificar .gitignore
if (Test-Path ".gitignore") {
    Write-Host "✅ .gitignore encontrado"
} else {
    Write-Host "⚠️ Advertencia: .gitignore no encontrado"
}
Write-Host ""

# Inicializar git
Write-Host "⏳ Paso 1: Inicializando git..."
if (-not (Test-Path ".git")) {
    git init
    Write-Host "✅ Git repositorio inicializado"
} else {
    Write-Host "✅ Git repositorio ya existe"
}
Write-Host ""

# Configurar remote
Write-Host "⏳ Paso 2: Configurando remoto..."
git remote remove origin 2>$null
git remote add origin "https://github.com/Rolo0317/busqueda_de_empleo.git"
Write-Host "✅ Repositorio configurado"
Write-Host ""

# Ver cambios
Write-Host "⏳ Paso 3: Revisando archivos..."
$status = git status --porcelain
Write-Host "📊 Cambios a subir:"
Write-Host $status
Write-Host ""

# Verificar archivos prohibidos
$forbidden = ".env", ".venv", "node_modules", "*.log", "credentials.json"
$hasForbidden = $false
foreach ($pattern in $forbidden) {
    $found = $status | Select-String $pattern
    if ($found) {
        Write-Host "❌ ADVERTENCIA: Incluye archivo prohibido: $pattern"
        $hasForbidden = $true
    }
}

if ($hasForbidden) {
    Write-Host ""
    Write-Host "❌ ERROR: Hay archivos que NO deben subirse a GitHub"
    Write-Host "⚠️  Verifica .gitignore y vuelve a intentar"
    exit 1
}

Write-Host "✅ Sin archivos sensibles"
Write-Host ""

# Confirmar
Write-Host "════════════════════════════════════════════════════════"
$response = Read-Host "¿Continuar? (escribe 'SI' para confirmar)"

if ($response -ne "SI") {
    Write-Host "❌ Cancelado"
    exit 0
}
Write-Host ""

# Agregar archivos
Write-Host "⏳ Paso 4: Agregando archivos..."
git add .
Write-Host "✅ Archivos agregados"
Write-Host ""

# Commit
Write-Host "⏳ Paso 5: Creando commit..."
git commit -m "Initial commit: Bot de búsqueda de empleo con auditoría completa y mejoras de seguridad"
Write-Host "✅ Commit creado"
Write-Host ""

# Rama main
Write-Host "⏳ Paso 6: Rama main..."
git branch -M main
Write-Host "✅ En rama main"
Write-Host ""

# Push
Write-Host "⏳ Paso 7: Subiendo a GitHub (espera 1-2 minutos)..."
git push -u origin main
Write-Host "✅ Push completado"
Write-Host ""

Write-Host "════════════════════════════════════════════════════════"
Write-Host "✅ ¡DESPLIEGUE COMPLETADO!"
Write-Host "════════════════════════════════════════════════════════"
Write-Host ""
Write-Host "🎉 Tu proyecto está en GitHub:"
Write-Host "   https://github.com/Rolo0317/busqueda_de_empleo"
Write-Host ""
