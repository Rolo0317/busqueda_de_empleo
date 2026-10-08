"""Elige la mejor opcion en preguntas de criterio ("¿que harias?").

Estas preguntas no piden un dato del perfil sino un enfoque. Antes caian en la
regla que prefiere la opcion que nombra una herramienta conocida, y por eso a
"eliminar un proceso manual que genera reprocesos" se respondio "construir
directamente un dashboard en Power BI", y a "consolidar Excel, SAP y otras
fuentes" se respondio "crear un Excel mas organizado" (3 de octubre).

Se puntua el enfoque: entender antes de construir, automatizar en vez de
repetir a mano, validar y dejar trazabilidad. Ninguna opcion afirma algo del
candidato: solo se elige cual describe mejor como trabaja.
"""
from __future__ import annotations

import re
import unicodedata

MARCAS_PREGUNTA = (
    "que harias", "que haria", "que hace", "cual seria tu enfoque", "como abordarias",
    "como lo resolverias", "como actuarias", "que harias primero", "cual seria tu primer paso",
    "que reto", "que proyecto", "cual de estos proyectos", "cual de estas situaciones",
    "what would you do", "how would you approach", "which approach",
)

# Senales de buen criterio y su peso. Positivo suma, negativo resta.
SENALES: tuple[tuple[str, int], ...] = (
    # Entender antes de construir.
    ("entender", 3), ("analizar", 3), ("levantar", 2), ("mapear", 3), ("diagnostic", 3),
    ("identificar", 2), ("causa raiz", 4), ("requerimiento", 2), ("fuentes", 1),
    # Automatizar y estandarizar.
    ("automatiz", 4), ("pipeline", 3), ("etl", 3), ("flujo", 2), ("integrar", 2),
    ("estandariz", 2), ("python", 1), ("sql", 1), ("proceso automatico", 3),
    # Calidad y control.
    ("valid", 3), ("control", 2), ("trazabilidad", 3), ("monitore", 2), ("prueba", 2),
    ("document", 2), ("alerta", 1), ("conciliar", 2),
    # Malas practicas o atajos.
    ("manual", -3), ("a mano", -3), ("directamente", -3), ("mas organizado", -2),
    ("ignorar", -5), ("esperar", -3), ("dejarlo", -4), ("copiar", -3), ("pegar", -3),
    ("solo", -1), ("sin revisar", -5), ("rapido", -1), ("excel mas", -2),
    ("ya esta consolidada", -2), ("periodicos a partir", -1),
)


def _plano(texto: str) -> str:
    base = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode("ascii")
    return " ".join(base.lower().split())


def es_pregunta_de_criterio(pregunta: str) -> bool:
    texto = _plano(pregunta)
    return any(m in texto for m in MARCAS_PREGUNTA)


def puntaje(opcion: str) -> int:
    texto = _plano(opcion)
    return sum(peso for senal, peso in SENALES
               if re.search(r"(?<![a-z])" + re.escape(senal), texto))


def elegir(pregunta: str, opciones: list[str]) -> tuple[str, str] | None:
    """(opcion, motivo) con el mejor enfoque, o None si no es de criterio o hay empate."""
    if not opciones or not es_pregunta_de_criterio(pregunta):
        return None
    puntuadas = sorted(((puntaje(o), o) for o in opciones), key=lambda par: par[0], reverse=True)
    mejor, segunda = puntuadas[0], puntuadas[1] if len(puntuadas) > 1 else (None, None)
    # Sin diferencia no hay criterio que aplicar: mejor que decida otra regla.
    if mejor[0] <= 0 or (segunda[0] is not None and mejor[0] == segunda[0]):
        return None
    return mejor[1], f"Pregunta de criterio: mejor enfoque (puntaje {mejor[0]})"
