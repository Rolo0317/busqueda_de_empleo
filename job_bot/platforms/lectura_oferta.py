"""Lectura del texto de una tarjeta de oferta.

Son funciones puras sobre texto: no tocan el navegador, asi que se pueden
probar sin abrir nada y las comparten todas las bolsas de empleo en vez de
repetir el mismo recorte de cadenas en cada una.
"""
from __future__ import annotations

import re
import unicodedata

CIUDADES_CONOCIDAS = {
    "bogota": "Bogota",
    "medellin": "Medellin",
    "cali": "Cali",
    "barranquilla": "Barranquilla",
    "bucaramanga": "Bucaramanga",
    "manizales": "Manizales",
    "colombia": "Colombia",
    "remoto": "Remoto",
    "teletrabajo": "Teletrabajo",
}

PALABRAS_VACIAS = {"de", "del", "la", "las", "el", "los", "en", "y", "o"}


def normalizar(valor: str) -> str:
    """Minusculas y sin tildes, para comparar textos que vienen de la pagina."""
    return unicodedata.normalize("NFKD", valor or "").encode("ascii", "ignore").decode("ascii").lower()


def limpiar(valor: str) -> str:
    return re.sub(r"\s+", " ", valor or "").strip()


def slug(valor: str) -> str:
    plano = normalizar(valor)
    palabras = re.findall(r"[a-z0-9]+", plano)
    return "-".join(p for p in palabras if p not in PALABRAS_VACIAS)


def titulo(texto: str) -> str:
    return texto.split(" - ")[0].split("|")[0].strip() or "Cargo no especificado"


def empresa(texto: str) -> str:
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]
    if len(lineas) >= 3:
        return lineas[2].split("|")[0].strip()
    partes = [p.strip() for p in re.split(r"\s+\|\s+", texto) if p.strip()]
    return partes[2] if len(partes) >= 3 else "No especificada"


def fecha(texto: str) -> str:
    hallado = re.search(
        r"\b(20\d{2}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/20\d{2}|Hace\s+\d+\s+\w+)\b", texto, re.IGNORECASE)
    return hallado.group(1) if hallado else "No especificada"


def salario(texto: str) -> str:
    for linea in (l.strip() for l in texto.splitlines() if l.strip()):
        if "$" in linea or "salario" in linea.lower() or "convenir" in linea.lower():
            return linea
    return "No especificado"


def ciudad(texto: str, configuradas: list[str]) -> str:
    preferidas = [(normalizar(c), c) for c in configuradas]
    for linea in (l.strip() for l in texto.splitlines() if l.strip()):
        plano = normalizar(linea)
        for buscada, mostrada in preferidas:
            if buscada in plano:
                return mostrada
        for marca, mostrada in CIUDADES_CONOCIDAS.items():
            if marca in plano:
                return mostrada
    return "No especificada"


def es_ubicacion_valida(texto: str, configuradas: list[str]) -> bool:
    plano = normalizar(texto)
    if any(m in plano for m in ("colombia", "remoto", "teletrabajo")):
        return True
    return any(normalizar(c) in plano for c in configuradas)


def coincide_con_busqueda(texto: str, palabra: str) -> bool:
    plano = normalizar(texto)
    buscada = normalizar(palabra)
    if buscada.replace(" ", "") in plano.replace(" ", ""):
        return True
    partes = [p for p in re.findall(r"[a-z0-9]+", buscada) if len(p) > 2]
    return bool(partes) and all(p in plano for p in partes)
