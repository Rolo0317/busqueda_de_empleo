# Job Application Bot - Magneto.co

Bot de postulacion automatica para Magneto.co usando Python, Selenium y el perfil real del navegador del usuario. Por defecto usa Microsoft Edge porque ya viene instalado en Windows. El bot asume que la sesion de Google/Magneto ya esta iniciada en ese navegador, por eso no maneja login manual.

## Estructura

```text
job_bot/
|-- .env
|-- main.py
|-- config.py
|-- requirements.txt
|-- browser/
|   `-- driver.py
|-- platforms/
|   |-- base.py
|   `-- magneto.py
|-- services/
|   |-- searcher.py
|   |-- applicant.py
|   |-- tracker.py
|   `-- question_answerer.py
`-- models/
    `-- job_offer.py
```

## Configuracion

El archivo `.env` guarda las variables sensibles y rutas locales:

```env
MAGNETO_SEARCH_KEYWORDS=Full Stack Developer,Frontend Developer,Backend Developer,React Developer,Node.js Developer,JavaScript Developer,TypeScript Developer,Software Engineer
TARGET_LOCATIONS=Colombia,Bogota,Medellin,Remoto LATAM,Remoto Worldwide
PRIORITY_SKILLS=React,Next.js,Node.js,TypeScript,JavaScript,APIs,MongoDB,SQL,AWS,Docker,IA,Automatizacion
MAGNETO_CITY=Bogota
MAX_OFFERS=30
WAIT_SECONDS=3
LOGIN_WAIT_SECONDS=180
LOOP_INTERVAL_SECONDS=300
MIN_MATCH_SCORE=70
RUN_CONTINUOUSLY=true
CV_PATH=C:\Users\millo\Downloads\hoja de vida\cv_danilo.html
BROWSER=edge
CHROME_USER_DATA_DIR=C:\Users\millo\AppData\Local\Google\Chrome\User Data
CHROME_PROFILE_DIRECTORY=Default
EDGE_USER_DATA_DIR=C:\Users\millo\AppData\Local\Microsoft\Edge\User Data
EDGE_PROFILE_DIRECTORY=Default
EDGE_BINARY_PATH=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe
EDGE_BOT_USER_DATA_DIR=C:\Users\millo\Downloads\hoja de vida\job_bot\edge_bot_profile
ALLOW_BOT_PROFILE_FALLBACK=false
```

Las credenciales MySQL se leen desde `..\magneto_job_system\.env` y, si hace falta, desde el `.env` raiz heredado. No dupliques secretos en este archivo.

Nota: el bot normaliza tildes para comparar ciudad, asi que `Bogota`, `Bogota, D.C.` y `Bogota D.C.` son opciones validas si Magneto cambia el texto visible.

## Instalacion

```powershell
cd "C:\Users\millo\Downloads\hoja de vida\job_bot"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

El bot usa `EDGE_USER_DATA_DIR`, tu perfil real de Edge, para reutilizar la sesion de Google/Magneto. Cierra todas las ventanas de Edge antes de ejecutar el bot, porque Selenium no puede abrir un perfil que ya esta en uso. Si prefieres usar un perfil separado, cambia `ALLOW_BOT_PROFILE_FALLBACK=true` e inicia sesion una vez en la ventana automatizada.

## Ejecucion

Opcion recomendada:

```powershell
.\run_bot.ps1
```

Este script cierra procesos residuales de Edge antes de iniciar, porque el perfil real no se puede abrir si Edge quedo activo en segundo plano.

O manual:

```powershell
python main.py
```

El bot:

1. Carga configuracion desde `.env`.
2. Abre Edge con el perfil real del usuario.
3. Si Magneto no tiene sesion activa, abre `Iniciar sesion`, intenta elegir Google y espera hasta `LOGIN_WAIT_SECONDS` para que termines el acceso.
4. Busca ofertas en Magneto por cada keyword.
5. Si una URL de busqueda no existe, usa la pagina de empleos por ciudad y filtra las tarjetas por keyword.
6. Filtra ofertas por ciudad.
7. Calcula compatibilidad segun cargo, skills, ubicacion, modalidad, seniority y salario.
8. Descarta ofertas por debajo de `MIN_MATCH_SCORE`.
9. Evita postular de nuevo a URLs ya registradas.
10. Intenta hacer clic en `Aplicar` o `Postularme`.
11. Adjunta el CV si aparece un campo de archivo.
12. Registra cada resultado en MySQL para verlo en el dashboard web.
13. Espera `LOOP_INTERVAL_SECONDS` y repite si `RUN_CONTINUOUSLY=true`.

## Seguimiento en MySQL y Dashboard

El bot Python escribe en las mismas tablas que usa `magneto_job_system`:

```text
companies | jobs | applications | searches | skills | job_skills | logs
```

Estados principales:

- `applied`: el bot encontro el boton de postulacion y pudo avanzar.
- `discarded`: la compatibilidad estuvo por debajo del minimo.
- `no_available`: no se encontro boton de aplicar o postular.
- `error`: ocurrio una excepcion durante esa oferta.

Para ver estadisticas, inicia el dashboard desde `magneto_job_system`:

```powershell
npm run dashboard
```

Abre `http://localhost:3000`.

## Plataformas

Estado actual:

- Magneto: funcional para busqueda, scoring, deduplicacion y postulacion basica.
- LinkedIn, Computrabajo, Indeed, Torre, Glassdoor, Wellfound, GetOnBoard, RemoteOK y WeWorkRemotely: pendientes como conectores independientes. La arquitectura permite agregarlos implementando `BasePlatform`, sin tocar el nucleo.

Nota: algunas plataformas pueden bloquear automatizaciones o requerir pasos manuales/captcha. El bot debe respetar esas barreras y registrar `no disponible` o `error` si no puede completar una postulacion.

## Guia del proyecto

Principios obligatorios:

- Clean Code: nombres descriptivos, funciones pequenas y comentarios solo si ayudan.
- DRY: la logica comun vive en servicios reutilizables.
- SOLID: `BasePlatform` define la interfaz, cada plataforma implementa `search()` y `apply()`, y los servicios reciben dependencias por inyeccion.

Responsabilidades:

- `config.py`: carga `.env` con `pydantic-settings`.
- `browser/driver.py`: configura Edge/Chrome y su driver.
- `platforms/base.py`: contrato comun para plataformas.
- `platforms/magneto.py`: logica especifica de Magneto.
- `services/searcher.py`: orquesta busquedas por varias palabras clave.
- `services/applicant.py`: decide si postula y maneja errores por oferta.
- `services/tracker.py`: persiste empresas, vacantes y aplicaciones en MySQL.
- `models/job_offer.py`: modelo de datos de una oferta.

Para agregar otra plataforma, crea un archivo nuevo en `platforms/`, implementa `BasePlatform`, y conecta esa clase desde `main.py` o desde una futura fabrica de plataformas.
