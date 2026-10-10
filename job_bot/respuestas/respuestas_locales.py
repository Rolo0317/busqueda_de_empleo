"""Respuestas a preguntas abiertas construidas desde el perfil real.

No inventa credenciales: si el candidato no tiene un titulo, la respuesta lo dice
y compensa con lo que si tiene. Una respuesta indefendible en entrevista cuesta
mas que una omision.

Los relatos propios de cada candidato (sus proyectos, sus empresas, su
formacion) viven en la clave "relatos" del perfil, no aqui: este modulo solo
decide cual corresponde a cada pregunta. Sin relato, se responde con el resumen.
"""
from __future__ import annotations

import re
import unicodedata
from string import Formatter
from typing import Any

# Tecnologias que el perfil puede declarar, con el nombre usado al responder.
CATALOGO_TECNICO = {
    "python": "Python",
    "sql": "SQL",
    "power bi": "Power BI",
    "powerbi": "Power BI",
    "excel": "Excel",
    "javascript": "JavaScript",
    "react": "React",
    "django": "Django",
    "flask": "Flask",
    "node": "Node.js",
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "docker": "Docker",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "git": "Git",
    "html": "HTML/CSS",
    "redis": "Redis",
    "rpa": "automatizacion RPA",
    "etl": "ETL",
}

# Tecnologias que suelen preguntarse y que el perfil NO declara.
NO_DECLARADAS = ("r", "spss", "sas", "stata", "matlab", "scala", "tableau", "qlik",
                 "salesforce", "apex", "sap", "java", "spring boot", "flutter",
                 "angular", ".net", "php", "ruby", "kubernetes", "azure",
                 "databricks", "spark", "airflow", "snowflake", "bigquery", "kafka",
                 "hadoop", "dbt", "ci/cd", "cicd", "jenkins", "github actions",
                 "gitlab ci", "terraform")

MARCAS_TITULO = (
    "ingenieria", "ingeniero", "profesional en", "titulo profesional",
    "pregrado", "licenciatura", "carrera universitaria",
)


def sin_tildes(texto: str) -> str:
    plano = unicodedata.normalize("NFKD", texto)
    return plano.encode("ascii", "ignore").decode("ascii").lower()


class RespuestasLocales:
    """Compone respuestas de texto libre a partir del perfil del candidato."""

    def __init__(self, perfil: dict[str, Any]) -> None:
        self.perfil = perfil
        self.anios = perfil.get("experience_years", {})
        self.skills = [sin_tildes(s) for s in perfil.get("main_skills", [])]

    def responder(self, pregunta: str) -> str | None:
        texto = sin_tildes(pregunta)
        # El orden importa: lo concreto antes que lo general. "Indicame tu
        # whatsapp" contiene la palabra que dispara el resumen generico, y
        # terminaba enviando un parrafo de experiencia donde iba un telefono.
        reglas = (
            (self._es_contacto, self._decir_contacto),
            (self._es_barrio, self._decir_barrio),
            (self._es_escala, self._decir_escala),
            (self._es_idioma, self._decir_idioma),
            (self._es_formacion_academica, self._decir_formacion_academica),
            (self._es_pipeline, self._decir_pipeline),
            (self._es_validacion_ia, self._decir_validacion_ia),
            (self._es_agentes_ia, self._decir_agentes_ia),
            (self._es_vinculo_empresa, self._decir_vinculo_empresa),
            (self._es_motores_bd, self._decir_motores_bd),
            (self._es_fecha, self._decir_fecha),
            (self._es_proyecto_ui, self._decir_proyecto_ui),
            (self._es_anios, self._decir_anios),
            (self._es_tecnologias, self._decir_tecnologias),
            (self._es_titulo, self._decir_titulo),
            (self._es_modelos, self._decir_modelos),
            (self._es_salario, self._decir_salario),
            (self._es_disponibilidad, self._decir_disponibilidad),
            (self._es_experiencia, self._decir_resumen),
            # Ultima red: una pregunta en ingles contestada con el parrafo en
            # espanol delata que nadie la leyo. Mejor responderla en su idioma.
            (self._en_ingles, self._decir_resumen_ingles),
        )
        for detecta, construye in reglas:
            if detecta(texto):
                return construye(texto)
        return None

    # ------------------------------------------------- datos de contacto y sede

    @staticmethod
    def _es_contacto(t: str) -> bool:
        # Con las faltas de ortografia reales de los formularios ("Whastapp").
        return any(m in t for m in ("whatsapp", "whastapp", "whatsap", "watsap", "wpp", "wasap",
                                    "numero de celular",
                                    "numero celular", "tu celular", "tu telefono",
                                    "numero de contacto", "numero de telefono",
                                    "numero movil", "linea de contacto"))

    def _decir_contacto(self, t: str) -> str:
        return str(self.perfil.get("phone", "")).strip()

    @staticmethod
    def _es_barrio(t: str) -> bool:
        return "barrio" in t or "localidad" in t

    def _decir_barrio(self, t: str) -> str:
        """Sin barrio en el perfil se responde la ciudad, que es dato cierto."""
        barrio = str(self.perfil.get("neighborhood", "")).strip()
        ciudad = str(self.perfil.get("city", "")).strip()
        return barrio or ciudad

    @staticmethod
    def _es_escala(t: str) -> bool:
        return bool(re.search(r"escala de\s*1\s*a\s*([0-9]+)", t))

    def _decir_escala(self, t: str) -> str:
        """Traduce los anos del perfil a la escala que pide la pregunta.

        Responder con un parrafo donde piden un numero deja la respuesta sin
        valor para quien filtra por ese campo.
        """
        tope = int(re.search(r"escala de\s*1\s*a\s*([0-9]+)", t).group(1))
        anios = max((v for clave, v in self.anios.items()
                     if clave.replace("_", " ") in t and isinstance(v, (int, float))), default=0)
        if not anios:
            anios = self.anios.get("total", 0) or 1

        # 6+ anos es el tope; por debajo se reparte de forma proporcional.
        nivel = min(tope, max(1, round(anios / 6 * tope)))
        return str(nivel)

    @staticmethod
    def _es_idioma(t: str) -> bool:
        return any(m in t for m in ("nivel de ingles", "ingles", "idioma", "english level"))

    def _decir_idioma(self, t: str) -> str:
        idiomas = self.perfil.get("languages", {})
        ingles = idiomas.get("english", "")
        espanol = idiomas.get("spanish", "Nativo")
        return (f"Espanol {espanol.lower()}. Ingles nivel {ingles}: leo documentacion "
                "tecnica sin dificultad y estoy mejorando la conversacion.")

    @staticmethod
    def _es_formacion_academica(t: str) -> bool:
        return any(m in t for m in ("formacion academica", "nivel educativo", "nivel academico",
                                    "estudios realizados", "formacion educativa",
                                    "indicame formacion", "ultimo nivel de estudios"))

    def _decir_formacion_academica(self, t: str) -> str:
        """Lista la formacion titulada real, sin inventar un titulo profesional."""
        titulos = [f"{e.get('degree', '')} ({e.get('institution', '')}, {e.get('year', '')})"
                   for e in self.perfil.get("education", []) if e.get("degree")]
        complemento = self._relato("formacion_complementaria", t)
        if not titulos:
            return complemento or "Formacion tecnica, complementada con cursos certificados."
        return self._enumerar(titulos) + "." + (f" {complemento}" if complemento else "")


    @staticmethod
    def _es_anios(t: str) -> bool:
        pide_cantidad = ("cuantos anos" in t or "how many years" in t or
                         "years of" in t or "anos de experiencia" in t)
        return pide_cantidad

    @staticmethod
    def _en_ingles(t: str) -> bool:
        """Detecta el idioma por palabras funcionales, no por frases hechas.

        Con una lista de frases exactas, "Describe one production application
        you personally worked on" no se reconocia como ingles.
        """
        marcas = ("how many", "do you have", "what is your", "are you", "years of",
                  "please describe", "tell us", "describe", "your experience",
                  "have you", "which", "what ", " the ", " and ", " you ")
        return sum(1 for m in marcas if m in t) >= 2

    def _decir_anios(self, t: str) -> str:
        """Responde los anos sin subvalorar ni exagerar.

        Decir "1 ano" porque el perfil marca full_stack=1 descarta al candidato
        de cualquier vacante que pida 3+, e ignora seis anos construyendo
        automatizaciones y sistemas de datos con Python y SQL, que tambien es
        ingenieria de software. Se informan ambas cifras y que las distingue.
        """
        return self._relato("anios", t) or self._decir_resumen(t)


    # Empresas donde el candidato SI trabajo. Cualquier otra afirmacion de
    # vinculo laboral es falsa y no debe construirse nunca.
    def _empresas_propias(self) -> list[str]:
        return [sin_tildes(e.get("company", "")) for e in self.perfil.get("experience", [])]

    # ------------------------------------------------------ agentes y automatizacion

    MARCAS_AGENTES = ("agentic", "agente de ia", "agentes de ia", "ai agent", "ai/agentic",
                      "agente rpa", "automatizacion", "automation", "rpa", "llm",
                      "inteligencia artificial", "ia generativa", "generative ai",
                      "herramienta de ia", "herramientas de ia", "copilot", "chatgpt")

    # Preguntan por el criterio antes de usar lo que genera una IA, no por
    # la tecnologia: contestar con los anos de SQL no responde nada.
    MARCAS_VALIDACION = ("antes de utilizar", "antes de usar", "antes de compartir",
                         "que harias antes", "como validaste", "como validas",
                         "verificar", "validar", "confiar en el resultado")

    @staticmethod
    def _es_pipeline(t: str) -> bool:
        # Piden describir un flujo de datos propio; el resumen generico no lo hace.
        return "pipeline" in t or ("flujo de datos" in t) or (
            "etl" in t and any(v in t for v in ("describe", "cuentanos", "cuenta un")))

    def _decir_pipeline(self, t: str) -> str:
        """Los flujos de datos reales del perfil, con sus resultados medibles."""
        return self._relato("pipeline", t) or self._decir_resumen(t)

    @classmethod
    def _es_validacion_ia(cls, t: str) -> bool:
        return (any(m in t for m in cls.MARCAS_AGENTES)
                and any(m in t for m in cls.MARCAS_VALIDACION))

    def _decir_validacion_ia(self, t: str) -> str:
        """Como contrasta lo que genera una IA antes de darlo por bueno."""
        if self._en_ingles(t):
            return (
                "I never ship AI output as it comes. I read the query or the logic line by "
                "line to check it answers the actual question, run it against a small known "
                "sample and compare the totals with a figure I already trust from the source "
                "system. If the numbers do not match, the problem is usually an implicit "
                "assumption about the data, so I go back to the source before sharing anything."
            )
        return (
            "Nunca doy por buena una salida de IA sin contrastarla. Leo la consulta o el "
            "razonamiento linea por linea para confirmar que responde a lo que se pregunto, "
            "la corro sobre una muestra conocida y comparo los totales con una cifra que ya "
            "tengo validada en el sistema origen. Si no cuadran, casi siempre hay un supuesto "
            "implicito sobre los datos, y vuelvo a la fuente antes de compartir nada."
        )

    CONTROLES_AGENTES = ("guardrail", "eval", "tracing", "trazabilidad", "monitoreo",
                         "controles de produccion", "production controls", "observabilidad",
                         # Tambien preguntan por lo mismo sin nombrar la tecnica.
                         "safe and reliable", "safe", "reliable", "confiable", "fiable",
                         "seguro", "errores", "fallos", "failures")

    @classmethod
    def _es_agentes_ia(cls, t: str) -> bool:
        return any(m in t for m in cls.MARCAS_AGENTES)

    def _decir_agentes_ia(self, t: str) -> str:
        """Describe el trabajo real con agentes, sin atribuirse herramientas ajenas.

        El perfil registra un agente RPA en produccion y uso de IA generativa. Lo
        que no hay son frameworks formales de evaluacion, y decirlo de frente vale
        mas que una afirmacion que no se sostiene en entrevista.
        """
        base = self._relato("agentes", t)
        if base is None:
            return self._decir_resumen(t)
        controles = self._relato("agentes_controles", t)
        if controles and any(c in t for c in self.CONTROLES_AGENTES):
            return f"{base} {controles}"
        return base

    # Siempre hablan de un vinculo previo con la empresa que ofrece el cargo.
    MARCAS_VINCULO_EMPRESA = ("experiencia laboral previa con", "trabajado en la empresa",
                              "vinculo con la empresa", "ex empleado", "exempleado",
                              "con nosotros", "para nosotros", "en nuestra compania",
                              "en nuestra empresa", "sus filiales")
    # Solo cuentan si ademas nombran a la empresa: "¿con que motores de bases
    # de datos has trabajado?" no pregunta por un empleo anterior alli.
    MARCAS_TRABAJO_PREVIO = ("has trabajado", "trabajaste", "ha laborado", "laboraste")
    REFERENCIAS_A_LA_EMPRESA = ("esta empresa", "la empresa", "esta compania", "la compania",
                                "esta organizacion", "la organizacion", "el grupo", "filial")

    @classmethod
    def _es_vinculo_empresa(cls, t: str) -> bool:
        if any(m in t for m in cls.MARCAS_VINCULO_EMPRESA):
            return True
        return (any(m in t for m in cls.MARCAS_TRABAJO_PREVIO)
                and any(r in t for r in cls.REFERENCIAS_A_LA_EMPRESA))

    def _decir_vinculo_empresa(self, t: str) -> str:
        """Nunca afirma un empleo que el perfil no registra."""
        for empresa in self._empresas_propias():
            palabras = [p for p in empresa.split() if len(p) > 3]
            if palabras and all(p in t for p in palabras[:2]):
                return "Si, he trabajado en esa empresa."
        return "No, no he trabajado en esa empresa ni en sus filiales."

    # Motores que se reconocen en experience_years, con su nombre comercial.
    MOTORES_BD = {"mysql": "MySQL", "postgresql": "PostgreSQL", "sql_server": "SQL Server",
                  "oracle": "Oracle", "mongodb": "MongoDB", "redis": "Redis"}

    @staticmethod
    def _es_motores_bd(t: str) -> bool:
        return (any(m in t for m in ("motor", "gestor", "manejador"))
                and ("base de datos" in t or "bases de datos" in t))

    def _decir_motores_bd(self, t: str) -> str:
        """Los motores del perfil con sus años, del más usado al menos (10/10:
        antes caía en un texto genérico que no nombraba ninguno)."""
        usados = sorted(((nombre, self.anios.get(clave, 0)) for clave, nombre in self.MOTORES_BD.items()
                         if self.anios.get(clave, 0)), key=lambda par: -par[1])
        if not usados:
            return f"Trabajo con SQL desde hace {self.anios.get('sql', 0)} años."
        partes = [f"{nombre} ({anios:g} año{'s' if anios != 1 else ''})" for nombre, anios in usados]
        lista = partes[0] if len(partes) == 1 else ", ".join(partes[:-1]) + " y " + partes[-1]
        return f"He trabajado con {lista}."

    @staticmethod
    def _es_fecha(t: str) -> bool:
        return ("dd-mm" in t or "dd/mm" in t or "aaaa" in t or
                "registra la fecha" in t or "fecha de ingreso" in t)

    def _decir_fecha(self, t: str) -> str:
        """El cargo actual es el mas reciente del perfil."""
        experiencias = self.perfil.get("experience", [])
        if not experiencias:
            return "01-01-2020"
        periodo = experiencias[0].get("period", "")
        meses = {"ene": "01", "feb": "02", "mar": "03", "abr": "04", "may": "05", "jun": "06",
                 "jul": "07", "ago": "08", "sep": "09", "oct": "10", "nov": "11", "dic": "12"}
        partes = sin_tildes(periodo).replace("-", " ").split()
        mes = anio = None
        for i, palabra in enumerate(partes):
            if palabra[:3] in meses and mes is None:
                mes = meses[palabra[:3]]
                if i + 1 < len(partes) and partes[i + 1].isdigit():
                    anio = partes[i + 1]
        return f"01-{mes or '01'}-{anio or '2026'}"

    @staticmethod
    def _es_proyecto_ui(t: str) -> bool:
        return ("componente de interfaz" in t or "interfaz de usuario mas complejo" in t
                or "proyecto mas complejo" in t or "cuentanos sobre" in t)

    def _decir_proyecto_ui(self, t: str) -> str:
        return self._relato("proyecto", t) or self._decir_resumen(t)

    # ------------------------------------------------------------- detectores

    @staticmethod
    def _menciona(clave: str, t: str) -> bool:
        """Busca la tecnologia como palabra completa.

        Con subcadenas, "r" de la lista de no declaradas aparecia en casi
        cualquier frase y toda pregunta se tomaba por tecnica.
        """
        return bool(re.search(r"(?<![a-z0-9])" + re.escape(clave) + r"(?![a-z0-9])", t))

    @classmethod
    def _es_tecnologias(cls, t: str) -> bool:
        claves = list(CATALOGO_TECNICO) + list(NO_DECLARADAS)
        menciones = sum(1 for c in claves if cls._menciona(c, t))
        # "Que lenguajes conoce?" no nombra ninguna tecnologia y aun asi pide
        # la lista: sin esto caia en el resumen generico.
        pide_listado = any(m in t for m in ("lenguaje", "herramienta", "tecnologias",
                                            "stack", "que maneja", "conoce y ha trabajado"))
        return menciones >= 2 or pide_listado or (menciones == 1 and "experiencia" in t)

    @staticmethod
    def _es_titulo(t: str) -> bool:
        return any(m in t for m in MARCAS_TITULO)

    @staticmethod
    def _es_modelos(t: str) -> bool:
        return any(m in t for m in ("modelo estadistico", "modelos estadisticos",
                                    "predictivo", "machine learning", "regresion"))

    @staticmethod
    def _es_salario(t: str) -> bool:
        return "aspiracion" in t or "pretension" in t or ("salario" in t and "espera" in t)

    @staticmethod
    def _es_disponibilidad(t: str) -> bool:
        return "disponibilidad" in t or "cuando puede" in t or "incorporacion" in t

    @staticmethod
    def _es_experiencia(t: str) -> bool:
        return "experiencia" in t

    # ----------------------------------------------------------- constructores

    def _decir_tecnologias(self, t: str) -> str:
        tengo: list[str] = []
        for clave, nombre in CATALOGO_TECNICO.items():
            if clave in t and any(clave in s for s in self.skills) and nombre not in tengo:
                tengo.append(nombre)

        faltan = [c.upper() if len(c) <= 4 else c.capitalize()
                  for c in NO_DECLARADAS if self._menciona(c, t)]

        # Si preguntan por algo que el perfil no tiene, la respuesta empieza por
        # ahi: enterrarlo tras una lista de habilidades parece esquivar la pregunta.
        if faltan and not tengo:
            return ("No tengo experiencia en " + self._enumerar(faltan) +
                    ". Mi experiencia esta en " + self._enumerar(self._skills_principales(5)) +
                    ", y adopto herramientas nuevas con rapidez.")

        # Si la pregunta no nombro nada conocido, se enumeran las habilidades
        # reales del perfil en vez de repetir el mismo parrafo de siempre.
        if not tengo:
            tengo = self._skills_principales()
        if not tengo:
            return self._decir_resumen(t)

        partes = ["Manejo " + self._enumerar(tengo) + "."]
        detalle = [f"{nombre} ({self.anios[clave]} anos)"
                   for clave, nombre in (("python", "Python"), ("sql", "SQL"), ("power_bi", "Power BI"))
                   if clave in self.anios and nombre in tengo]
        if detalle:
            partes.append("Mi experiencia principal esta en " + self._enumerar(detalle) + ".")
        if faltan:
            partes.append("No tengo experiencia en " + self._enumerar(faltan) +
                          ", pero adopto herramientas nuevas de analisis con rapidez.")
        return " ".join(partes)

    def _decir_titulo(self, t: str) -> str:
        # El relato del perfil dice la verdad sobre el titulo; sin el, se lista
        # la formacion real en vez de afirmar o negar un titulo a ciegas.
        return self._relato("titulo", t) or self._decir_formacion_academica(t)

    def _decir_modelos(self, t: str) -> str:
        return self._relato("modelos", t) or self._decir_resumen(t)

    def _decir_salario(self, t: str) -> str:
        monto = self.perfil.get("minimum_salary_cop", 0)
        return (f"Mi aspiracion salarial es de ${monto:,.0f} COP mensuales, "
                "negociable segun el alcance del rol.")

    def _decir_disponibilidad(self, t: str) -> str:
        return "Disponibilidad inmediata, en modalidad presencial, remota o hibrida."

    def _decir_resumen(self, t: str) -> str:
        if self._en_ingles(t):
            return self._decir_resumen_ingles(t)
        return self.perfil.get("short_texts", {}).get(
            "profile_summary",
            "Cuento con experiencia en desarrollo full stack, analisis de datos y automatizacion.",
        )

    def _decir_resumen_ingles(self, t: str) -> str:
        """Resumen en ingles construido con las mismas cifras del perfil."""
        relato = self.perfil.get("relatos", {}).get("resumen", {}).get("en")
        if relato:
            return self._rellenar(relato)
        habilidades = self._enumerar_ingles(self._skills_principales(5))
        return f"{self.anios.get('total', 0)} years of professional experience with {habilidades}."

    # ---------------------------------------------------------------- relatos

    def _relato(self, clave: str, t: str) -> str | None:
        """El relato del perfil para esta pregunta, en el idioma en que se hizo.

        Si falta la version en ingles se usa la de espanol: una respuesta cierta
        en otro idioma vale mas que ninguna.
        """
        versiones = self.perfil.get("relatos", {}).get(clave) or {}
        idioma = "en" if self._en_ingles(t) else "es"
        texto = versiones.get(idioma) or versiones.get("es")
        return self._rellenar(texto) if texto else None

    def _rellenar(self, plantilla: str) -> str:
        """Sustituye {total}, {web} y {titulo}; cualquier otra llave queda tal cual."""
        datos = self._datos_plantilla()
        partes = []
        for literal, campo, _, _ in Formatter().parse(plantilla):
            partes.append(literal)
            if campo is not None:
                partes.append(str(datos.get(campo, "{" + campo + "}")))
        return "".join(partes)

    def _datos_plantilla(self) -> dict[str, Any]:
        educacion = self.perfil.get("education", [])
        return {
            "total": self.anios.get("total", 0),
            "web": max(self.anios.get("full_stack", 0), self.anios.get("react", 0), 1),
            "titulo": educacion[0].get("degree", "") if educacion else "",
        }

    @staticmethod
    def _enumerar_ingles(items: list[str]) -> str:
        if len(items) <= 1:
            return items[0] if items else ""
        return ", ".join(items[:-1]) + " and " + items[-1]

    def _skills_principales(self, tope: int = 7) -> list[str]:
        """Las habilidades del perfil ordenadas por los anos registrados."""
        declaradas = self.perfil.get("main_skills", [])
        def anios_de(skill: str) -> float:
            clave = sin_tildes(skill).replace(" ", "_").replace("/", "_")
            valor = self.anios.get(clave)
            return float(valor) if isinstance(valor, (int, float)) else 0.0
        return sorted(declaradas, key=anios_de, reverse=True)[:tope]

    @staticmethod
    def _enumerar(items: list[str]) -> str:
        if len(items) == 1:
            return items[0]
        return ", ".join(items[:-1]) + " y " + items[-1]
