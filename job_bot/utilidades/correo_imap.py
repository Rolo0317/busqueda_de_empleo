"""Lectura de Gmail por IMAP, compartida por el login de Magneto y el seguimiento.

Siempre en modo solo lectura: el bot nunca marca correos como leidos ni los
mueve. Necesita una contrasena de aplicacion de Google (CORREO_CODIGOS_CLAVE_APP).
"""
from __future__ import annotations

import email
import email.policy
import html as html_lib
import imaplib
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from email.header import decode_header, make_header
from email.message import Message
from email.utils import parsedate_to_datetime

SERVIDOR_GMAIL = "imap.gmail.com"
# Tope por consulta: el seguimiento revisa unas horas; mas de esto es una bandeja
# vieja que no vale la pena reprocesar de una vez.
MAXIMO_MENSAJES = 150


@dataclass(frozen=True)
class MensajeCorreo:
    message_id: str
    remitente: str
    asunto: str
    texto: str          # cuerpo en texto plano (sin etiquetas HTML)
    html: str           # cuerpo HTML crudo, para extraer enlaces
    recibido: datetime


class BuzonGmail:
    def __init__(self, usuario: str, clave_aplicacion: str) -> None:
        self._usuario = usuario
        # Google la muestra en grupos de 4 con espacios; IMAP la quiere seguida.
        self._clave = clave_aplicacion.replace(" ", "")

    def mensajes_desde(self, desde: datetime, remitente: str | None = None) -> list[MensajeCorreo]:
        """Los mensajes de la bandeja recibidos desde esa fecha (por dia, en IMAP)."""
        criterio = f'SINCE "{desde.astimezone(timezone.utc).strftime("%d-%b-%Y")}"'
        if remitente:
            criterio = f'(FROM "{remitente}" {criterio})'
        with imaplib.IMAP4_SSL(SERVIDOR_GMAIL) as imap:
            imap.login(self._usuario, self._clave)
            imap.select("INBOX", readonly=True)
            _, datos = imap.search(None, criterio)
            mensajes = []
            for numero in datos[0].split()[-MAXIMO_MENSAJES:]:
                _, partes = imap.fetch(numero, "(BODY.PEEK[])")
                # La politica moderna entiende cabeceras con UTF-8 crudo (Computrabajo
                # las manda asi); la antigua las convertia en simbolos de reemplazo.
                mensaje = _a_mensaje(email.message_from_bytes(partes[0][1], policy=email.policy.default))
                if mensaje and mensaje.recibido >= desde:
                    mensajes.append(mensaje)
            return mensajes


def _a_mensaje(crudo: Message) -> MensajeCorreo | None:
    try:
        recibido = parsedate_to_datetime(crudo["Date"])
    except (TypeError, ValueError):
        return None
    if recibido.tzinfo is None:
        recibido = recibido.replace(tzinfo=timezone.utc)
    texto, html = [], []
    for parte in crudo.walk():
        if parte.get_content_maintype() != "text":
            continue
        contenido = (parte.get_payload(decode=True) or b"").decode(parte.get_content_charset() or "utf-8", "ignore")
        (html if parte.get_content_subtype() == "html" else texto).append(contenido)
    cuerpo_html = "\n".join(html)
    # El HTML manda: hay remitentes cuya parte "texto plano" es CSS suelto.
    cuerpo_texto = html_a_texto(cuerpo_html) if cuerpo_html else html_lib.unescape("\n".join(texto))
    return MensajeCorreo(
        message_id=(crudo["Message-ID"] or f"{crudo['Date']}|{crudo['Subject']}").strip(),
        remitente=_decodificar(crudo["From"]),
        asunto=_una_linea(_decodificar(crudo["Subject"])),
        texto=_una_linea(cuerpo_texto),
        html=cuerpo_html,
        recibido=recibido,
    )


def html_a_texto(cuerpo_html: str) -> str:
    """El texto visible del HTML: sin estilos, scripts, etiquetas ni entidades."""
    sin_bloques = re.sub(r"(?is)<(style|script|head)\b.*?</\1>", " ", cuerpo_html)
    return html_lib.unescape(re.sub(r"<[^>]+>", " ", sin_bloques))


def _una_linea(texto: str) -> str:
    # Los asuntos largos llegan partidos en varias lineas (cabecera plegada) y
    # algunos remitentes escriben las tildes descompuestas ("o" + acento).
    return unicodedata.normalize("NFC", re.sub(r"\s+", " ", texto).strip())


def _decodificar(valor: str | None) -> str:
    if not valor:
        return ""
    try:
        return str(make_header(decode_header(valor)))
    except (UnicodeDecodeError, LookupError):
        return valor
