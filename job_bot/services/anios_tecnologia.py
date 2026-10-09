"""Cuantos anos registra el perfil para la tecnologia que menciona una pregunta.

Antes habia dos mapas distintos, uno en el respondedor y otro en el elegidor de
opciones, y cada uno sabia cosas que el otro no: por eso "Mas de 3" en Python
salia como "2 a 3", y una pregunta de ETL se contestaba "No" teniendo seis anos.
Aqui hay uno solo, con coincidencia por palabra completa.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

from services.relevancia_cargo import STACK_AJENO

# Como se nombra cada tecnologia en las preguntas -> clave en experience_years.
ALIAS: dict[str, str] = {
    "python": "python",
    "sql": "sql",
    "mysql": "mysql",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    # NoSQL no es SQL: lo que el perfil respalda de ese mundo es Redis.
    "nosql": "redis",
    "redis": "redis",
    "power bi": "power_bi",
    "powerbi": "power_bi",
    "excel": "excel",
    "pandas": "pandas",
    "numpy": "numpy",
    "etl": "etl",
    "rpa": "rpa",
    "javascript": "javascript",
    "typescript": "javascript",
    "react": "react",
    "node": "node",
    "nodejs": "node",
    "html": "html",
    "css": "css",
    "api": "apis_rest",
    "apis": "apis_rest",
    "rest": "apis_rest",
    "full stack": "full_stack",
    "fullstack": "full_stack",
    "docker": "docker",
    "ia generativa": "generative_ai",
    "inteligencia artificial": "generative_ai",
    "angular": "angular",
    ".net": "dotnet",
    "net core": "dotnet",
    "c#": "dotnet",
    "c sharp": "dotnet",
    "microservicio": "microservices",
    "microservicios": "microservices",
    "liderazgo": "leadership",
    "liderando": "leadership",
    # Areas y oficios, no solo herramientas. Sin estas, "minimo 3 anos en
    # analisis de datos" se contestaba "No" teniendo seis (3 de octubre).
    "analisis de datos": "data_analysis",
    "analitica de datos": "data_analysis",
    "analista de datos": "data_analysis",
    "data analysis": "data_analysis",
    "data analyst": "data_analysis",
    "analisis de informacion": "data_analysis",
    # "experiencia en el cargo" es el de la oferta, y el filtro de relevancia
    # ya garantiza que es del perfil: cuentan los anos totales. Se contestaba
    # "No" a "1 a 2 anos en el cargo" de Analista de datos con seis (3 de octubre).
    "en el cargo": "total",
    "en el rol": "total",
    "cargos similares": "total",
    "cargos afines": "total",
    "roles similares": "total",
    "inteligencia de negocios": "data_analysis",
    "business intelligence": "data_analysis",
    "gestion de informacion": "data_analysis",
    "gestion de la informacion": "data_analysis",
    "base de datos": "sql",
    "bases de datos": "sql",
    "call center": "call_center",
    "contact center": "call_center",
    "servicio al cliente": "customer_service",
    "atencion al cliente": "customer_service",
    "customer service": "customer_service",
    "backoffice": "backoffice",
    "back office": "backoffice",
    "crm": "crm",
    "gtr": "gtr",
    "workforce": "gtr",
    "torre de control": "gtr",
    # "¿Tiene experiencia realizando dashboard?" se contesto "No" con cuatro
    # anos de tableros en Power BI (3 de octubre).
    "dashboard": "power_bi",
    "dashboards": "power_bi",
    "tablero": "power_bi",
    "tableros": "power_bi",
    "visualizacion de datos": "power_bi",
    "reporteria": "data_analysis",
    "kpi": "data_analysis",
    "kpis": "data_analysis",
    "indicadores": "data_analysis",
    "ecommerce": "ecommerce",
    "e-commerce": "ecommerce",
    "marketing digital": "marketing_digital",
}


# Un alias que, si aparece, anula otros mas genericos de la misma frase:
# "bases de datos NoSQL" habla de NoSQL, no de los anos de SQL relacional.
ANULA: dict[str, tuple[str, ...]] = {
    "nosql": ("base de datos", "bases de datos", "sql"),
}

# Variantes de SQL que el perfil no registra. Si la pregunta las nombra, los
# anos de SQL generico no responden por ellas: "avanzado en Oracle PL/SQL, SQL"
# casi se contesto "Mas de 2 anos" sin haber usado nunca Oracle (3 de octubre).
SQL_AJENO = ("oracle", "pl/sql", "plsql", "pl sql", "t-sql", "tsql")
SQL_GENERICO = ("sql", "base de datos", "bases de datos")


# Lo que el perfil no maneja, venga del filtro de cargos (Java, .NET, SAP...) o
# de las variantes de SQL que no registra. Una sola lista para ambos usos.
TECNOLOGIAS_AJENAS = tuple(dict.fromkeys(STACK_AJENO + SQL_AJENO))

# Lo que va despues de "experiencia en/con..." y no nombra una tecnologia, sino
# la trayectoria en general: ahi si valen los anos totales.
CONTEXTOS_GENERICOS = (
    "el cargo", "este cargo", "el rol", "este rol", "la posicion", "esta posicion",
    "cargos similares", "cargos afines", "roles similares", "posiciones similares",
    "funciones similares", "el area", "esta area", "el campo", "total", "general",
)
TEMA_DE_EXPERIENCIA = re.compile(
    r"\b(?:en|con|usando|manejando|utilizando|desarrollando|programando)\s+(.+)$"
)


def tecnologia_ajena(texto: str) -> str | None:
    """La primera tecnologia que nombra el texto y que el perfil no tiene."""
    normalizado = plano(texto)
    return next((t for t in TECNOLOGIAS_AJENAS if _menciona(t, normalizado)), None)


def pregunta_por_algo_especifico(texto: str) -> bool:
    """Si la pregunta de anos nombra un tema concreto en lugar de la trayectoria.

    "¿Cuantos anos de experiencia tienes?" admite los anos totales; "¿cuantos anos
    trabajando con AWS Aurora?" no: responder 6 seria inventar experiencia.
    """
    normalizado = plano(texto).strip(" ?¿.!")
    _, _, despues = normalizado.partition("experiencia")
    tema = TEMA_DE_EXPERIENCIA.search(despues or normalizado)
    if not tema:
        return False
    return not tema.group(1).strip().startswith(CONTEXTOS_GENERICOS)


def plano(texto: str) -> str:
    base = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode("ascii")
    return " ".join(base.lower().split())


def _menciona(alias: str, texto: str) -> bool:
    # Palabra completa: "sql" no debe casar dentro de "nosql", ni "api" en "capital".
    return bool(re.search(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])", texto))


def tecnologias_mencionadas(texto: str, perfil: dict[str, Any]) -> list[tuple[str, float]]:
    """(alias, anos) de cada tecnologia nombrada en el texto que el perfil registra."""
    anios = perfil.get("experience_years", {})
    normalizado = plano(texto)
    encontradas: list[tuple[str, float]] = []
    for alias, clave in ALIAS.items():
        valor = anios.get(clave)
        if isinstance(valor, (int, float)) and _menciona(alias, normalizado):
            encontradas.append((alias, float(valor)))

    anulados = {otro for alias, _ in encontradas for otro in ANULA.get(alias, ())}
    if any(_menciona(ajeno, normalizado) for ajeno in SQL_AJENO):
        anulados.update(SQL_GENERICO)
    return [(alias, anios) for alias, anios in encontradas if alias not in anulados]


def anios_de(texto: str, perfil: dict[str, Any]) -> tuple[str, float] | None:
    """La tecnologia mas especifica mencionada y sus anos.

    Ante varias, gana el alias mas largo ("power bi" antes que "bi", "postgresql"
    antes que "sql"), porque es el que describe mejor lo que se pregunta.
    """
    encontradas = tecnologias_mencionadas(texto, perfil)
    if not encontradas:
        return None
    return max(encontradas, key=lambda par: len(par[0]))


def max_anios(texto: str, perfil: dict[str, Any]) -> float | None:
    """Los anos mas altos entre las tecnologias que nombra el texto."""
    encontradas = tecnologias_mencionadas(texto, perfil)
    return max((anios for _, anios in encontradas), default=None)
