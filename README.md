# Bot de Búsqueda de Empleo Automatizado

Sistema automatizado de búsqueda y postulación de empleos en Magneto365 con dashboard en tiempo real.

![Estado](https://img.shields.io/badge/estado-activo-brightgreen)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Node.js](https://img.shields.io/badge/Node.js-18+-green)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🎯 Características Principales

- ✅ **Búsqueda Automatizada** en Magneto365
- ✅ **Análisis Inteligente** de ofertas con puntuación de coincidencia
- ✅ **Postulación Automática** a ofertas calificadas
- ✅ **Respuesta de Preguntas** durante el proceso de aplicación
- ✅ **Dashboard en Tiempo Real** con estadísticas
- ✅ **Base de Datos MySQL** para persistencia
- ✅ **Actualización en Vivo** con Server-Sent Events (SSE)
- ✅ **Renovación Automática** de sesión
- ✅ **Logging Detallado** para debugging

---

## 📋 Requisitos Previos

### Obligatorio:
- **Windows 10/11** (compatible con Linux con ajustes)
- **Python 3.10+** 
- **Node.js 18+**
- **MySQL 8.0+**
- **Microsoft Edge** (navegador principal) o **Chrome**
- **Git** (para clonar el repositorio)

### Cuenta Magneto365:
- Una cuenta activa en [magneto365.com](https://www.magneto365.com)
- Sesión iniciada en tu navegador (el bot reutilizará esta sesión)

---

## 🚀 Instalación Rápida

### 1. Clonar el Repositorio

```bash
git clone https://github.com/Rolo0317/busqueda_de_empleo.git
cd busqueda_de_empleo
```

### 2. Configurar Base de Datos MySQL

```bash
# En terminal de MySQL o MySQL Workbench
CREATE DATABASE job_bot;
CREATE USER 'bot_user'@'localhost' IDENTIFIED BY 'tu_contraseña_segura';
GRANT ALL PRIVILEGES ON job_bot.* TO 'bot_user'@'localhost';
FLUSH PRIVILEGES;
```

O usar el script automático de Node:

```bash
cd magneto_job_system
npm run init-db
cd ..
```

### 3. Configurar Python

```bash
cd job_bot
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Copiar y completar los archivos `.env`:

```bash
# Python Bot
cp job_bot\.env.example job_bot\.env
# Editar con tus valores

# Node Dashboard  
cp magneto_job_system\.env.example magneto_job_system\.env
# Editar con tus valores
```

### 5. Configurar Node.js

```bash
cd magneto_job_system
npm install
npm run init-db
cd ..
```

### 6. Copiar CV

Copiar tu CV a:
```
job_bot/cv.pdf
```

### 7. Crear Perfil de Candidato

Crear archivo `job_bot/candidate_profile.json`:

```json
{
  "name": "Tu Nombre",
  "email": "tu@email.com",
  "phone": "+57 123 4567890",
  "location": "Bogota, Colombia",
  "experience_years": 5,
  "education": "Ingeniería en Sistemas",
  "title": "Full Stack Developer",
  "bio": "Desarrollador con experiencia en React y Node.js"
}
```

---

## 🎮 Uso

### Opción 1: Iniciar el Bot (Postulación Automática)

```bash
cd job_bot
.\run_bot.ps1
```

**Primer paso:** El bot abrirá Edge y esperará que **inicie sesión en Magneto365** (máximo 180 segundos).

El bot entonces:
1. ✅ Buscará ofertas con tus palabras clave
2. ✅ Analizará cada oferta
3. ✅ Aplicará automáticamente si cumple criterios
4. ✅ Responderá preguntas si es necesario
5. ✅ Guardará todo en MySQL
6. ✅ Renovará la sesión cada 5 ciclos

### Opción 2: Iniciar el Dashboard (Visualización)

```bash
cd magneto_job_system
npm run dashboard
```

Luego abre en tu navegador:
```
http://localhost:3000
```

El dashboard mostrará:
- 📊 Total de ofertas encontradas
- ✅ Ofertas aplicadas
- 📈 Estadísticas en tiempo real
- 🔍 Búsqueda por palabras clave
- 📋 Historial de aplicaciones

### Opción 3: Ambos Simultáneamente

Terminal 1:
```bash
cd magneto_job_system
npm run dashboard
```

Terminal 2:
```bash
cd job_bot
.\run_bot.ps1
```

---

## 🔧 Configuración Avanzada

### Palabras Clave de Búsqueda

En `job_bot/.env`:
```env
MAGNETO_SEARCH_KEYWORDS=React Developer,Full Stack,Node.js,TypeScript Engineer
```

### Filtros Mínimos

```env
MIN_SALARY=2500000           # Salario mínimo en COP
MIN_MATCH_SCORE=70           # Puntuación mínima (0-100)
PRIORITY_SKILLS=React,Node.js,TypeScript
```

### Velocidad de Ejecución

```env
WAIT_SECONDS=10              # Esperar entre aplicaciones
LOOP_INTERVAL_SECONDS=300    # Intervalo entre ciclos (segundos)
LOGIN_WAIT_SECONDS=180       # Esperar login manual (segundos)
```

### Modo de Ejecución

```env
RUN_CONTINUOUSLY=true        # true = loop infinito, false = una sola vez
```

---

## 📁 Estructura del Proyecto

```
busqueda_de_empleo/
├── job_bot/                          # Bot principal Python
│   ├── main.py                       # Entrada principal
│   ├── config.py                     # Configuración
│   ├── requirements.txt              # Dependencias Python
│   ├── .env                          # Variables de entorno (NO commitear)
│   ├── .env.example                  # Plantilla .env
│   ├── .venv/                        # Virtualenv
│   ├── bot.log                       # Log del bot
│   ├── cv.pdf                        # CV del candidato
│   ├── candidate_profile.json        # Perfil del candidato
│   ├── browser/
│   │   └── driver.py                 # Configuración Selenium
│   ├── models/
│   │   └── job_offer.py              # Modelo de oferta
│   ├── platforms/
│   │   ├── base.py                   # Clase base
│   │   └── magneto.py                # Implementación Magneto365
│   └── services/
│       ├── tracker.py                # Persistencia MySQL
│       ├── applicant.py              # Lógica de postulación
│       ├── analyzer.py               # Análisis de ofertas
│       ├── searcher.py               # Búsqueda de ofertas
│       └── question_answerer.py      # Respuesta automática
│
├── magneto_job_system/               # Dashboard Node.js
│   ├── server.js                     # Servidor Express
│   ├── package.json                  # Dependencias Node
│   ├── .env                          # Variables de entorno
│   ├── .env.example                  # Plantilla .env
│   ├── bot.log                       # Log del dashboard
│   ├── logs/                         # Directorio de logs
│   ├── database/
│   │   ├── connection.js             # Pool de conexión MySQL
│   │   └── init.js                   # Inicialización BD
│   ├── services/
│   │   ├── jobRepository.js          # Queries a ofertas
│   │   ├── logRepository.js          # Queries a logs
│   │   └── scoringService.js         # Cálculo de puntuaciones
│   ├── utils/
│   │   ├── config.js                 # Carga de configuración
│   │   └── logger.js                 # Sistema de logging
│   ├── bot/
│   │   ├── runner.js                 # Runner del bot Node
│   │   └── browser.js                # Control Playwright
│   ├── scrapers/
│   │   └── magnetoScraper.js         # Scraper Magneto365
│   └── dashboard/
│       └── public/
│           ├── index.html            # Frontend
│           ├── app.js                # Lógica frontend
│           └── style.css             # Estilos
│
├── .env                              # Env raíz (fallback)
├── .env.example                      # Plantilla raíz
├── .gitignore                        # Git ignore
├── README.md                         # Este archivo
├── AUDITORIA_COMPLETA.md             # Informe de auditoría
├── AUDITORIA_BOT_EMPLEO.md           # Notas históricas
└── docker-compose.yml                # (Próximamente)
```

---

## 🔐 Seguridad

### ⚠️ IMPORTANTE: Nunca Commitear Secretos

El `.env` está en `.gitignore`. NUNCA:
- Hagas push de `.env`
- Compartas credenciales en GitHub
- Dejes contraseñas en logs

### Buenas Prácticas:

1. **Copiar `.env.example` a `.env`** y completar con tus valores
2. **Usar contraseña segura** para MySQL
3. **No compartir credenciales** públicamente
4. **Rotar secretos** periódicamente

### Variables de Entorno Críticas:

```env
DB_PASSWORD=        # 🔴 CRÍTICO - Nunca en GitHub
DB_USER=            # 🟡 Sensitivo
CHROME_USER_DATA_DIR= # 🟡 Path personal
```

---

## 🐛 Troubleshooting

### El bot no puede conectar a MySQL

```bash
# Verificar que MySQL está corriendo
mysql -h localhost -u root -p

# Verificar credenciales en .env
# Ejecutar script de inicialización
npm run init-db
```

### Error: "No se pudo abrir tu perfil real de Edge"

**Solución:** Cierra todas las ventanas de Edge y desactiva "Edge Startup Boost":

1. Edge → Configuración → Privacidad
2. Buscar "Startup Boost"
3. Apagar el toggle

O permitir perfil fallback:
```env
ALLOW_BOT_PROFILE_FALLBACK=true
```

### Bot se detiene o pierde sesión

El bot ahora verifica login cada 5 ciclos automáticamente. Si aún hay problemas:

```env
LOGIN_WAIT_SECONDS=300    # Aumentar tiempo de espera
RUN_CONTINUOUSLY=false    # Probar modo una sola vez
```

### Dashboard no muestra datos

```bash
# Verificar que MySQL está corriendo
# Verificar conexión
curl http://localhost:3000/api/status

# Ver logs del servidor
tail magneto_job_system/logs/bot.log
```

### Performance lento

Aumentar intervalo entre ciclos:
```env
LOOP_INTERVAL_SECONDS=600    # 10 minutos
WAIT_SECONDS=20              # Más tiempo entre aplicaciones
```

---

## 📊 Monitoreo

### Ver Logs del Bot

```bash
# Python
tail -f job_bot/bot.log

# Node Dashboard
tail -f magneto_job_system/logs/bot.log
```

### Verificar Estado MySQL

```bash
mysql -u root -p job_bot
SELECT COUNT(*) as total_jobs FROM jobs;
SELECT COUNT(*) as total_apps FROM applications;
SELECT status, COUNT(*) FROM jobs GROUP BY status;
```

### API Status

```bash
curl http://localhost:3000/api/status
```

---

## 📈 Estadísticas Típicas

Después de una semana de funcionamiento:

```
Total ofertas encontradas: 150-300
Ofertas analizadas:        150-300
Postulaciones enviadas:    30-60
Tasa de aplicación:        20-40%
Match score promedio:      72-85
```

---

## 🤝 Contribuir

Las contribuciones son bienvenidas. Para cambios importantes:

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📝 Licencia

Este proyecto está bajo la licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

---

## ⚠️ Disclaimer

Este bot está diseñado para **automatizar procesos legales** en plataformas que lo permiten. El usuario es responsable de:

- Verificar que Magneto365 permite automation
- Respetar los términos de servicio
- No usar para spam o abuso
- Mantener comportamiento ético

---

## 📞 Soporte

Para reportar bugs o solicitar features:

1. Abre un [Issue](https://github.com/Rolo0317/busqueda_de_empleo/issues)
2. Incluye detalles del problema
3. Adjunta logs relevantes

---

## 🎉 Agradecimientos

- [Selenium](https://www.selenium.dev/) - Automatización de navegador
- [Express.js](https://expressjs.com/) - Framework web
- [MySQL](https://www.mysql.com/) - Base de datos
- [Pydantic](https://pydantic-settings.readthedocs.io/) - Validación Python

---

**Última actualización:** Mayo 2026  
**Mantenedor:** [@Rolo0317](https://github.com/Rolo0317)

