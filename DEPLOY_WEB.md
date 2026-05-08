# 🚀 Desplegar Dashboard en la Web (Gratuito)

Aquí tienes **3 opciones** para publicar el dashboard gratuitamente:

---

## Opción 1: VERCEL (⭐ Recomendado - 5 minutos)

**VERCEL** es la más fácil y rápida.

### Pasos:

#### 1. Instalar Vercel CLI
```powershell
npm install -g vercel
```

#### 2. Login en Vercel
```powershell
vercel login
```

#### 3. Desplegar
```powershell
cd "C:\Users\millo\Downloads\hoja de vida"
vercel
```

Sigue los pasos:
- Project name: `busqueda-de-empleo`
- Root directory: `.`
- Framework: `Other`
- Build command: `npm --prefix magneto_job_system install && npm --prefix magneto_job_system run check`
- Output directory: `magneto_job_system/dashboard/public`

#### 4. Configurar Variables de Entorno
En el panel de Vercel:
1. Settings → Environment Variables
2. Agregar:
   - `DB_HOST` = tu IP o dominio MySQL
   - `DB_PORT` = 3306
   - `DB_USER` = root
   - `DB_PASSWORD` = tu contraseña
   - `DB_NAME` = job_bot

**Tu dashboard estará en:** `https://busqueda-de-empleo.vercel.app`

---

## Opción 2: RAILWAY (💰 Requiere tarjeta, pero muy potente)

Railway es excelente para full-stack. Puedes desplegar bot + dashboard + BD todo en un lugar.

**Ventajas:**
- ✅ Soporta Node.js + Python + MySQL
- ✅ Panel visual excelente
- ✅ $5/mes gratis (crédito inicial)

**Pasos:**
1. Ir a https://railway.app
2. Login con GitHub
3. New Project → GitHub Repo
4. Seleccionar `busqueda_de_empleo`
5. Railway detecta automáticamente
6. Deploy

---

## Opción 3: GITHUB PAGES (Estático - Solo para frontend)

Si solo quieres la interfaz sin backend:

### Pasos:

#### 1. Crear rama gh-pages
```bash
git checkout -b gh-pages
```

#### 2. Copiar solo el frontend
```bash
# Copiar dashboard estático
copy magneto_job_system\dashboard\public\* .
```

#### 3. Hacer commit y push
```bash
git add .
git commit -m "Deploy to GitHub Pages"
git push origin gh-pages
```

#### 4. Habilitar GitHub Pages
1. GitHub → Settings → Pages
2. Source: Branch `gh-pages`
3. Save

**Tu dashboard estará en:** `https://rolo0317.github.io/busqueda_de_empleo`

---

## 🎯 RECOMENDACIÓN

Para tu caso, lo ideal es:

### 1️⃣ Vercel (Frontend Node.js) - **GRATIS**
```powershell
vercel --prod
```
El dashboard estará en: `https://busqueda-de-empleo.vercel.app`

### 2️⃣ Bot Python en Local o en Servidor
El bot sigue corriendo en tu computadora y escribe en MySQL

### 3️⃣ Base de Datos MySQL
- En tu computadora (local)
- O en un servidor MySQL gratuito como:
  - PlanetScale (MySQL compatible)
  - CockroachDB
  - Firebase Firestore

---

## 🚀 FORMA MÁS RÁPIDA (15 minutos):

### Paso 1: Desplegar en Vercel
```powershell
npm install -g vercel
vercel login
cd "C:\Users\millo\Downloads\hoja de vida"
vercel --prod
```

### Paso 2: Configurar Variables en Vercel
Panel de Vercel → Environment Variables:
```
DB_HOST = 192.168.x.x (tu IP local)
DB_USER = root
DB_PASSWORD = tu_contraseña
DB_NAME = job_bot
```

### Paso 3: Exponer MySQL a Internet
```bash
# En mysql
SELECT USER(), DATABASE();
ALTER USER 'root'@'%' IDENTIFIED BY 'tu_contraseña_segura';
FLUSH PRIVILEGES;
```

---

## 📊 Comparativa

| Opción | Costo | Facilidad | BD Incluida | Soporte |
|--------|-------|-----------|-------------|---------|
| **Vercel** | Gratis | ⭐⭐⭐⭐⭐ | Requiere otra | Node.js ✅ |
| **Railway** | $5/mes gratis | ⭐⭐⭐⭐ | ✅ MySQL | Full-stack ✅ |
| **GitHub Pages** | Gratis | ⭐⭐⭐ | ❌ No | Solo estático |

---

## ⚡ OPCIÓN EXPRESS (Si quieres ya mismo)

```powershell
# 1. Instalar Vercel
npm install -g vercel

# 2. Login
vercel login

# 3. Desplegar
cd "C:\Users\millo\Downloads\hoja de vida"
vercel --prod

# 4. Abrir en navegador
# Vercel te da la URL automáticamente
```

Luego, en el panel de Vercel:
- Settings → Environment Variables
- Agregar credenciales de BD

---

## 🔗 URLs Resultantes

```
Frontend:  https://busqueda-de-empleo.vercel.app
GitHub:    https://github.com/Rolo0317/busqueda_de_empleo
Repo:      Ya está aquí ✅
```

---

## 💡 PRÓXIMOS PASOS

1. **Vercel (5 min):** `vercel --prod`
2. **Configurar BD (2 min):** Agregar variables
3. **Prueba (1 min):** Abrir URL
4. **Listo:** Dashboard público y funcionando

---

¿Cuál opción prefieres? **Yo recomiendo Vercel** por:
- ✅ Más fácil (5 minutos)
- ✅ Gratis
- ✅ No requiere tarjeta
- ✅ Se conecta directamente con GitHub

