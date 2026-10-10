"""Preguntas de criterio: se elige el mejor enfoque, no la herramienta conocida.

Las preguntas son las reales de Magneto (Analista de Automatizacion y Datos,
3 de octubre); la opcion que eligio el bot entonces esta entre las incorrectas.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from respuestas.criterio_situacional import elegir

# (pregunta, opciones, la opcion correcta)
CASOS = [
    ("Si recibes un proceso financiero que cada mes requiere consolidar información de Excel, "
     "SAP y otras fuentes, ¿qué harías primero?",
     ["Crear un Excel más organizado para reducir el tiempo de consolidación.",
      "Entender el proceso, mapear las fuentes y validar los datos antes de automatizar.",
      "Pedir a cada área que envíe la información a tiempo."],
     "Entender el proceso, mapear las fuentes y validar los datos antes de automatizar."),
    ("Tienes Python, SQL y Power BI disponibles. El área financiera te pide eliminar un proceso "
     "manual que genera reprocesos todos los meses. ¿Cuál sería tu enfoque?",
     ["Construir directamente un dashboard en Power BI.",
      "Automatizar la extracción y transformación con Python y SQL, con validaciones, "
      "y luego visualizar en Power BI.",
      "Documentar el proceso manual para que otra persona lo haga."],
     "Automatizar la extracción y transformación con Python y SQL, con validaciones, "
     "y luego visualizar en Power BI."),
    ("Encuentras que un proceso automatizado funciona correctamente el 95% de las veces, pero "
     "ocasionalmente genera información incorrecta. ¿Qué harías?",
     ["Ignorarlo, porque el 95% es un buen resultado.",
      "Investigar la causa raíz, revisar las reglas de transformación, implementar controles "
      "y dejar trazabilidad del error.",
      "Corregir a mano los casos incorrectos cuando aparezcan."],
     "Investigar la causa raíz, revisar las reglas de transformación, implementar controles "
     "y dejar trazabilidad del error."),
    ("¿Cuál de estos proyectos representa mejor el tipo de reto que te gustaría asumir?",
     ["Crear reportes periódicos a partir de información que ya está consolidada.",
      "Automatizar un proceso de punta a punta integrando varias fuentes de datos."],
     "Automatizar un proceso de punta a punta integrando varias fuentes de datos."),
]


def main() -> int:
    fallos = 0
    for pregunta, opciones, correcta in CASOS:
        elegida = elegir(pregunta, opciones)
        ok = elegida is not None and elegida[0] == correcta
        fallos += not ok
        print(f"  [{'ok ' if ok else 'FALLA'}] {pregunta[:60]}")
        if not ok:
            print(f"          eligio: {elegida}")

    # Una pregunta de dato no es de criterio: la decide otra regla.
    ok = elegir("¿Cuál es tu nivel de inglés?", ["A1", "A2", "B1"]) is None
    fallos += not ok
    print(f"  [{'ok ' if ok else 'FALLA'}] una pregunta de dato no se toma como de criterio")

    total = len(CASOS) + 1
    print(f"\n  {total - fallos} de {total} correctos")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
