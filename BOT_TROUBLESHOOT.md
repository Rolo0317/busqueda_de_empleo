# 🔴 BOT NO ENCIENDE - DIAGNOSIS Y SOLUCIÓN

## Problema Identificado

El bot no puede iniciar porque **MySQL requiere una contraseña que no tenemos configurada**.

### Estado Actual ✓
- ✅ MySQL **ESTÁ CORRIENDO** (MySQL97 servicio activo)
- ✅ Base de datos **EXISTE** (job_bot creada)  
- ✅ Tablas **EXISTEN** (68 aplicaciones registradas)
- ❌ **CONTRASEÑA INCORRECTA** o **NO CONFIGURADA**

### Error Exacto
```
Access denied for user 'root'@'localhost' (using password: YES)
Error Code 1045 MySQL Authentication Failure
```

---

## 🚀 SOLUCIÓN RÁPIDA (3 Minutos)

### Opción A: Ejecutar Script de Reset (RECOMENDADO)

```powershell
# PASO 1: Abre PowerShell COMO ADMINISTRADOR
# PASO 2: Ve a la carpeta
cd "C:\Users\millo\Downloads\hoja de vida"

# PASO 3: Ejecuta el script
.\reset_mysql.ps1

# PASO 4: Espera a que termine (2-3 min)
# Verás: "✓ Conexión exitosa!"
```

**Lo que hace el script:**
1. Detiene MySQL
2. Lo inicia en modo "sin contraseña"
3. Resetea la contraseña a `admin123`
4. Reinicia MySQL normalmente
5. Verifica que funciona

---

### Opción B: Reseteo Manual (Si el script no funciona)

#### En Windows CMD (COMO ADMINISTRADOR):

```bash
# 1. Detener MySQL
net stop MySQL97

# 2. Iniciar sin contraseña
cd "C:\Program Files\MySQL\MySQL Server 9.7\bin"
mysqld --skip-grant-tables

# (Deja esta ventana abierta y abre OTRA ventana CMD como admin)
```

#### En NUEVA ventana CMD (COMO ADMINISTRADOR):

```bash
# 3. Conectar a MySQL sin contraseña
cd "C:\Program Files\MySQL\MySQL Server 9.7\bin"
mysql -u root

# 4. En la consola MySQL, escribe (línea por línea):
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED BY 'admin123';
EXIT;

# 5. Vuelve a la primera ventana y presiona Ctrl+C

# 6. Reinicia el servicio
net start MySQL97
```

---

## ✏️ Configurar el Bot

Una vez que la contraseña esté reseteada:

### Paso 1: Edita `.env`

Abre: `job_bot/.env`

Cambia esta línea:
```
DB_PASSWORD=password
```

Por esta:
```
DB_PASSWORD=admin123
```

Guarda el archivo.

### Paso 2: Inicia el Bot

```powershell
cd "C:\Users\millo\Downloads\hoja de vida\job_bot"
.\run_bot.ps1
```

---

## ✓ Verifica que Funciona

Deberías ver en la terminal:
```
[2026-05-09 14:30:00] INFO: ================================================================================
[2026-05-09 14:30:00] INFO: INICIANDO BOT DE EMPLEO
[2026-05-09 14:30:00] INFO: ================================================================================
[2026-05-09 14:30:05] INFO: ✅ Login verificado al inicio
[2026-05-09 14:30:10] INFO: Iniciando ciclo #1
```

Si ves esto, ¡**EL BOT ESTÁ FUNCIONANDO! ✅**

---

## 🆘 Si Nada Funciona

### Opción C: Reinstalar MySQL (Nuclear)

```bash
# 1. Ve a Panel de Control → Programas → Desinstalar
# 2. Busca "MySQL 9.7" y desinstálalo
# 3. Descarga MySQL 9.0 Community Server: 
#    https://dev.mysql.com/downloads/mysql/
# 4. Instala y recuerda la contraseña que ELIJAS
# 5. Actualiza .env con esa contraseña
```

### Opción D: Ver Registros de Error

```powershell
# Ver logs de MySQL
Get-Content "C:\ProgramData\MySQL\MySQL Server 9.7\Data\*.err" -Tail 50
```

---

## 📋 Checklist

- [ ] Ejecuté `.\reset_mysql.ps1` O reseté manualmente
- [ ] Edité `job_bot/.env` y puse `DB_PASSWORD=admin123`
- [ ] Ejecuté `.\run_bot.ps1`
- [ ] Veo logs del bot en la terminal
- [ ] El bot comienza a postularse

---

## 💡 Información Técnica

**Por qué pasó esto:**
- MySQL fue instalado con una contraseña pero no se guardó en `.env`
- El bot nunca pudo verificar conexión la primera vez
- Sin conexión a BD, el bot no puede funcionar

**Por qué el reset funciona:**
- Modo `--skip-grant-tables` permite acceso sin contraseña
- Reseteamos la contraseña a algo que SÍ sabemos
- Actualizamos `.env` para que coincida
- Listo ✅

---

## Contacto/Help

Si el script falla, lo más probable es que necesites ejecutar como administrador:

```powershell
# En PowerShell (NO como admin):
Start-Process PowerShell -ArgumentList "-NoExit", "-Command", "& .\reset_mysql.ps1" -Verb RunAs

# Eso abrirá una NUEVA ventana con permisos de admin
```

---

**Hora: 2026-05-09 14:35**  
**Última Actualización: Auto-generado**
