# 🚀 Desplegar Dashboard en GitHub Pages (GRATIS - Sin Vercel)

GitHub Pages es **completamente gratuito** y perfecto para desplegar tu dashboard estático.

---

## ⏱️ Tiempo Total: 10 Minutos

### Paso 1: Crear rama gh-pages

```powershell
cd "C:\Users\millo\Downloads\hoja de vida"
git checkout -b gh-pages
```

### Paso 2: Mantener solo los archivos del dashboard

```powershell
# Eliminar archivos que no necesitamos
Remove-Item -Recurse -Force job_bot
Remove-Item -Recurse -Force magneto_job_system\bot
Remove-Item -Recurse -Force magneto_job_system\database
Remove-Item -Recurse -Force magneto_job_system\services
Remove-Item -Recurse -Force magneto_job_system\utils
Remove-Item -Recurse -Force magneto_job_system\scrapers
Remove-Item -Recurse -Force magneto_job_system\logs
Remove-Item -Recurse -Force magneto_job_system\package.json
Remove-Item -Recurse -Force magneto_job_system\server.js

# Mantener solo:
# - magneto_job_system/dashboard/public/*
# - README.md
# - .gitignore
```

### Paso 3: Mover archivos del dashboard a la raíz

```powershell
# Copiar archivos del dashboard a la raíz
Copy-Item magneto_job_system\dashboard\public\* .

# Eliminar la carpeta magneto_job_system
Remove-Item -Recurse -Force magneto_job_system
```

### Paso 4: Crear archivo index.html si no existe

Verificar que existe `index.html` en la raíz. Si no, crear uno:

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Bot de Búsqueda de Empleo</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div id="app"></div>
    <script src="app.js"></script>
</body>
</html>
```

### Paso 5: Hacer commit en gh-pages

```powershell
git add .
git commit -m "Deploy to GitHub Pages: Dashboard estático"
```

### Paso 6: Push a GitHub

```powershell
git push origin gh-pages
```

### Paso 7: Habilitar GitHub Pages

1. Abre: https://github.com/Rolo0317/busqueda_de_empleo/settings
2. Ve a: **Pages** (en el menú lateral)
3. En **Source**: Selecciona Branch → `gh-pages`
4. Presiona **Save**

**¡Listo!** Tu dashboard estará en:
```
https://rolo0317.github.io/busqueda_de_empleo
```

---

## 🎯 Alternativa: Script Automatizado

```powershell
# Script rápido para preparar GitHub Pages
$ErrorActionPreference = "Stop"

# Crear rama gh-pages
git checkout -b gh-pages 2>$null || git checkout gh-pages

# Limpiar archivos innecesarios
$toRemove = @("job_bot", "magneto_job_system/bot", "magneto_job_system/database", 
              "magneto_job_system/services", "magneto_job_system/utils", 
              "magneto_job_system/scrapers", "magneto_job_system/logs",
              "magneto_job_system/package.json", "magneto_job_system/server.js",
              ".gitignore", "DEPLOYMENT.md", "DEPLOY_WEB.md", "VERCEL_DEPLOY.md",
              "deploy_to_github.ps1", "vercel.json", "AUDITORIA*", "INSTRUCCIONES*",
              "RESUMEN*", "README.md")

foreach ($item in $toRemove) {
    if (Test-Path $item) {
        Remove-Item -Recurse -Force $item -ErrorAction SilentlyContinue
    }
}

# Copiar dashboard a raíz
if (Test-Path "magneto_job_system/dashboard/public") {
    Copy-Item -Path "magneto_job_system/dashboard/public/*" -Destination "." -Recurse -Force
    Remove-Item -Recurse -Force magneto_job_system
}

# Commit
git add .
git commit -m "Deploy to GitHub Pages: Dashboard estático"
git push origin gh-pages

Write-Host "✅ GitHub Pages configurado!"
Write-Host "URL: https://rolo0317.github.io/busqueda_de_empleo"
```

---

## 📊 URL Final

```
Dashboard Público:  https://rolo0317.github.io/busqueda_de_empleo
Repositorio:        https://github.com/Rolo0317/busqueda_de_empleo
Rama principal:     main (código fuente)
Rama deployment:    gh-pages (dashboard estático)
```

---

## 🔄 Actualizar Dashboard

Cada vez que cambies el dashboard:

```powershell
# En rama main, hacer cambios
# Luego:

cd magneto_job_system/dashboard/public

# Hacer cambios en app.js, style.css, index.html

# Agregar cambios
git add .

# Commit en main
git commit -m "Update dashboard"
git push origin main

# Cambiar a gh-pages y actualizar
git checkout gh-pages
git merge main
git push origin gh-pages

# Volver a main
git checkout main
```

---

## 💡 Ventajas de GitHub Pages

✅ **Completamente GRATIS**  
✅ **Sin necesidad de Vercel**  
✅ **Actualizaciones automáticas desde GitHub**  
✅ **Hosting incluido en GitHub**  
✅ **HTTPS automático**  
✅ **Dominio .github.io gratuito**  

---

## ⚠️ Limitaciones

❌ No puede conectar a backend dinámico (API MySQL)  
❌ Solo archivos estáticos (HTML, CSS, JS)  
❌ El bot sigue corriendo en local  

**SOLUCIÓN:** El dashboard es estático pero se actualiza cuando:
- El bot ejecuta y actualiza MySQL
- Recargas la página (se conecta a tu BD local)

---

## 🚀 Próximos Pasos

1. Ejecutar los comandos de arriba
2. Verificar en GitHub Pages que está activo
3. Compartir URL pública: `https://rolo0317.github.io/busqueda_de_empleo`
4. Bot sigue corriendo en tu computadora

---

**¡Tu dashboard está PÚBLICAMENTE DISPONIBLE en GitHub Pages! 🎉**

