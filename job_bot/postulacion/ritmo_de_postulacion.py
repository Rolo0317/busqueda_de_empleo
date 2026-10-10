"""Cuanto y cuando postula el bot, y a que no debe postular dos veces.

- Repetidas: la misma vacante llega con otra URL, porque la empresa la
  republica o porque esta en Magneto y en Computrabajo. En la base habia unas
  24 de 562 postulaciones repetidas por empresa y cargo.
- Tope diario: un cambio de filtros llego a disparar 150 postulaciones en un
  dia (23/09); lo normal son 20-45.
- Horario: postular a las 3 a. m. delata al bot ante el reclutador.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime, time

from modelos.job_offer import JobOffer

# Ventana en la que una postulacion previa cuenta para detectar repetidas.
DIAS_DE_HISTORIAL = 60
EMPRESAS_SIN_NOMBRE = {"", "no especificada", "confidencial", "empresa confidencial", "importante empresa"}
# Sin empresa conocida, solo un cargo muy especifico identifica la vacante:
# "Desarrollador de software" de dos empresas ocultas no es la misma oferta.
PALABRAS_MINIMAS_SIN_EMPRESA = 6
SUFIJOS_LEGALES = re.compile(r"\b(s\s?a\s?s|s\s?a|ltda|limitada|s\s?en\s?c|e\s?u)\b")
# "Ejecutivo(a)", "Desarrollador/a": la marca de genero no cambia la vacante.
MARCA_DE_GENERO = re.compile(r"\(\s*[ao]\s*\)|/\s*[ao]\b")


def _plano(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", sin_tildes.lower()).strip()


def clave_de_vacante(titulo: str, empresa: str) -> str | None:
    """Identifica la vacante por empresa y cargo; None si no alcanza para saberlo."""
    cargo = _plano(MARCA_DE_GENERO.sub("", titulo or ""))
    nombre = _plano(empresa)
    if nombre in EMPRESAS_SIN_NOMBRE:
        return f"?|{cargo}" if len(cargo.split()) >= PALABRAS_MINIMAS_SIN_EMPRESA else None
    nombre = re.sub(r"\s+", " ", SUFIJOS_LEGALES.sub(" ", nombre)).strip()
    return f"{nombre}|{cargo}" if nombre and cargo else None


class HistorialDePostulaciones:
    """Las postulaciones recientes: alimenta el tope diario y las repetidas."""

    def __init__(self, postulaciones: list[dict]) -> None:
        self._claves: dict[str, str] = {}
        self._fechas: list[datetime] = []
        for fila in postulaciones:
            self._anotar(fila.get("titulo", ""), fila.get("empresa", ""), fila.get("plataforma", ""))
            if fila.get("aplicada"):
                self._fechas.append(datetime.fromisoformat(str(fila["aplicada"])))

    def plataforma_previa(self, oferta: JobOffer) -> str | None:
        """Donde ya se postulo a esta vacante, o None si es nueva."""
        clave = clave_de_vacante(oferta.title, oferta.company)
        return self._claves.get(clave) if clave else None

    def registrar(self, oferta: JobOffer, cuando: datetime) -> None:
        self._anotar(oferta.title, oferta.company, oferta.platform)
        self._fechas.append(cuando)

    def postuladas_desde(self, momento: datetime) -> int:
        return sum(1 for fecha in self._fechas if fecha >= momento)

    def _anotar(self, titulo: str, empresa: str, plataforma: str) -> None:
        clave = clave_de_vacante(titulo, empresa)
        if clave:
            self._claves.setdefault(clave, plataforma or "otra plataforma")


class RitmoDePostulacion:
    """Tope diario y horario en que el bot continuo puede postular."""

    def __init__(self, tope_diario: int, hora_inicio: int, hora_fin: int) -> None:
        self.tope_diario = tope_diario
        self._inicio = time(hour=hora_inicio)
        self._fin = time(hour=hora_fin) if hora_fin < 24 else time.max
        self.descripcion_horario = f"{hora_inicio:02d}:00-{hora_fin:02d}:00"

    def dentro_de_horario(self, ahora: datetime) -> bool:
        return self._inicio <= ahora.time() < self._fin

    def cupo_de_hoy(self, historial: HistorialDePostulaciones, ahora: datetime) -> int | None:
        """Postulaciones que quedan hoy; None si no hay tope (0)."""
        if self.tope_diario <= 0:
            return None
        medianoche = datetime.combine(ahora.date(), time.min, tzinfo=ahora.tzinfo)
        return max(0, self.tope_diario - historial.postuladas_desde(medianoche))
