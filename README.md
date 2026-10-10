# Bot de búsqueda de empleo

Busca ofertas en **Magneto** y **Computrabajo** (Colombia), descarta las que no encajan con tu perfil, contesta los cuestionarios con tus datos reales y se postula por ti. Guarda todo en **Supabase** para no repetir ofertas y para que veas en el **panel web** qué se envió.

Trabaja sobre **tu propio Edge**, con tus sesiones iniciadas. No guarda las contraseñas de Magneto ni de Computrabajo.

## Qué hace

- Busca con tus palabras clave en varias páginas de resultados de cada plataforma.
- Descarta cargos que no son tu oficio, por debajo de tu nivel, con tecnologías que no manejas o en otra ciudad (si no aceptas reubicarte).
- Responde preguntas abiertas, de opción múltiple y de sí/no desde tu perfil. **Nunca inventa experiencia:** si no manejas una tecnología, lo dice.
- Confirma que cada postulación quedó enviada antes de darla por hecha.
- Inicia sesión solo en Magneto: pide el código al correo y lo lee de Gmail.
- Panel web en Vercel con cifras, gráfica de actividad, vacantes y un botón para lanzar el bot.

## Antes de usarlo

- **Tu perfil es lo que el bot dice de ti.** Escribe en `candidate_profile.json` solo lo que puedas defender en una entrevista.
- **Empieza en modo supervisado** (`SUPERVISED_APPLY=true`): el bot te pregunta antes de cada postulación. Una postulación enviada no se puede retirar.
- Úsalo con moderación y respeta los términos de cada plataforma. Las pruebas psicotécnicas las presentas tú.

## Instalación (Windows 10/11, Edge, Python 3.11+)

```powershell
git clone https://github.com/Rolo0317/busqueda_de_empleo.git
cd busqueda_de_empleo
.\scripts\instalar.ps1
```

Crea el entorno virtual, instala dependencias, crea tu `.env` y tu perfil desde las plantillas y corre las pruebas. Se puede repetir: nunca sobrescribe tu configuración. Si PowerShell bloquea los scripts, corre una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## Configuración

**`.env`** (en la raíz; plantilla en `.env.example`). Lo principal:

| Variable | Para qué sirve |
|---|---|
| `SUPABASE_EMAIL`, `SUPABASE_PASSWORD` | Tu usuario del panel; el bot inicia sesión con él para guardar los datos |
| `MAGNETO_SEARCH_KEYWORDS` | Palabras clave separadas por comas |
| `PLATFORMS` | `magneto`, `computrabajo` o ambas |
| `CV_PATH` | PDF de tu hoja de vida que se adjunta al postular |
| `MIN_MATCH_SCORE` | Puntaje mínimo (0–100) para postular |
| `MAX_OFFERS` | Tope de postulaciones por corrida (`0` = sin tope) |
| `SUPERVISED_APPLY` | `true`: pregunta antes de cada postulación |
| `MAGNETO_EMAIL`, `CORREO_CODIGOS_CLAVE_APP` | Login automático de Magneto (contraseña de aplicación de Gmail) |
| `DB_BACKEND` | `supabase` (por defecto) o `mysql` si prefieres una base local |

**`job_bot/candidate_profile.json`**: tu perfil, a partir de `candidate_profile.example.json`. Datos de contacto, años por tecnología (`experience_years`; pon `0` en lo que no manejas), experiencia, estudios, textos para preguntas abiertas (`short_texts`, `relatos`) y temas que nunca se contestan (`never_answer_keywords`). No se sube a git.

## Uso

```powershell
.\scripts\abrir_navegador_bot.ps1   # abre el Edge del bot (la primera vez inicia sesión en Magneto y Computrabajo)
.\scripts\ejecutar_bot.ps1          # busca y postula en ciclos
```

No cierres la ventana de Edge del bot: trabaja dentro de ella. El resumen de cada ciclo, con los motivos de descarte, queda en `job_bot\logs\bot.log`.

**Desde el panel web** (Vercel, en `/panel`): el botón *Ejecutar* deja una orden en Supabase y el agente de tu PC la toma.

```powershell
.\scripts\iniciar_agente.ps1             # deja la PC escuchando el panel
.\scripts\iniciar_agente.ps1 -AlIniciar  # y además arranca solo con Windows
```

**Herramientas de prueba** (sí envían postulaciones reales):

```powershell
cd job_bot
.venv\Scripts\python.exe herramientas\prueba_una_oferta.py <url-de-la-oferta>
.venv\Scripts\python.exe herramientas\prueba_en_vivo.py 3
```

## Pruebas

```powershell
Get-ChildItem job_bot\tests\test_*.py | ForEach-Object { job_bot\.venv\Scripts\python.exe $_.FullName }
```

No usan tu cuenta, tu navegador ni tu base de datos.

## Estructura

```
scripts/                 Todo lo que se ejecuta a mano (.ps1)
  instalar.ps1             Instalación en un equipo nuevo
  abrir_navegador_bot.ps1  Abre el Edge del bot (puerto 9222)
  ejecutar_bot.ps1         Lanza el bot
  iniciar_agente.ps1       Escucha el botón del panel web
  ver_vacantes.ps1         Panel web en local
  reset_mysql.ps1          Solo para quien use MySQL

job_bot/                 El bot (Python + Playwright)
  main.py                  Ciclo: buscar -> filtrar -> responder -> postular
  agente.py                Toma las órdenes del panel y lanza main.py
  config.py                Lee el .env y el perfil
  navegador/               Conexión con el Edge del bot
  plataformas/             Magneto, Computrabajo, login y cuestionarios
  postulacion/             Búsqueda, análisis, filtro de cargos, zona y postulación
  respuestas/              Cómo se contesta cada pregunta del cuestionario
  almacenamiento/          Dónde se guarda todo (Supabase o MySQL)
  utilidades/              Avisos de Windows, códigos del correo, URL
  modelos/                 La oferta de empleo
  herramientas/            Scripts de prueba manual
  logs/                    Registros de cada corrida (no se suben a git)
  tests/                   Pruebas automáticas

frontend/                Panel web (React + Vite), publicado en Vercel en /panel
cv_builder/              Genera la hoja de vida (HTML y PDF) desde el perfil
sitio/                   Hoja de vida generada; Vercel la publica en /
supabase/migrations/     Esquema de la base de datos
docs/                    Arquitectura y decisiones
```

Más detalle en [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md).

## Privacidad

Nunca subas tu `.env`, tu `candidate_profile.json`, la carpeta `job_bot/.edge-bot/` (tiene tus sesiones) ni `job_bot/logs/`. Ya están en `.gitignore`.

## Problemas frecuentes

| Síntoma | Solución |
|---|---|
| "No hay navegador escuchando en el puerto 9222" | Corre primero `.\scripts\abrir_navegador_bot.ps1` |
| "No existe el perfil del candidato" | Copia `candidate_profile.example.json` como `candidate_profile.json` |
| Una plataforma "sin sesión por ahora" | El bot la reintenta cada hora; en Magneto inicia sesión solo si configuraste el login automático |
| "No se pudo iniciar sesión en Supabase" | Revisa `SUPABASE_EMAIL` y `SUPABASE_PASSWORD` en `.env` |
| El panel dice "PC desconectada" | Corre `.\scripts\iniciar_agente.ps1` y no cierres la ventana |
| Se salta casi todas las ofertas | Mira los motivos de descarte en el log; ajusta `cargos` en tu perfil o baja `MIN_MATCH_SCORE` |
