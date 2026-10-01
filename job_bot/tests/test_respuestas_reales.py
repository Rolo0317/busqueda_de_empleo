"""Comprueba las respuestas contra las preguntas reales que el bot ya recibio.

Son las preguntas registradas en la base durante las corridas: es el unico
banco de pruebas que refleja lo que las empresas preguntan de verdad.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from services.question_answerer import CandidateQuestionAnswerer

# El perfil de ejemplo del repositorio, no el personal: asi las pruebas dan lo
# mismo en cualquier maquina y no dependen de datos privados.
PERFIL_DE_EJEMPLO = Path(__file__).resolve().parent.parent / "candidate_profile.example.json"

# (pregunta, opciones, comprobacion, que se espera en palabras)
CASOS = [
    ("indicame tu whatsapp", [],
     lambda r: bool(re.search(r"\d{3}", r)), "el numero de telefono"),
    ("Confirma tu número de WhatsApp, por ese medio te notificaremos del avance", [],
     lambda r: bool(re.search(r"\d{3}", r)), "el numero de telefono"),
    ("¿vives en Bogotá?", [],
     lambda r: r.strip().lower().startswith("si"), "Si (vive en Bogota)"),
    ("vives en bogotá o alrededores?", [],
     lambda r: r.strip().lower().startswith("si"), "Si (vive en Bogota)"),
    ("¿vives en Medellín?", [],
     lambda r: r.strip().lower().startswith("no"), "No (no vive en Medellin)"),
    ("indicame formacion academica", [],
     lambda r: "sena" in r.lower(), "su formacion titulada"),
    ("¿Nivel de ingles?", [],
     lambda r: "a2" in r.lower(), "el nivel real de ingles"),
    (": En una escala de 1 a 5, ¿cuál es su nivel de experiencia real con Python?", [],
     lambda r: r.strip() in {"1", "2", "3", "4", "5"}, "un numero del 1 al 5"),
    ("¿Qué lenguajes de programación conoce y ha trabajado?", [],
     lambda r: "python" in r.lower(), "los lenguajes del perfil"),
    ("indicame barrio de residencia", [],
     lambda r: "bogot" in r.lower(), "su ubicacion"),
    ("¿Cuál es tu correo electrónico?", [],
     lambda r: "@" in r, "el correo del perfil"),
    ("¿Cuentas con experiencia sólida en Salesforce - Sales Cloud?", [],
     lambda r: r.strip().lower().startswith("no"), "No (no lo tiene)"),
    ("Describe one production application you personally worked on across both "
     "frontend and backend.", [],
     lambda r: " the " in r or " and " in r, "una respuesta en ingles"),
    ("Describe a production Agentic AI system you personally designed or built.", [],
     lambda r: " and " in r or " years " in r, "una respuesta en ingles"),
    # Con opciones: negarse una habilidad que el perfil respalda es descartarse solo.
    ("¿Qué experiencia tienes en el uso de Power BI para visualización de datos?",
     ["No tengo experiencia con Power BI, pero estoy dispuesto a aprender.",
      "He usado Power BI una vez en un proyecto personal.",
      "Uso Power BI regularmente para crear dashboards y reportes."],
     lambda r: "regularmente" in r.lower(), "la opcion que afirma uso regular"),
    # Trabajo real con agentes: el robot RPA en produccion del perfil.
    ("Have you personally implemented production controls for an AI/agentic system "
     "such as guardrails, evals or tracing?", ["Yes", "No"],
     lambda r: r.strip().lower() in ("si", "yes"), "Si (tiene un agente RPA en produccion)"),
    ("In that Agentic AI system, how did you make the agent safe and reliable in production?", [],
     lambda r: "logging" in r.lower() or "validation" in r.lower(), "los controles reales"),
    ("¿Tienes experiencia construyendo agentes de IA o automatizaciones RPA?", [],
     lambda r: r.strip().lower().startswith("si"), "Si"),
    ("Describe a production Agentic AI system you personally designed, built or ran.", [],
     lambda r: "rpa" in r.lower(), "el robot RPA del perfil"),
    # Preguntas reales de Computrabajo (cuestionario de seleccion).
    ("Si una herramienta de IA te genera una consulta SQL, un análisis o una "
     "recomendación sobre los datos, ¿qué harías antes de utilizar o compartir ese resultado?", [],
     lambda r: "contrast" in r.lower() or "comparo" in r.lower(), "como valida la salida de IA"),
    ("Cuéntanos brevemente cómo has utilizado herramientas de IA generativa como ChatGPT "
     "o Copilot en tu trabajo o proyectos de analítica.", [],
     lambda r: "rpa" in r.lower() or "generativa" in r.lower(), "su uso real de IA"),
    ("En caso de encontrarse interesad@ por favor dejar línea de contacto", [],
     lambda r: bool(re.search(r"\d{3}", r)), "el telefono, no un texto de motivacion"),
    ("Cuentanos brevemente tu experiencia y los lenguajes que manejas", [],
     lambda r: len(r) > 40, "un relato, no una cifra suelta"),
    ("Indique número de celular y correo electrónico actualizado", [],
     lambda r: "@" in r and bool(re.search(r"\d{3}", r)), "telefono y correo"),
    # Preguntas cerradas reales de Computrabajo (radios KillerQuestions).
    ("¿Cuántos años has programado en Python para procesos de datos?",
     ["Ninguno", "Menos de 1", "1 a 2", "2 a 3", "Más de 3"],
     lambda r: r == "Más de 3", "Más de 3 (el perfil tiene 4 anos)"),
    ("¿Has construido y mantenido procesos ETL en producción?", ["Si", "No"],
     lambda r: r == "Si", "Si (el perfil registra ETL)"),
    ("¿Cuántos años de experiencia tienes con React?",
     ["Ninguno", "Menos de 1", "1 a 2", "2 a 3", "Más de 3"],
     lambda r: r == "1 a 2", "1 a 2 (tiene 1 ano), sin exagerar"),
    # NoSQL no es SQL: no debe responder con los anos de SQL.
    ("¿Cuántos años de experiencia tienes con bases de datos NoSQL?", [],
     lambda r: r.strip() == "1", "1 (Redis), no los 6 de SQL"),
    ("Describe un pipeline de datos que hayas construido: fuentes, transformaciones y destino.", [],
     lambda r: "rpa" in r.lower() and "etl" in r.lower(), "sus pipelines reales"),
    ("Si tienes experiencia con Databricks o Spark, cuéntanos en qué proyectos.", [],
     lambda r: r.lower().startswith("no tengo experiencia en"), "un no honesto"),
    # Magneto, 28 de septiembre: nunca afirmar una tecnologia que no tiene.
    ("Are you comfortable using Java and TypeScript?",
     ["I am stronger in Java but can use both", "I am stronger in TypeScript but can use both",
      "I only know Java", "I only know TypeScript", "I am not comfortable with either"],
     lambda r: "java" not in r.lower().replace("typescript", "") and "both" not in r.lower(),
     "una opcion que no afirme Java"),
    ("What is your english level?", ["A1", "A2", "B1", "B2", "C1", "C2"],
     lambda r: r == "A2", "A2"),
    ("¿Qué experiencia tiene manejando flujos de integración continua y despliegue continuo (CI/CD)?", [],
     lambda r: r.lower().startswith("no tengo experiencia en"), "un no honesto sobre CI/CD"),
    ("¿Cuál es tu nivel de conocimiento en SQL?",
     ["Sin experiencia", "Básico", "Intermedio", "Avanzado"],
     lambda r: r.lower() in ("avanzado", "intermedio"), "Avanzado o Intermedio"),
]


def main() -> int:
    respondedor = CandidateQuestionAnswerer(PERFIL_DE_EJEMPLO)
    fallos = 0

    for pregunta, opciones, cumple, esperado in CASOS:
        decision = respondedor.answer(pregunta, opciones)
        respuesta = str(decision.value or "")
        ok = decision.should_answer and cumple(respuesta)
        if not ok:
            fallos += 1
        print(f"  [{'ok   ' if ok else 'FALLA'}] {pregunta[:52]:<54}")
        print(f"          -> {respuesta[:88]}")
        if not ok:
            print(f"          se esperaba: {esperado}")

    print()
    print(f"  {len(CASOS) - fallos} de {len(CASOS)} correctas")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
