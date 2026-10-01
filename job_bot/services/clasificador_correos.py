"""Clasifica correos de busqueda de empleo por lo que exigen del candidato.

La bandeja se llena de alertas y boletines de las bolsas; lo que de verdad
importa son unos pocos correos al dia. Este modulo separa lo accionable del
ruido sin depender de Gmail: recibe los campos ya extraidos y devuelve una
clasificacion, de modo que se puede probar sin red.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class Categoria(str, Enum):
    """Que exige el correo del candidato, de mas a menos urgente."""

    ACCION_REQUERIDA = "accion_requerida"   # pruebas, entrevistas, documentos
    CONTACTO_HUMANO = "contacto_humano"     # una persona escribio directamente
    AVANCE = "avance"                       # la candidatura cambio de estado
    CONFIRMACION = "confirmacion"           # acuse de recibo, no exige nada
    RECHAZO = "rechazo"
    RUIDO = "ruido"                         # alertas, boletines, recomendaciones


PRIORIDAD = {
    Categoria.ACCION_REQUERIDA: 0,
    Categoria.CONTACTO_HUMANO: 1,
    Categoria.AVANCE: 2,
    Categoria.RECHAZO: 3,
    Categoria.CONFIRMACION: 4,
    Categoria.RUIDO: 5,
}


@dataclass(frozen=True)
class Correo:
    """Los campos minimos que necesita la clasificacion."""

    remitente: str
    asunto: str
    resumen: str
    fecha: str = ""

    @property
    def texto(self) -> str:
        return f"{self.asunto} {self.resumen}"


@dataclass(frozen=True)
class Clasificacion:
    categoria: Categoria
    motivo: str

    @property
    def prioridad(self) -> int:
        return PRIORIDAD[self.categoria]


def sin_tildes(valor: str) -> str:
    plano = unicodedata.normalize("NFKD", valor or "")
    return plano.encode("ascii", "ignore").decode("ascii").lower()


# Reglas que mandan sobre cualquier otra senal: cierran o exigen accion.
REGLAS_URGENTES: tuple[tuple[Categoria, str, tuple[str, ...]], ...] = (
    (Categoria.RECHAZO, "El proceso se cerro", (
        "no fuiste seleccionado", "no continuaras", "hemos decidido continuar con otros",
        "continuar el proceso con otros", "no hemos avanzado con tu candidatura",
        "no te elegimos", "proceso ha finalizado", "no avanzaste",
        # Magneto titula asi sus rechazos; en la bandeja, todos lo eran.
        "carta de agradecimiento", "agradecimiento candidato",
        "agradecimiento proceso de seleccion",
    )),
    (Categoria.ACCION_REQUERIDA, "Piden completar una prueba o evaluacion", (
        "completa el test", "completa la evaluacion", "inicia las evaluaciones",
        "completa el juego", "prueba tecnica", "assessment", "evaluaciones ya estan listas",
        "completa esta etapa", "test para continuar", "pruebas psicotecnicas",
        "avanzaste a la siguiente etapa",
    )),
    (Categoria.ACCION_REQUERIDA, "Citan a entrevista", (
        "entrevista", "agenda tu", "agendar una cita", "programar una llamada",
        "nos gustaria conocerte", "videollamada",
    )),
    (Categoria.ACCION_REQUERIDA, "Piden documentos o datos", (
        "envianos tu", "adjunta tu", "necesitamos que nos envies", "completa tu perfil",
        "documentos requeridos",
    )),
)

# Reglas informativas: una persona escribiendo pesa mas que estas frases.
REGLAS_INFORMATIVAS: tuple[tuple[Categoria, str, tuple[str, ...]], ...] = (
    (Categoria.AVANCE, "La candidatura avanza", (
        "tu candidatura avanza",
    )),
    # "Nuevo estado en..." suena a avance, pero el enlace de esos correos dice
    # MatchDescartado: es el filtro automatico de Computrabajo descartando el CV.
    # En la bandeja fueron 56 frente a 8 avances reales.
    (Categoria.RECHAZO, "Descarte automatico del filtro de Computrabajo", (
        "novedades en tu postulacion", "actualizacion en tu solicitud",
        "nuevo estado en", "cambio en tu candidatura",
    )),
    (Categoria.CONFIRMACION, "Solo confirma que la postulacion llego", (
        "te postulaste con exito", "hemos recibido tu postulacion",
        "tu hv esta a la espera", "seguimiento de tu candidatura",
        "tu cv ya esta en manos", "postulacion enviada",
    )),
    (Categoria.RUIDO, "Alerta o boletin de vacantes", (
        "nuevos empleos para ti", "ofertas de empleo", "tienen nuevos empleos",
        "mira estas vacantes", "postulate ahora", "tu perfil encaja",
        "oportunidades frescas", "tu proximo empleo en", "nuevas vacantes listas",
        "visualiza como te destacas", "postulaciones pendientes de enviar",
        "necesitan talento", "empleos esperandote",
    )),
)

# Remitentes que nunca son una persona escribiendo.
REMITENTES_AUTOMATICOS = (
    "noreply", "no-reply", "sin-respuesta", "jobalerts", "empleos_co",
    "recomendaciones", "notificaciones", "mailer", "newsletter",
)


class ClasificadorCorreos:
    """Asigna una categoria a cada correo de la busqueda de empleo."""

    def clasificar(self, correo: Correo) -> Clasificacion:
        texto = sin_tildes(correo.texto)

        urgente = self._primera_coincidencia(REGLAS_URGENTES, texto)
        if urgente:
            return urgente

        # Una persona escribiendo vale mas que una frase automatica en el cuerpo:
        # muchos reclutadores incluyen "hemos recibido tu postulacion" en su saludo.
        if self._es_persona(correo):
            return Clasificacion(Categoria.CONTACTO_HUMANO,
                                 "Escribe una persona, no un buzon automatico")

        informativa = self._primera_coincidencia(REGLAS_INFORMATIVAS, texto)
        if informativa:
            return informativa

        return Clasificacion(Categoria.RUIDO, "Sin senales de accion requerida")

    @staticmethod
    def _primera_coincidencia(reglas, texto: str) -> Clasificacion | None:
        for categoria, motivo, frases in reglas:
            if any(frase in texto for frase in frases):
                return Clasificacion(categoria, motivo)
        return None

    def ordenar(self, correos: Iterable[Correo]) -> list[tuple[Correo, Clasificacion]]:
        """Devuelve los correos con su clasificacion, lo urgente primero."""
        clasificados = [(c, self.clasificar(c)) for c in correos]
        return sorted(clasificados, key=lambda par: (par[1].prioridad, par[0].fecha), reverse=False)

    @staticmethod
    def _es_persona(correo: Correo) -> bool:
        remitente = sin_tildes(correo.remitente)
        if any(marca in remitente for marca in REMITENTES_AUTOMATICOS):
            return False
        # Un buzon con nombre y apellido suele ser alguien de seleccion.
        usuario = remitente.split("@")[0]
        return "." in usuario or "_" in usuario
