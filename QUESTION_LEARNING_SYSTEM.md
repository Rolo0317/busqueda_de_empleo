# 🤖 Sistema de Extracción y Aprendizaje de Preguntas

## ¿Qué se implementó?

El bot ahora **extrae, almacena y aprende de todas las preguntas** que aparecen en los formularios de postulación.

---

## 📋 Flujo de Funcionamiento

```
1. Bot abre oferta de trabajo
   ↓
2. Detecta formulario con preguntas
   ↓
3. Extrae TODAS las preguntas (texto + opciones)
   ↓
4. Usa candidate_profile.json para responder
   ↓
5. GUARDA en BD: pregunta + respuesta + confianza
   ↓
6. Registra patrones para futuro aprendizaje
```

---

## 💾 Base de Datos - Tabla QUESTIONS

Se crea automáticamente con estructura:

```sql
CREATE TABLE questions (
    id BIGINT PRIMARY KEY,
    job_id BIGINT,                    -- Referencia a la oferta
    question_text VARCHAR(1000),      -- La pregunta completa
    answer_given VARCHAR(500),        -- Lo que respondió el bot
    confidence_score DECIMAL(3,2),    -- Confianza 0.0 - 1.0
    created_at TIMESTAMP              -- Cuándo se respondió
)
```

### Ejemplo de Datos Guardados:

```
| ID | question_text                    | answer_given | confidence |
|----|----------------------------------|-------------|-----------|
| 1  | ¿Aceptas trabajar remoto?        | Si          | 0.95      |
| 2  | ¿Años de experiencia?            | 5           | 0.99      |
| 3  | ¿Tienes conflicto de interés?    | No          | 1.00      |
| 4  | ¿Autorizas tratamiento datos?    | Si          | 0.98      |
```

---

## 📊 Logs Mejorados con Emojis

Cuando ejecutas el bot, ves:

```
✅ Pregunta respondida | respuesta=Si | confianza=0.95 | razon=Autorizacion de datos | pregunta=¿Autorizas el tratamiento de tus datos...?

❌ Pregunta omitida | razon=Pregunta sensible fuera del perfil | pregunta=¿Cuál es tu diagnóstico médico?

⚠️ No se pudo aplicar respuesta | respuesta=5 | pregunta=¿Años de experiencia?
```

---

## 🧠 Aprendizaje Automático

### Al terminar los ciclos, el bot muestra:

```
================================================================================
📚 PREGUNTAS FRECUENTES DETECTADAS (últimos 7 días):
  • ¿Aceptas trabajar remoto?... (veces=23, confianza=95.32%)
  • ¿Años de experiencia?... (veces=19, confianza=99.15%)
  • ¿Nivel de inglés?... (veces=17, confianza=92.10%)
  • ¿Autorizas tratamiento de datos?... (veces=16, confianza=98.75%)
  • ¿Disponibilidad para viajar?... (veces=14, confianza=94.20%)
================================================================================
```

**Beneficios:**
- Identifica qué preguntas aparecen más
- Muestra confianza del bot en sus respuestas
- Permite optimizar el perfil para futuro

---

## 🔧 Cómo Usar esta Información

### 1. Monitorear Respuestas

```bash
# Ver últimas 100 preguntas respondidas:
mysql -u root -p job_bot -e "SELECT * FROM questions ORDER BY created_at DESC LIMIT 100;"
```

### 2. Encontrar Patrones

```sql
-- Preguntas que el bot respondió con baja confianza:
SELECT question_text, answer_given, confidence_score 
FROM questions 
WHERE confidence_score < 0.70 
ORDER BY confidence_score ASC;

-- Preguntas más frecuentes:
SELECT question_text, COUNT(*) as veces 
FROM questions 
GROUP BY question_text 
ORDER BY veces DESC 
LIMIT 20;
```

### 3. Optimizar Respuestas

Si el bot responde mal una pregunta frecuente:

1. Edita `candidate_profile.json`
2. Agrega regla en `question_answerer.py`
3. El bot aprenderá automáticamente

---

## 📈 Mejoras por Implementar (Futuro)

- [ ] Machine Learning para predecir mejores respuestas
- [ ] Dashboard con gráficos de preguntas
- [ ] Exportar PDF de patrones semanales
- [ ] Notificaciones si confianza baja < 70%
- [ ] Reentrenamiento automático cada 100 preguntas

---

## 🚀 Ejecutar el Bot con Sistema de Preguntas

```powershell
cd "C:\Users\millo\Downloads\hoja de vida\job_bot"
.\run_bot.ps1
```

**Verás en logs:**
```
[2026-05-09 14:35:00] ✅ Pregunta respondida | respuesta=Si | confianza=0.95
[2026-05-09 14:35:01] ✅ Pregunta respondida | respuesta=5 | confianza=0.99
[2026-05-09 14:35:02] ✅ Pregunta respondida | respuesta=No | confianza=1.00
[2026-05-09 14:36:00] 📊 RESUMEN CICLO | 👀 revisadas=8 | ✅ aplicadas=2 | ❌ errores=0 | ⏭️ omitidas=6
```

---

## 📝 Detalles Técnicos

### Archivos Modificados:

1. **services/tracker.py**
   - `record_question()` - Guarda pregunta en BD
   - `get_question_patterns()` - Analiza patrones
   - `ensure_questions_table()` - Crea tabla si no existe

2. **platforms/magneto.py**
   - Recibe tracker como parámetro
   - `_answer_visible_questions()` - Registra cada pregunta
   - Emojis en logs: ✅ ❌ ⚠️

3. **services/applicant.py**
   - `ApplicationSummary` - Cuenta de preguntas respondidas

4. **main.py**
   - Pasa tracker a platform
   - Muestra resumen de preguntas al terminar
   - Emojis mejorados en logs

---

## ✨ Ventajas

- **Transparencia**: Ves exactamente qué pregunta respondió el bot
- **Aprendizaje**: Los patrones ayudan a optimizar futuras respuestas
- **Auditoría**: Registro completo de todas las respuestas
- **Debugging**: Si algo falla, ves exactamente en qué pregunta
- **Mejora Continua**: Los datos permiten entrenar mejor al bot

---

Implementado: **9 de Mayo de 2026**
