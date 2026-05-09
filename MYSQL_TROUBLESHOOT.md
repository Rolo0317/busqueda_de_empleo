# Solución: Bot no Enciende - Error de Conexión MySQL

## Problema Identificado
El bot no puede iniciar porque **no puede conectarse a la base de datos MySQL**. 

### Error Exacto
```
mysql.connector.errors.ProgrammingError: 1045 (28000): Access denied for user 'root'@'localhost' 
```

Esto significa que:
- ✅ MySQL **SÍ está corriendo** (servicio MySQL97 activo)
- ❌ La contraseña en `.env` es **incorrecta**
- ❌ Usuario/contraseña no coinciden con la configuración de MySQL

## Soluciones

### Opción 1: Resetear Contraseña de MySQL (Recomendado)

#### En Windows (CMD como Administrador):
```bash
net stop MySQL97
cd "C:\Program Files\MySQL\MySQL Server 9.7\bin"
mysqld --skip-grant-tables
```

En otra ventana CMD (como admin):
```bash
mysql -u root
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED BY 'password123';
EXIT;
```

Luego reinicia el servicio:
```bash
net start MySQL97
```

#### Actualizar .env:
```
DB_PASSWORD=password123
```

---

### Opción 2: Usar MySQL Workbench (Si Está Instalado)

1. Abre MySQL Workbench
2. Click en "+" para crear conexión
3. Prueba con diferentes passwords hasta encontrar la correcta
4. Una vez conectado, edita el usuario root:
   - Right-click en usuario → Edit
   - Cambia la contraseña
5. Actualiza el `.env` con la nueva contraseña

---

### Opción 3: Ver Configuración Actual de MySQL

Crea un archivo `check_mysql_config.ps1`:
```powershell
$mySQLDir = "C:\Program Files\MySQL\MySQL Server 9.7"
$configFile = "$mySQLDir\my.ini"

if (Test-Path $configFile) {
    Get-Content $configFile | Select-String -Pattern "user|password|port"
} else {
    Write-Host "No se encontró my.ini"
}
```

---

### Opción 4: Verificar BD Existe

Una vez que logres acceder a MySQL, verifica que la BD existe:

```sql
CREATE DATABASE IF NOT EXISTS job_bot;
USE job_bot;

SHOW TABLES;
```

Si las tablas no existen, ejecuta el script init:
```bash
mysql -u root -p < database/schema.sql
```

---

## Próximos Pasos

1. **Resetea la contraseña de MySQL** usando una de las opciones arriba
2. **Actualiza el `.env`** con la contraseña correcta
3. **Ejecuta el bot:**
   ```powershell
   cd job_bot
   .\run_bot.ps1
   ```

## Si Nada Funciona

Reinstala MySQL:
1. Desinstala MySQL 9.7 desde Panel de Control
2. Descarga MySQL Community Server: https://dev.mysql.com/downloads/mysql/
3. Instala con contraseña que recuerdes (ej: `admin123`)
4. Actualiza `.env` con esa contraseña

---

## Archivo: job_bot/.env (Actual)

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=password    <- ESTO ES INCORRECTO
DB_NAME=job_bot
```

**Cambia `DB_PASSWORD` al valor correcto cuando lo encuentres.**
