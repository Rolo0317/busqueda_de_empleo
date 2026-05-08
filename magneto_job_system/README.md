# Magneto Job System

Sistema autonomo de busqueda y postulacion laboral para Magneto365 usando Node.js, Playwright, Express, MySQL y dashboard web con Tailwind.

## Estado

- Magneto365: implementado con busqueda por input real en `https://www.magneto365.com/co/trabajos/buscar`.
- Dashboard: implementado con metricas, vacantes, busquedas y logs en tiempo real.
- MySQL: esquema completo con tablas, indices y relaciones.
- Navegador: Playwright persistent context reutilizando perfil real.

## Importante Sobre Chrome

El `.env` queda configurado para Chrome real:

```env
BROWSER_CHANNEL=chrome
USER_DATA_DIR=C:\Users\millo\AppData\Local\Google\Chrome\User Data
PROFILE_DIRECTORY=Default
```

Si prefieres Edge, cambia a:

```env
BROWSER_CHANNEL=msedge
USER_DATA_DIR=C:\Users\millo\AppData\Local\Microsoft\Edge\User Data
PROFILE_DIRECTORY=Default
```

## Instalacion

```powershell
cd "C:\Users\millo\Downloads\hoja de vida\magneto_job_system"
npm install
```

Configura MySQL local en `.env` o usa el `.env` raiz heredado:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=job_bot
```

Si `DB_PASSWORD` esta vacio, el sistema usa `Sql_password` del `.env` raiz. Esto permite que Node, Python y MySQL Workbench apunten a la misma base sin duplicar secretos.

Inicializa base de datos:

```powershell
npm run init-db
```

## Ejecutar Dashboard

```powershell
npm run dashboard
```

Abre:

```text
http://localhost:3000
```

## Ejecutar Bot

Cierra Edge/Chrome antes de ejecutar para que Playwright pueda abrir el perfil real.

```powershell
npm run bot
```

El bot:

1. Abre el perfil real del navegador.
2. Entra a `https://www.magneto365.com/co/trabajos/buscar`.
3. Detecta `input[name="search"]`.
4. Escribe keywords configuradas.
5. Extrae tarjetas de vacantes.
6. Abre detalle de cada vacante.
7. Calcula score de compatibilidad.
8. Guarda todo en MySQL.
9. Si score >= 70, intenta aplicar.
10. Repite cada 5 minutos.

## Estructura

```text
magneto_job_system/
|-- bot/
|-- scrapers/
|-- database/
|-- dashboard/
|-- services/
|-- utils/
|-- logs/
|-- server.js
|-- package.json
|-- .env
|-- .env.example
```

## Tablas

- `companies`
- `jobs`
- `applications`
- `searches`
- `skills`
- `job_skills`
- `logs`

## Seguridad

- Credenciales solo en `.env`.
- Sin passwords hardcodeados.
- No automatiza login de Google.
- Reutiliza sesion existente del navegador.
- Si Magneto muestra captcha o bloqueo, registra error y continua.
