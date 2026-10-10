"""Seguimiento de postulaciones por correo.

Cada cierto tiempo el bot lee la bandeja, clasifica los correos de la busqueda
(tests, entrevistas, personas escribiendo, avances, rechazos) y los guarda como
eventos en Supabase asociados a la vacante postulada. Si llega algo que exige
a la persona (un test, una entrevista, un reclutador), muestra un aviso.
"""
from __future__ import annotations

import html
import imaplib
import logging
import re
from datetime import datetime, timedelta
from typing import Callable

from utilidades.aviso import avisar
from utilidades.clasificador_correos import Categoria, ClasificadorCorreos, Correo
from utilidades.correo_imap import BuzonGmail, MensajeCorreo
from utilidades.lector_codigos import ahora

# La bandeja se descarga completa: hacerlo en cada ciclo (5 min) es un abuso.
MINUTOS_ENTRE_REVISIONES = 30
# IMAP filtra por dia; dos dias cubren una noche con el bot apagado.
DIAS_HACIA_ATRAS = 2
# Un primer arranque encuentra muchos eventos "nuevos"; no se avisa de lo viejo.
HORAS_PARA_AVISAR = 24
MAXIMO_AVISOS_POR_REVISION = 3

CATEGORIAS_SEGUIDAS = (Categoria.ACCION_REQUERIDA, Categoria.CONTACTO_HUMANO,
                       Categoria.AVANCE, Categoria.RECHAZO)
CATEGORIAS_CON_AVISO = (Categoria.ACCION_REQUERIDA, Categoria.CONTACTO_HUMANO)

# Frases reales que preceden al cargo: "tu postulacion a Ingeniero DBA",
# "solicitud de empleo Analista BI", "Proceso de seleccion para: Jefe de
# Sistemas", "para el puesto de AI Ops Engineer".
PATRON_CARGO = re.compile(
    r"(?:postulaci[oó]n a|solicitud de empleo|puesto de|cargo de|vacante(?: de)?|"
    r"proceso de selecci[oó]n para:)\s+"
    r"(?P<cargo>[^.,;!?¡¿|\n]{3,90}?)"
    r"(?=\s*(?:[.,;!?¡¿|]|\s[-–]\s|\bHola\b|$))",
    re.IGNORECASE)
# Lo que se lee del cuerpo basta con el comienzo; el pie trae textos legales.
CARACTERES_DE_CUERPO = 1500

URL = re.compile(r"https?://[^\s\"'<>)]+")
# Enlaces que llevan a la accion pedida, del mas al menos util.
DOMINIOS_DE_ACCION = ("pandape", "genoma", "evaluar", "hirint", "teams.microsoft", "meet.google",
                      "zoom.us", "calendly", "forms.", "computrabajo", "magneto365")
ENLACES_IGNORADOS = ("unsubscribe", "desuscrib", "/baja", "privacy", "privacidad",
                     ".png", ".jpg", ".gif", "facebook", "instagram", "linkedin.com/company",
                     "twitter", "youtube")


def cargo_mencionado(asunto: str, cuerpo: str = "") -> str | None:
    """El cargo que nombra el correo: primero el asunto, luego el cuerpo.

    Un mismo correo lo repite con ruido distinto ("puesto de Ingeniero de
    Software Danilo, completa..." y "puesto de Ingeniero de Software ."):
    la mencion mas corta es la mas limpia.
    """
    for texto in (asunto, cuerpo[:CARACTERES_DE_CUERPO]):
        menciones = [m.group("cargo").strip() for m in PATRON_CARGO.finditer(texto or "")]
        menciones = [m for m in menciones if len(m) >= 4]
        if menciones:
            return min(menciones, key=len)[:120]
    return None


def enlace_de_accion(*cuerpos: str) -> str | None:
    """El primer enlace que lleva a una prueba, entrevista o mensaje."""
    enlaces = [html.unescape(u).rstrip(".,;") for cuerpo in cuerpos for u in URL.findall(cuerpo or "")]
    utiles = [u for u in enlaces if not any(i in u.lower() for i in ENLACES_IGNORADOS)]
    for dominio in DOMINIOS_DE_ACCION:
        for enlace in utiles:
            if dominio in enlace.lower():
                return enlace[:500]
    return None


class SeguimientoCorreo:
    def __init__(self, buzon: BuzonGmail, registrar: Callable[[dict], bool],
                 clasificador: ClasificadorCorreos | None = None) -> None:
        self._buzon = buzon
        self._registrar = registrar
        self._clasificador = clasificador or ClasificadorCorreos()
        self._ultima_revision: datetime | None = None
        # Message-ID ya enviados a Supabase en esta corrida: no se repiten.
        self._procesados: set[str] = set()

    def revisar_si_toca(self) -> None:
        if self._ultima_revision and ahora() - self._ultima_revision < timedelta(minutes=MINUTOS_ENTRE_REVISIONES):
            return
        self._ultima_revision = ahora()
        try:
            mensajes = self._buzon.mensajes_desde(ahora() - timedelta(days=DIAS_HACIA_ATRAS))
        except (imaplib.IMAP4.error, OSError) as error:
            logging.warning("Seguimiento: no se pudo leer el correo: %s", str(error)[:120])
            return
        nuevos = [m for m in mensajes if m.message_id not in self._procesados]
        avisos = 0
        registrados = 0
        for mensaje in nuevos:
            evento = self._evento(mensaje)
            try:
                nuevo = evento is not None and self._registrar(evento)
            except Exception as error:
                # Sin marcarlo como procesado: se reintenta en la proxima revision.
                logging.warning("Seguimiento: no se guardo un evento: %s", str(error)[:90])
                continue
            self._procesados.add(mensaje.message_id)
            if not nuevo:
                continue
            registrados += 1
            if self._merece_aviso(evento, mensaje) and avisos < MAXIMO_AVISOS_POR_REVISION:
                avisos += 1
                avisar(f"Empleo: {evento['motivo']}", evento["cargo"] or evento["asunto"][:80])
        logging.info("Seguimiento: %d correos revisados, %d eventos nuevos.", len(nuevos), registrados)

    def _evento(self, mensaje: MensajeCorreo) -> dict | None:
        clasificacion = self._clasificador.clasificar(
            Correo(mensaje.remitente, mensaje.asunto, mensaje.texto[:1500]))
        if clasificacion.categoria not in CATEGORIAS_SEGUIDAS:
            return None
        return {
            "message_id": mensaje.message_id,
            "categoria": clasificacion.categoria.value,
            "motivo": clasificacion.motivo,
            "remitente": mensaje.remitente[:200],
            "asunto": mensaje.asunto[:300],
            "cargo": cargo_mencionado(mensaje.asunto, mensaje.texto),
            # En un rechazo el enlace solo es rastreo de la plataforma.
            "enlace": (None if clasificacion.categoria is Categoria.RECHAZO
                       else enlace_de_accion(mensaje.html, mensaje.texto)),
            "recibido_at": mensaje.recibido.isoformat(),
        }

    @staticmethod
    def _merece_aviso(evento: dict, mensaje: MensajeCorreo) -> bool:
        reciente = ahora() - mensaje.recibido < timedelta(hours=HORAS_PARA_AVISAR)
        return reciente and evento["categoria"] in {c.value for c in CATEGORIAS_CON_AVISO}


def crear_seguimiento(usuario: str, clave_aplicacion: str, cliente_supabase) -> SeguimientoCorreo | None:
    """Sin contrasena de aplicacion o sin Supabase no hay donde leer ni guardar."""
    if not (usuario and clave_aplicacion and cliente_supabase):
        return None

    def registrar(evento: dict) -> bool:
        return bool(cliente_supabase.rpc("empleo_registrar_evento", {"p_evento": evento}))

    return SeguimientoCorreo(BuzonGmail(usuario, clave_aplicacion), registrar)
