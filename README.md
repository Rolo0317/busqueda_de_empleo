# Bot de búsqueda de empleo

Busca ofertas en **Magneto** y **Computrabajo** (Colombia), descarta las que no encajan con tu perfil, contesta los cuestionarios de postulación con tus datos reales y se postula por ti. Guarda todo en Supabase para no repetir ofertas y para que veas en el panel web qué se envió.

Funciona sobre **tu propio navegador Edge**, con tu sesión iniciada: no guarda tus contraseñas de Magneto ni de Computrabajo.

## Qué hace

- Busca por las palabras clave que configures, en varias páginas de resultados.
- Filtra cargos que no son tu oficio, que están por debajo de tu nivel, que piden tecnologías que no tienes o que quedan en otra ciudad (si no aceptas reubicarte).
- Responde preguntas abiertas, de opción múltiple, desplegables y de "sí/no" a partir de tu perfil. Si no tienes una tecnología, lo dice; nunca inventa experiencia.
- Confirma que la postulación realmente quedó enviada antes de darla por hecha.
- Opcional: usa Gemini o Groq (gratis) para preguntas abiertas que el perfil no cubre.
- Un panel web en Vercel con cifras, gráfica de actividad, vacantes y un botón para lanzar el bot.

## Antes de usarlo

- **Tu perfil es lo que el bot dice de ti.** Todo lo que pongas en `candidate_profile.json` lo afirmará ante las empresas. Escribe solo lo que puedas defender en una entrevista.
- **Empieza en modo supervisado** (`SUPERVISED_APPLY=true`, el valor por defecto): el bot te muestra cada oferta y te pregunta antes de postular. Una postulación enviada no se puede retirar.
- Úsalo con moderación y respeta los términos de uso de cada plataforma.
- El bot no presenta pruebas psicotécnicas ni evaluaciones: esas las haces tú.

## Requisitos

- Windows 10 u 11 con **Microsoft Edge**.
- **Python 3.11** o superior.
- **MySQL 8** o superior.
- Una cuenta en Magneto y/o Computrabajo, con tu hoja de vida cargada.
- Node.js 20+ solo si quieres el panel web o generar tu hoja de vida con `cv_builder`.

## Instalación

```powershell
git clone https://github.com/Rolo0317/busqueda_de_empleo.git
cd busqueda_de_empleo
.\instalar.ps1
```

`instalar.ps1` crea el entorno virtual, instala las dependencias, crea tu `.env` y tu `candidate_profile.json` a partir de las plantillas y corre las pruebas. Puedes volver a correrlo: nunca sobrescribe tu configuración.

Si PowerShell no deja ejecutar scripts, abre PowerShell y corre una vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Luego crea la base de datos:

```powershell
mysql -u root -p < job_bot\database\schema.sql
```

## Configuración

### 1. `.env` (en la raíz)

| Variable | Para qué sirve |
|---|---|
| `DB_BACKEND` | `supabase` (el panel web lo lee) o `mysql` (base local antigua) |
| `SUPABASE_EMAIL`, `SUPABASE_PASSWORD` | Tu usuario del panel; el bot y el agente inician sesión con él |
| `DB_USER`, `DB_PASSWORD`, `DB_NAME` | Conexión a MySQL, solo si `DB_BACKEND=mysql` |
| `MAGNETO_SEARCH_KEYWORDS` | Palabras clave separadas por comas: `analista de datos,python,sql` |
| `PLATFORMS` | `magneto`, `computrabajo` o ambas separadas por coma |
| `CV_PATH` | Ruta completa al PDF de tu hoja de vida |
| `MIN_MATCH_SCORE` | Puntaje mínimo (0–100) para postular a una oferta |
| `MAX_OFFERS` | Tope de postulaciones por corrida; `0` es sin tope |
| `SUPERVISED_APPLY` | `true`: te pregunta antes de cada postulación |
| `RUN_CONTINUOUSLY`, `LOOP_INTERVAL_SECONDS` | Correr en ciclos y cada cuánto |
| `GEMINI_API_KEY` / `GROQ_API_KEY` | Opcionales, para preguntas abiertas con IA |

### 2. `job_bot/candidate_profile.json`

Es tu perfil. Parte de la plantilla `candidate_profile.example.json` (una persona ficticia) y reemplaza todo:

- **Datos de contacto:** `name`, `email`, `phone`, `city`, `minimum_salary_cop`.
- **`availability`:** modalidades que aceptas; `relocation: false` descarta ofertas presenciales en otras ciudades.
- **`experience_years`:** años por tecnología. Con esto responde "¿cuántos años tienes con X?". Pon `0` en lo que no manejas.
- **`main_skills`, `experience`, `education`, `certifications`.**
- **`short_texts`:** resumen y motivación para preguntas abiertas.
- **`relatos`:** tus historias para preguntas como "describe un pipeline que hayas construido" o "¿tienes título profesional?". Cada una en español (`es`) y, si quieres, en inglés (`en`).
- **`cargos`** (opcional): qué cargos buscas y cuáles descartar. Si no la pones, usa listas pensadas para perfiles de datos y desarrollo.
- **`never_answer_keywords`:** temas sensibles que el bot nunca contesta (salud, deudas…).

Este archivo está en `.gitignore`: no se sube al repositorio.

## Uso

```powershell
.\abrir_navegador_bot.ps1   # abre el Edge del bot
```

La primera vez, **inicia sesión en Magneto y en Computrabajo** en esa ventana. No la cierres: el bot trabaja dentro de ella. La sesión queda guardada en `job_bot\.edge-bot\` para las próximas veces.

```powershell
.\ejecutar_bot.ps1          # busca y postula
```

El resumen de cada ciclo aparece en la consola y en `job_bot\bot.log`.

### Postular a una sola oferta (Magneto)

```powershell
cd job_bot
.venv\Scripts\python.exe prueba_una_oferta.py <url-de-la-oferta>
```

**Sí envía la postulación**, pero solo a esa oferta, mostrando cada pregunta y la respuesta que dio. Sirve para revisar cómo responde el bot después de editar tu perfil.

### Panel web y botón de ejecutar

El panel está publicado en Vercel, en `/panel` del mismo sitio que la hoja de vida. Entras con tu correo y la clave de `SUPABASE_PASSWORD`.

El bot no corre en la nube: necesita tu Edge con las sesiones iniciadas. Por eso el botón **Ejecutar** deja una orden en Supabase y un **agente** en tu PC la toma:

```powershell
.\iniciar_agente.ps1             # deja la PC escuchando el panel
.\iniciar_agente.ps1 -AlIniciar  # y además arranca solo con Windows
```

El agente abre el navegador del bot si está cerrado, corre una sola pasada con el tope que elegiste y va subiendo el estado y el log al panel. Una orden que la PC no toma en 30 minutos caduca, para que un clic viejo no postule cuando prendas el equipo.

Para probar cambios del panel en local: `.er_vacantes.ps1` (http://localhost:5173/panel/).

## Pruebas

```powershell
Get-ChildItem job_bot\tests\test_*.py | ForEach-Object { job_bot\.venv\Scripts\python.exe $_.FullName }
```

No usan tu cuenta, tu navegador ni tu base de datos: corren contra el perfil de ejemplo y páginas locales.

## Estructura

```
instalar.ps1              Instalación en un equipo nuevo
abrir_navegador_bot.ps1   Abre el Edge del bot (puerto 9222)
ejecutar_bot.ps1          Lanza el bot
iniciar_agente.ps1        Deja la PC escuchando el botón del panel web
ver_vacantes.ps1          Panel web en local
reset_mysql.ps1           Restablece la clave de root de MySQL (como administrador)

job_bot/
  main.py                         Ciclo: buscar -> filtrar -> responder -> postular
  config.py                       Lee .env y el perfil
  candidate_profile.example.json  Plantilla del perfil
  browser/navegador.py            Playwright conectado a tu Edge
  platforms/                      Magneto, Computrabajo y sus cuestionarios
  agente.py                       Toma las órdenes del panel y lanza el bot
  services/                       Filtros, respuestas, registro (Supabase o MySQL)
  database/schema.sql             Esquema MySQL antiguo
  tests/                          Pruebas
frontend/                 Panel web (React + Vite), publicado en Vercel en /panel
supabase/migrations/      Esquema `empleo` y sus funciones (proyecto SurIA)
cv_builder/               Genera tu hoja de vida en HTML y PDF desde el perfil -> sitio/
sitio/                    Hoja de vida generada; Vercel la publica tal cual en /
backend/                  Panel Django antiguo sobre MySQL (ya no lo usa el panel web)
```

Detalles de arquitectura en [DOCS.md](DOCS.md).

## Privacidad

Nunca subas al repositorio tu `.env`, tu `candidate_profile.json`, la carpeta `job_bot/.edge-bot/` (tiene tus sesiones iniciadas) ni los `bot.log`. Ya están en `.gitignore`.

## Problemas frecuentes

| Síntoma | Solución |
|---|---|
| "No hay navegador escuchando en el puerto 9222" | Corre primero `.\abrir_navegador_bot.ps1` |
| "No existe el perfil del candidato" | Copia `candidate_profile.example.json` como `candidate_profile.json` |
| Una plataforma "queda fuera de esta corrida" | Se cerró la sesión: vuelve a iniciarla en el Edge del bot |
| "No autorizado" o "No se pudo iniciar sesión en Supabase" | Revisa `SUPABASE_EMAIL` y `SUPABASE_PASSWORD` en `.env` |
| El panel dice "PC desconectada" | Corre `.\iniciar_agente.ps1` y no cierres la ventana |
| Se salta casi todas las ofertas | Revisa las listas `cargos` de tu perfil y baja `MIN_MATCH_SCORE` |
