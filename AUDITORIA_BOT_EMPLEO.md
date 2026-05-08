# Auditoria y Migracion del Bot de Empleo

Fecha: 2026-05-08

## Objetivo

Unificar el bot de postulacion y el dashboard en una sola fuente de verdad: MySQL. El bot Python conserva el flujo que responde preguntas durante la aplicacion; el dashboard Node muestra estadisticas y resultados desde la misma base `job_bot`.

## Resultado

- El archivo `seguimiento_empleo.xlsx` fue migrado a MySQL y eliminado.
- `job_bot` ya no depende de Excel ni de `openpyxl`.
- `job_bot` escribe en las tablas `companies`, `jobs`, `applications`, `skills` y `job_skills`.
- `magneto_job_system` sigue sirviendo el frontend y lee la misma base.
- Las credenciales se toman de los `.env` del proyecto sin duplicar secretos.

## Principios Aplicados

- Clean Code: nombres explicitos, responsabilidades claras y persistencia encapsulada en `MySqlApplicationTracker`.
- DRY: se retiro el seguimiento paralelo en Excel; MySQL queda como unico almacenamiento operativo.
- SOLID: `JobApplicant` depende de la abstraccion `ApplicationTracker`, no de una clase concreta.

## Cambios Principales

- `job_bot/services/tracker.py`: reemplazado por tracker MySQL.
- `job_bot/main.py`: usa `MySqlApplicationTracker`.
- `job_bot/services/applicant.py`: recibe la interfaz `ApplicationTracker`.
- `job_bot/config.py`: carga `job_bot/.env`, `magneto_job_system/.env` y `.env` raiz.
- `job_bot/requirements.txt`: reemplaza `openpyxl` por `mysql-connector-python`.
- `magneto_job_system/utils/config.js`: carga el `.env` raiz como respaldo para MySQL.
- `magneto_job_system/services/jobRepository.js`: corrige la consulta del dashboard para MySQL y sanea paginacion.
- `magneto_job_system/server.js`: evita que errores de API tumben el servidor.
- `magneto_job_system/dashboard/public/app.js`: lee el nuevo alias de prioridad alta.
- `job_bot/.env`: se elimino `EXCEL_PATH`.

## Base de Datos

Base creada en MySQL:

```text
job_bot
```

Tablas verificadas:

```text
applications
companies
job_skills
jobs
logs
searches
skills
```

Conteo posterior a migracion:

```text
jobs: 98
applications: 67
applied: 66
discarded: 32
```

## Pruebas Ejecutadas

```powershell
npm run init-db
npm run check
.\.venv\Scripts\python.exe -m py_compile main.py config.py browser\driver.py models\job_offer.py platforms\base.py platforms\magneto.py services\analyzer.py services\applicant.py services\question_answerer.py services\searcher.py services\tracker.py
```

Tambien se hizo una escritura temporal desde Python a MySQL y luego se elimino la fila temporal.

## Frontend

Dashboard:

```text
http://localhost:3000
```

Estado validado:

```text
online | jobs=98 | applied=66
```

API de estado:

```text
http://localhost:3000/api/status
```

## Operacion

Encender dashboard:

```powershell
cd "C:\Users\millo\Downloads\hoja de vida\magneto_job_system"
npm run dashboard
```

Encender bot Python:

```powershell
cd "C:\Users\millo\Downloads\hoja de vida\job_bot"
.\run_bot.ps1
```

## Nota

El dashboard Node puede buscar y aplicar ofertas simples, pero el flujo recomendado para postulaciones con preguntas es `job_bot`, porque contiene `CandidateQuestionAnswerer`.
