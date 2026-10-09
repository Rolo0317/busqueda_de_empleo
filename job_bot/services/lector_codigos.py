"""Lee de Gmail (IMAP) los codigos de acceso que mandan las plataformas.

Magneto no pide contrasena: envia un codigo de 6 digitos al correo. Con una
"contrasena de aplicacion" de Google el bot lo lee solo; sin ella, el login
espera a que la persona lo escriba en la ventana del navegador.
"""
from __future__ import annotations

import email
import imaplib
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from email.message import Message
from email.utils import parsedate_to_datetime
from typing import Protocol

SERVIDOR_GMAIL = "imap.gmail.com"
SEGUNDOS_ENTRE_CONSULTAS = 5
# El reloj del servidor de correo y el de la PC no coinciden al segundo.
TOLERANCIA_RELOJ = timedelta(seconds=90)
CODIGO_SEIS_DIGITOS = re.compile(r"(?<!\d)(\d{6})(?!\d)")


class FuenteDeCodigos(Protocol):
    def esperar_codigo(self, remitentes: tuple[str, ...], desde: datetime,
                       segundos: int) -> str | None:
        ...


class SinLectorDeCorreo:
    """Cuando no hay contrasena de aplicacion: el codigo lo escribe la persona."""

    def esperar_codigo(self, remitentes: tuple[str, ...], desde: datetime,
                       segundos: int) -> str | None:
        return None


class LectorCodigosGmail:
    def __init__(self, usuario: str, clave_aplicacion: str) -> None:
        self._usuario = usuario
        # Google la muestra en grupos de 4 con espacios; IMAP la quiere seguida.
        self._clave = clave_aplicacion.replace(" ", "")

    def esperar_codigo(self, remitentes: tuple[str, ...], desde: datetime,
                       segundos: int) -> str | None:
        limite = time.time() + segundos
        while time.time() < limite:
            try:
                codigo = self._buscar(remitentes, desde)
            except (imaplib.IMAP4.error, OSError) as error:
                logging.warning("No se pudo leer el correo para el codigo: %s", str(error)[:120])
                return None
            if codigo:
                return codigo
            time.sleep(SEGUNDOS_ENTRE_CONSULTAS)
        return None

    def _buscar(self, remitentes: tuple[str, ...], desde: datetime) -> str | None:
        with imaplib.IMAP4_SSL(SERVIDOR_GMAIL) as imap:
            imap.login(self._usuario, self._clave)
            imap.select("INBOX", readonly=True)
            dia = desde.astimezone(timezone.utc).strftime("%d-%b-%Y")
            recientes: list[tuple[datetime, str]] = []
            for remitente in remitentes:
                _, datos = imap.search(None, f'(FROM "{remitente}" SINCE "{dia}")')
                for numero in datos[0].split()[-5:]:
                    _, partes = imap.fetch(numero, "(RFC822)")
                    mensaje = email.message_from_bytes(partes[0][1])
                    fecha = parsedate_to_datetime(mensaje["Date"])
                    if fecha < desde - TOLERANCIA_RELOJ:
                        continue
                    codigo = _codigo_en(mensaje)
                    if codigo:
                        recientes.append((fecha, codigo))
            return max(recientes)[1] if recientes else None


def _codigo_en(mensaje: Message) -> str | None:
    for parte in mensaje.walk():
        if parte.get_content_maintype() != "text":
            continue
        contenido = parte.get_payload(decode=True) or b""
        texto = contenido.decode(parte.get_content_charset() or "utf-8", "ignore")
        codigo = codigo_en_texto(texto)
        if codigo:
            return codigo
    return None


def codigo_en_texto(texto: str) -> str | None:
    """El codigo de 6 digitos que sigue a la palabra "codigo".

    Los enlaces de seguimiento del correo traen otros numeros largos: se quitan
    las URL y las etiquetas, y se busca despues de la palabra clave.
    """
    limpio = re.sub(r"https?://\S+|<[^>]+>", " ", texto)
    clave = re.search(r"c[oó]digo", limpio, re.IGNORECASE)
    encontrado = CODIGO_SEIS_DIGITOS.search(limpio, clave.end() if clave else 0)
    return encontrado.group(1) if encontrado else None


def crear_fuente_de_codigos(usuario: str, clave_aplicacion: str) -> FuenteDeCodigos:
    if usuario and clave_aplicacion:
        return LectorCodigosGmail(usuario, clave_aplicacion)
    return SinLectorDeCorreo()


def ahora() -> datetime:
    return datetime.now(timezone.utc)
