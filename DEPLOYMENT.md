# Guía de Despliegue a GitHub

Esta guía te ayudará a desplegar el proyecto a tu repositorio de GitHub.

---

## Opción 1: Subir Proyecto Existente a GitHub

Si ya tienes el proyecto localmente:

### 1. Inicializar Git (si no está iniciado)

```bash
cd "C:\Users\millo\Downloads\hoja de vida"
git init
```

### 2. Verificar .gitignore

```bash
# Confirmar que .gitignore existe y tiene contenido
cat .gitignore
```

Debe incluir:
```
.env
.venv/
node_modules/
*.log
```

### 3. Agregar Archivos

```bash
# Agregar todos EXCEPTO lo que está en .gitignore
git add .

# Verificar qué se va a subir
git status
```

**IMPORTANTE:** Verifica que NO aparezcan:
- `.env` ❌
- `.venv/` ❌
- `node_modules/` ❌
- `*.log` ❌
- Archivos con credenciales ❌

### 4. Commit Inicial

```bash
git commit -m "Initial commit: Bot de búsqueda de empleo con MySQL y dashboard"
```

### 5. Conectar Repositorio Remoto

```bash
# Cambiar USUARIO por tu usuario de GitHub
git remote add origin https://github.com/Rolo0317/busqueda_de_empleo.git

# Verificar
git remote -v
```

### 6. Cambiar Rama a Main (si es necesario)

```bash
git branch -M main
```

### 7. Push a GitHub

```bash
# Primera vez: subir todo
git push -u origin main

# Siguientes veces: solo git push
```

---

## Opción 2: Crear Repositorio en GitHub y Clonar

Si prefieres empezar desde GitHub:

### 1. En GitHub:
1. Crear nuevo repositorio: https://github.com/new
2. Nombre: `busqueda_de_empleo`
3. NO inicializar con README (nosotros ya lo tenemos)
4. Copiar URL: `https://github.com/Rolo0317/busqueda_de_empleo.git`

### 2. En Terminal:

```bash
# Cambiar a carpeta padre
cd "C:\Users\millo\Downloads"

# Clonar repo vacío
git clone https://github.com/Rolo0317/busqueda_de_empleo.git busqueda_de_empleo_temp

# Copiar archivos
copy "hoja de vida\*" busqueda_de_empleo_temp\
```

### 3. Hacer Commit y Push

```bash
cd busqueda_de_empleo_temp
git add .
git commit -m "Initial commit"
git push -u origin main
```

---

## Opción 3: Automatizado (Script PowerShell)

Crear archivo `push_to_github.ps1`:

```powershell
# Variables
$githubURL = "https://github.com/Rolo0317/busqueda_de_empleo.git"
$projectPath = "C:\Users\millo\Downloads\hoja de vida"

# Ir al proyecto
cd $projectPath

# Inicializar git si no existe
if (-not (Test-Path ".git")) {
    git init
}

# Configurar remote
git remote remove origin 2>$null
git remote add origin $githubURL

# Agregar archivos
git add .

# Verificar cambios
Write-Host "Cambios a subir:"
git status

# Confirmar antes de hacer push
$response = Read-Host "¿Continuar con el push? (S/N)"
if ($response -eq "S") {
    git commit -m "Actualización: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    git branch -M main
    git push -u origin main
    Write-Host "✅ Push completado"
} else {
    Write-Host "❌ Push cancelado"
}
```

Ejecutar:
```powershell
.\push_to_github.ps1
```

---

## Después de Subir a GitHub

### 1. Proteger Rama Main

En GitHub:
1. Ir a Settings → Branches
2. Agregar regla de protección para `main`
3. Requerir pull requests antes de merge

### 2. Crear Documentación

✅ Ya tienes:
- `README.md` - Documentación principal
- `.env.example` - Plantilla de configuración
- `AUDITORIA_COMPLETA.md` - Informe técnico
- `.gitignore` - Archivos ignorados

### 3. Crear Issues para Tareas Pendientes

En GitHub Issues, crear:

```markdown
## [CRÍTICO] Implementar Autenticación en Dashboard
- [ ] JWT en API
- [ ] Login en frontend
- [ ] CORS configurado
- [ ] Rate limiting

## [MEJORA] Connection Pooling en MySQL
- [ ] Cambiar de conexión individual a pool
- [ ] Agregar reintentos
- [ ] Mejorar performance

## [FEATURE] Docker Support
- [ ] Dockerfile para Python bot
- [ ] Dockerfile para Node dashboard
- [ ] docker-compose.yml
```

### 4. Crear Releases

Para versiones estables:

```bash
git tag -a v1.0.0 -m "Version 1.0.0 - Initial Release"
git push origin v1.0.0
```

---

## Actualizar Código Localmente

Después de trabajar en el código:

```bash
# Ver cambios
git status

# Agregar cambios
git add .

# Commit con mensaje descriptivo
git commit -m "Fix: Verificación de login cada 5 ciclos"

# Push
git push origin main
```

---

## Descargar Cambios desde GitHub

Si trabajas en múltiples computadoras:

```bash
# Ir al proyecto
cd "ruta/del/proyecto"

# Descargar cambios
git pull origin main
```

---

## Troubleshooting

### Error: "fatal: remote origin already exists"

```bash
git remote remove origin
git remote add origin https://github.com/Rolo0317/busqueda_de_empleo.git
```

### Error: "permission denied"

Generar token de acceso:
1. GitHub → Settings → Developer settings → Personal access tokens
2. Generar token con permisos `repo`
3. Usar como contraseña en lugar de password

O configurar SSH:
```bash
git remote set-url origin git@github.com:Rolo0317/busqueda_de_empleo.git
```

### Subió .env por accidente

```bash
# Remover del repo (pero no del local)
git rm --cached .env

# Agregar a .gitignore
echo ".env" >> .gitignore

# Commit
git add .gitignore
git commit -m "Remove .env from tracking"
git push origin main

# IMPORTANTE: Cambiar credenciales en GitHub si fue expuesto
```

---

## Verificación Final

Antes de considerar el proyecto "listo":

- [x] `.gitignore` incluye `.env` ✅
- [x] README.md completo ✅
- [x] `.env.example` con instrucciones ✅
- [x] AUDITORIA_COMPLETA.md ✅
- [x] Código mejorado (verificación de login) ✅
- [ ] Push a GitHub ← TÚ ESTÁS AQUÍ
- [ ] Rama protegida en GitHub
- [ ] Issues creados
- [ ] Release v1.0.0

---

## Próximos Pasos (Post-Deploy)

1. **Implementar Autenticación:**
   ```javascript
   // magneto_job_system/middleware/auth.js
   const apiKeyMiddleware = (req, res, next) => {
     const apiKey = req.headers['x-api-key'];
     if (apiKey !== process.env.API_KEY) {
       return res.status(401).json({ error: 'Unauthorized' });
     }
     next();
   };
   ```

2. **Agregar GitHub Actions (CI/CD):**
   ```yaml
   # .github/workflows/test.yml
   name: Tests
   on: [push, pull_request]
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: Run tests
           run: npm test
   ```

3. **Docker (Opcional):**
   ```dockerfile
   FROM node:18-alpine
   WORKDIR /app
   COPY package*.json ./
   RUN npm install
   COPY . .
   EXPOSE 3000
   CMD ["npm", "start"]
   ```

---

## Contacto & Soporte

Si tienes problemas:
1. Revisar los logs en `bot.log`
2. Consultar `AUDITORIA_COMPLETA.md`
3. Abrir issue en GitHub
4. Contactar al mantenedor

---

**Última actualización:** Mayo 2026

