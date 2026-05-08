# 🚀 Desplegar en Vercel (La Forma Más Fácil)

**Vercel** es la forma más fácil y rápida para publicar tu dashboard. Es GRATIS y sin complicaciones.

---

## ⏱️ Tiempo Total: 5 Minutos

### Paso 1: Instalar Vercel CLI (1 minuto)

```powershell
npm install -g vercel
```

### Paso 2: Login en Vercel (1 minuto)

```powershell
vercel login
```

Te pedirá email. Puedes usar tu cuenta de GitHub para login más rápido.

### Paso 3: Desplegar (2 minutos)

```powershell
cd "C:\Users\millo\Downloads\hoja de vida"
vercel --prod
```

Sigue los pasos interactivos:
- **What's your project's name?** → `busqueda-de-empleo`
- **In which directory is your code located?** → `.` (punto)
- **Want to modify these settings?** → `N` (no)
- **Link to existing project?** → `N` (no)

### Paso 4: Esperar Deploy (Automático)

Vercel subirá automáticamente a:
```
https://busqueda-de-empleo.vercel.app
```

### Paso 5: Configurar Base de Datos (1 minuto)

1. Abre el panel de Vercel: https://vercel.com/dashboard
2. Selecciona tu proyecto `busqueda-de-empleo`
3. Settings → Environment Variables
4. Agrega estas variables:

```
DB_HOST     = 192.168.X.X (tu IP local)
DB_PORT     = 3306
DB_USER     = root
DB_PASSWORD = tu_contraseña
DB_NAME     = job_bot
```

5. Haz redeploy: Click en "Redeploy" o:
```powershell
vercel --prod
```

---

## ✅ ¡LISTO!

Tu dashboard está ahora PUBLIC en:
```
https://busqueda-de-empleo.vercel.app
```

Cualquiera puede acceder desde cualquier navegador.

---

## 🔄 Actualizar el Dashboard

Cada vez que hagas cambios:

```powershell
cd "C:\Users\millo\Downloads\hoja de vida"

# Hacer cambios, luego:
git add .
git commit -m "Update dashboard"
git push origin main

# Vercel redeploya automáticamente
```

---

## ⚠️ Notas Importantes

### Base de Datos
- Tu MySQL debe estar accesible desde Vercel
- Si está en local, necesitas exponer MySQL a Internet:
  ```bash
  # En tu computadora, exponer MySQL
  # Esto requiere configuración de firewall/router
  ```
- **Alternativa FÁCIL:** Usar una base de datos en la nube como [PlanetScale](https://planetscale.com) (gratuita)

### API Pública
El dashboard en Vercel tendrá una URL pública, pero:
- ✅ Cualquiera puede ver el dashboard
- ✅ Los datos se cargan desde tu MySQL
- ✅ El bot sigue corriendo en tu computadora

---

## 🆘 Troubleshooting

### Error: "Cannot find module 'express'"

Vercel necesita que instales las dependencias:

```powershell
cd magneto_job_system
npm install
cd ..
vercel --prod
```

### Error de Base de Datos

Si la BD no conecta:
1. Verifica que MySQL está corriendo
2. Verifica variables de entorno en Vercel
3. Verifica que tu firewall permite conexiones externas
4. Usa PlanetScale si está en nube

### ¿Cómo veo los logs?

```powershell
vercel logs  # Ver logs en tiempo real
```

---

## 📊 Resultado Final

```
✅ Dashboard en: https://busqueda-de-empleo.vercel.app
✅ GitHub en:    https://github.com/Rolo0317/busqueda_de_empleo
✅ Bot corriendo en tu computadora
✅ BD MySQL local o en la nube
✅ TODO GRATIS
```

---

## 🎯 Próximos Pasos

1. ✅ Ya lo hiciste: Subir a GitHub
2. ⏳ Ahora: `vercel --prod`
3. 🎉 Resultado: Dashboard público y funcionando

