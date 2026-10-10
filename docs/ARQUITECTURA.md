# Hoja de vida y bot de postulación

Tres piezas que comparten un solo perfil (`job_bot/candidate_profile.json`):

- **CV web y PDF** — `cv_builder/` genera `sitio/index.html` y los PDF en tu PC (necesita el perfil privado y Chromium). `sitio/` se versiona y Vercel lo publica en `/`.
- **Bot de postulación** — `job_bot/` busca ofertas en Magneto y Computrabajo, contesta los cuestionarios desde el perfil y postula. Registra todo en Supabase.
- **Panel** — `frontend/` (React + Vite + TypeScript) en Vercel, en `/panel`. Habla directo con Supabase: login con Supabase Auth y datos por las funciones `public.empleo_*`.
- **Agente** — `job_bot/agente.py` corre en la PC, escucha las órdenes del botón y lanza el bot.

## Datos en Supabase

Proyecto **SurIA**, esquema propio **`empleo`** (no se mezcla con las tablas de SurIA). Las tablas tienen RLS sin políticas y el esquema no está expuesto: todo pasa por funciones `security definer` que exigen que el usuario esté en `empleo.operators`. La migración está en `supabase/migrations/`.

```
Panel (Vercel) --rpc--> public.empleo_solicitar_corrida --> empleo.bot_runs (pending)
Agente (PC)    --rpc--> empleo_tomar_corrida -> lanza main.py -> empleo_reportar_corrida
Bot (PC)       --rpc--> empleo_registrar_oferta / empleo_registrar_pregunta
```

## Estructura del bot (`job_bot/`)

Cada carpeta tiene una sola responsabilidad. El flujo de un ciclo las recorre en orden:

```
main.py ─▶ navegador/ ─▶ plataformas/ ─▶ postulacion/ ─▶ respuestas/ ─▶ almacenamiento/
            (Edge)        (buscar,         (analizar,      (contestar      (guardar en
                          login)           filtrar,        cuestionarios)   Supabase)
                                           postular)
```

| Carpeta | Qué contiene |
|---|---|
| `main.py` | Arranque y ciclo continuo; `ControlDeSesiones` reintenta las plataformas sin sesión (máx. 1 vez por hora) |
| `agente.py` | Escucha el botón del panel (Supabase) y lanza `main.py` con un tope |
| `config.py` | Ajustes del `.env` (Pydantic) y carga del perfil |
| `navegador/` | Playwright enganchado por CDP al Edge del bot; una pestaña por plataforma |
| `plataformas/` | `magneto.py`, `computrabajo.py`, `login_magneto.py` (código al correo), `cuestionario*.py`, `lectura_oferta.py`, `registry.py` (agregar una bolsa = una línea) |
| `postulacion/` | `searcher.py` (busca), `analyzer.py` (puntaje), `relevancia_cargo.py` (¿es mi oficio?), `zona.py` (ciudad), `applicant.py` (decide y postula; resume los descartes por motivo) |
| `respuestas/` | `question_answerer.py` (decide), `respuestas_locales.py` (redacta desde el perfil), `eleccion_opciones.py` (elige entre opciones), `anios_tecnologia.py` (años por tecnología), `criterio_situacional.py`, `ai_answerer.py` (Gemini/Groq opcional) |
| `almacenamiento/` | `tracker.py` (protocolo y MySQL), `tracker_supabase.py`, `supabase_cliente.py` (sesión, RPC y reintentos), `esquema_mysql.sql` |
| `utilidades/` | `aviso.py` (aviso de Windows), `lector_codigos.py` (códigos de Gmail por IMAP), `url_utils.py` |
| `modelos/` | `job_offer.py` (la oferta) |
| `herramientas/` | `prueba_una_oferta.py`, `prueba_en_vivo.py`: pruebas manuales que sí postulan |
| `logs/` | `bot.log` rotado (5 MB × 3); fuera de git |
| `tests/` | Pruebas sin navegador ni base de datos |

Fuera del bot: `scripts/` (los `.ps1`), `frontend/` (panel), `cv_builder/` → `sitio/` (hoja de vida, con la foto en `cv_builder/static/`), `supabase/migrations/`.

## Uso diario

```powershell
.\scripts\abrir_navegador_bot.ps1   # la primera vez: inicia sesión en Magneto y Computrabajo
.\scripts\ejecutar_bot.ps1          # corre en ciclos cada LOOP_INTERVAL_SECONDS
.\scripts\ver_vacantes.ps1          # panel en local: http://localhost:5173/panel/
```

No cierres la ventana de Edge del bot: el bot trabaja dentro de ella. El log queda en `job_bot/logs/bot.log`.

## Cómo postula

1. **Busca** en cada plataforma con `MAGNETO_SEARCH_KEYWORDS`.
2. **Analiza** cada oferta (`analyzer.py`): salario mínimo, ubicación, habilidades. Por debajo de `MIN_MATCH_SCORE` se descarta.
3. **Postula** (`applicant.py`), saltando las ya registradas y respetando `MAX_OFFERS`.
   - *Magneto*: pulsa Aplicar, contesta el cuestionario y confirma. El veredicto final lo da su API (`jobs/v1/jobs/apply`): un 422 "ya ha sido aplicada" cuenta como postulada.
   - *Computrabajo*: navega a la URL de `data-href-offer-apply` (no pulsa, para no caer en "guardar"), contesta las preguntas de selección y confirma por la ruta `/candidate/postapply`.
4. **Registra** oferta, estado y cada pregunta contestada en Supabase (o MySQL con `DB_BACKEND=mysql`).

Una postulación solo se marca `applied` si la plataforma la confirma.

## Respuestas a cuestionarios

`question_answerer.py` decide; `respuestas_locales.py` redacta desde el perfil; `eleccion_opciones.py` escoge entre opciones. Reglas que no se negocian:

- Nunca afirmar un título, un empleo o un nivel que el perfil no respalda.
- Nunca negar una habilidad que el perfil sí registra.
- Contestar en el idioma de la pregunta.
- Respetar el límite de caracteres de cada campo.

La IA (Gemini o Groq) solo se usa si hay clave y ninguna regla local aplica.

## Pruebas

```powershell
cd job_bot
.\.venv\Scripts\python.exe tests\test_respuestas_reales.py
.\.venv\Scripts\python.exe tests\test_tope_postulaciones.py
```

`test_respuestas_reales.py` usa preguntas que las empresas hicieron de verdad. Cada error de respuesta que aparezca en una corrida debe entrar ahí como caso nuevo.

## Configuración

Copia `.env.example` como `.env` en la raíz y rellénalo. El `.env` nunca se sube a git, y tampoco `job_bot/.edge-bot/`, que guarda las sesiones iniciadas.
