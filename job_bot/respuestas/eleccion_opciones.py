"""Eleccion de opciones en preguntas de seleccion multiple, contra el perfil.

El fallback anterior tenia "sin experiencia" y "si" entre sus preferencias, asi
que respondia "No tengo experiencia" a una pregunta sobre SQL teniendo seis anos,
y afirmaba haber trabajado en empresas donde nunca estuvo. Aqui cada eleccion se
justifica con un dato del perfil, y ante la duda se prefiere la opcion que no
afirma nada.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

from respuestas.anios_tecnologia import max_anios, tecnologias_mencionadas

# Tecnologias que suelen aparecer en preguntas y que el perfil no registra.
TECNOLOGIAS_AUSENTES = (
    "java", "spring", "php", ".net", "c#", "golang", "go", "angular", "flutter", "kotlin",
    "swift", "ruby", "salesforce", "sap", "databricks", "spark", "airflow", "kubernetes",
    "terraform", "jenkins", "scala", "typescript",
)
# Opciones que niegan: nombrar la tecnologia para decir que no se tiene es honesto.
NEGACIONES_OPCION = ("not comfortable", "no tengo", "no manejo", "no conozco", "neither",
                     "ninguno", "ninguna", "none", "no experience", "sin experiencia")

INFINITO = float("inf")
NUMERO = r"(\d+(?:[.,]\d+)?)"


def _numero(texto: str) -> float:
    return float(texto.replace(",", "."))


def rango_de(opcion: str) -> tuple[float, float] | None:
    """Convierte el texto de una opcion en un rango de anos (desde, hasta)."""
    t = opcion
    if any(m in t for m in ("ninguno", "ninguna", "sin experiencia", "no tengo")):
        return (0.0, 0.0)
    m = re.search(r"menos de\s*" + NUMERO, t)
    if m:
        return (0.0, _numero(m.group(1)) - 1e-9)
    m = re.search(r"(?:mas de|mayor a|superior a)\s*" + NUMERO, t) or re.search(NUMERO + r"\s*(?:o mas|\+)", t)
    if m:
        return (_numero(m.group(1)), INFINITO)
    m = re.search(NUMERO + r"\s*(?:a|-|y)\s*" + NUMERO, t)
    if m:
        return (_numero(m.group(1)), _numero(m.group(2)))
    m = re.fullmatch(r"\s*" + NUMERO + r"\s*(?:anos?)?\s*", t)
    if m:
        return (_numero(m.group(1)), _numero(m.group(1)))
    return None


def elegir_por_rango(anios: float, opciones) -> str | None:
    """La opcion cuyo rango contiene los anos; si los superan todas, la mas alta."""
    rangos = [(original, rango_de(limpia)) for original, limpia in opciones]
    rangos = [(o, r) for o, r in rangos if r is not None]
    if len(rangos) < 2:
        return None
    for original, (desde, hasta) in rangos:
        if desde <= anios <= hasta:
            return original
    original, _ = max(rangos, key=lambda par: par[1][0])
    return original if anios >= max(r[0] for _, r in rangos) else None

# Como se nombra cada nivel en las opciones tipicas de un formulario.
NIVELES = (
    (4, ("experto", "avanzado", "senior", "alto", "5 o mas", "mas de 5")),
    (3, ("intermedio", "medio", "3 a", "2 a", "mas de 2", "2 o mas")),
    (1, ("basico", "junior", "bajo", "1 ano", "menos de")),
    (0, ("sin experiencia", "no tengo", "ninguno", "ninguna", "no manejo")),
)

# Palabras que delatan una afirmacion de vinculo o credencial.
AFIRMACIONES_RIESGOSAS = ("si, trabaje", "si trabaje", "si, he trabajado", "soy empleado",
                          "actualmente trabajo", "si, tengo titulo", "si, soy")

NEGACIONES = ("no aplica", "no, no", "ninguna de las anteriores", "ninguno", "ninguna",
              "no he trabajado", "no tengo vinculo", "no")


def sin_tildes(texto: str) -> str:
    plano = unicodedata.normalize("NFKD", texto or "")
    return plano.encode("ascii", "ignore").decode("ascii").lower().strip()


class EleccionDeOpciones:
    """Escoge la opcion que el perfil respalda."""

    def __init__(self, perfil: dict[str, Any]) -> None:
        self.perfil = perfil
        self.anios = {sin_tildes(k): v for k, v in perfil.get("experience_years", {}).items()}
        self.skills = [sin_tildes(s) for s in perfil.get("main_skills", [])]
        self.empresas = [sin_tildes(e.get("company", "")) for e in perfil.get("experience", [])]

    def elegir(self, pregunta: str, opciones: list[str]) -> tuple[str, str] | None:
        """Devuelve (opcion, motivo) o None si ninguna regla aplica."""
        if not opciones:
            return None

        texto = sin_tildes(pregunta)
        limpias = [(o, sin_tildes(o)) for o in opciones if o and o.strip()]
        if not limpias:
            return None

        vinculo = self._elegir_por_vinculo(texto, limpias)
        if vinculo:
            return vinculo

        nivel = self._elegir_por_nivel(texto, limpias)
        if nivel:
            return nivel

        return self._elegir_conservadora(limpias)

    # ---------------------------------------------------------------- reglas

    def _elegir_por_vinculo(self, texto: str, opciones) -> tuple[str, str] | None:
        """Preguntas sobre haber trabajado en la empresa o el grupo."""
        marcas = ("experiencia laboral previa", "has trabajado", "trabajaste",
                  "vinculacion laboral", "vinculo con", "eres empleado", "ex empleado")
        if not any(m in texto for m in marcas):
            return None

        trabajo_ahi = any(
            palabras and all(p in texto for p in palabras[:2])
            for palabras in ([p for p in empresa.split() if len(p) > 3] for empresa in self.empresas)
        )
        if trabajo_ahi:
            for original, limpia in opciones:
                if any(a in limpia for a in AFIRMACIONES_RIESGOSAS):
                    return original, "Vinculo confirmado en el perfil"

        # Sin respaldo en el perfil, jamas se afirma el vinculo.
        for negacion in NEGACIONES:
            for original, limpia in opciones:
                if limpia.startswith(negacion) or negacion in limpia:
                    if not any(a in limpia for a in AFIRMACIONES_RIESGOSAS):
                        return original, "Sin vinculo con esa empresa en el perfil"
        return None

    def _elegir_por_nivel(self, texto: str, opciones) -> tuple[str, str] | None:
        """Preguntas de nivel sobre una tecnologia concreta."""
        anios = self._anios_de_la_tecnologia(texto)
        if anios is None:
            return None

        # Opciones con rangos de anos ("Menos de 1", "1 a 2", "Mas de 3"): se
        # elige el rango que contiene los anos reales. Con solo etiquetas,
        # "Mas de 3" no casaba con nada y 6 anos de Python salian como "2 a 3".
        por_rango = elegir_por_rango(anios, opciones)
        if por_rango:
            return por_rango, f"Rango que contiene los {anios:g} anos del perfil"

        # Se busca la opcion cuyo nivel declarado no supere lo que el perfil respalda.
        # El umbral 0 solo aplica si de verdad no hay experiencia: al recorrerlo
        # siempre (anios >= 0 es cierto) se elegia "No tengo experiencia con Power BI"
        # teniendo cuatro anos registrados, que es negarse el puesto por escrito.
        for umbral, etiquetas in NIVELES:
            if umbral == 0 and anios > 0:
                continue
            if anios >= umbral:
                for original, limpia in opciones:
                    if any(e in limpia for e in etiquetas):
                        return original, f"Nivel respaldado por {anios} anos en el perfil"
        return None

    # Cuando las opciones son frases y no etiquetas de nivel, se ordenan por
    # lo que afirman. Responder "Si" a una lista de frases no elige nada y la
    # pregunta queda sin contestar, dejando el boton de enviar deshabilitado.
    FUERZA_OPCION = (
        (0, ("no tengo", "sin experiencia", "no he ", "ninguna", "ninguno", "no manejo",
             "dispuesto a aprender", "no cuento")),
        (1, ("una vez", "basico", "poca", "proyecto personal", "academico", "solo he")),
        (3, ("regularmente", "diariamente", "avanzado", "amplia", "varios proyectos",
             "a diario", "experto", "lidero", "produccion")),
    )

    def elegir_por_afirmacion(self, pregunta: str, opciones: list[str]) -> tuple[str, str] | None:
        """Escoge la frase cuyo alcance corresponde a los anos del perfil."""
        anios = self._anios_de_la_tecnologia(sin_tildes(pregunta))
        if anios is None:
            return None

        # Una opcion que afirma una tecnologia ausente del perfil queda fuera,
        # por fuerte que suene: asi se eligio "I am stronger in Java but can use
        # both" sin tener Java. "both"/"ambos" tambien la afirman si la pregunta
        # nombra una tecnologia que no esta.
        ajenas = self._tecnologias_ajenas(sin_tildes(pregunta))
        candidatas = [o for o in opciones if o and o.strip()
                      and not self._afirma_ajena(sin_tildes(o), ajenas)]
        graduadas = [(self._fuerza(sin_tildes(o)), o) for o in candidatas]
        if not graduadas:
            return None

        if anios <= 0:
            tope = 0
        elif anios < 3:
            tope = 2
        else:
            tope = 3

        admisibles = [(f, o) for f, o in graduadas if f <= tope]
        if not admisibles:
            return None

        fuerza, elegida = max(admisibles, key=lambda par: par[0])
        # Con experiencia registrada jamas se elige la opcion que la niega.
        if anios > 0 and fuerza == 0:
            return None
        return elegida, f"Alcance respaldado por {anios} anos en el perfil"

    def _tecnologias_ajenas(self, texto: str) -> list[str]:
        """Tecnologias nombradas en el texto que el perfil no respalda."""
        propias = {alias for alias, anios in tecnologias_mencionadas(texto, self.perfil) if anios > 0}
        return [t for t in TECNOLOGIAS_AUSENTES
                if t not in propias and re.search(r"(?<![a-z0-9])" + re.escape(t) + r"(?![a-z0-9])", texto)]

    @staticmethod
    def _afirma_ajena(opcion: str, ajenas: list[str]) -> bool:
        if any(m in opcion for m in NEGACIONES_OPCION):
            return False
        nombra = any(re.search(r"(?<![a-z0-9])" + re.escape(t) + r"(?![a-z0-9])", opcion) for t in ajenas)
        abarca = bool(ajenas) and any(m in opcion for m in ("both", "ambos", "ambas", "todos", "all of"))
        return nombra or abarca

    @classmethod
    def _fuerza(cls, limpia: str) -> int:
        for valor, marcas in cls.FUERZA_OPCION:
            if any(m in limpia for m in marcas):
                return valor
        return 2

    def _elegir_conservadora(self, opciones) -> tuple[str, str] | None:
        """Ante la duda, la opcion que no afirma nada."""
        for negacion in NEGACIONES:
            for original, limpia in opciones:
                if limpia == negacion or limpia.startswith(negacion):
                    return original, "Opcion conservadora: no afirma nada sin respaldo"
        return None

    # --------------------------------------------------------------- apoyo

    def _anios_de_la_tecnologia(self, texto: str) -> float | None:
        """Anos que el perfil registra para lo que nombra la pregunta (el mayor)."""
        return max_anios(texto, self.perfil)
