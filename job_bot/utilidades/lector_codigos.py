"""Lee de Gmail (IMAP) los codigos de acceso que mandan las plataformas.

Magneto no pide contrasena: envia un codigo de 6 digitos al correo. Con una
"contrasena de aplicacion" de Google el bot lo lee solo; sin ella, el login
espera a que la persona lo escriba en la ventana del navegador.
"""
from __future__ import annotations

import imaplib
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Protocol

from utilidades.correo_imap import BuzonGmail

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
    def __init__(self, buzon: BuzonGmail) -> None:
        self._buzon = buzon

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
        recientes: list[tuple[datetime, str]] = []
        for remitente in remitentes:
            for mensaje in self._buzon.mensajes_desde(desde - TOLERANCIA_RELOJ, remitente):
                codigo = codigo_en_texto(mensaje.texto) or codigo_en_texto(mensaje.html)
                if codigo:
                    recientes.append((mensaje.recibido, codigo))
        return max(recientes)[1] if recientes else None


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
        return LectorCodigosGmail(BuzonGmail(usuario, clave_aplicacion))
    return SinLectorDeCorreo()


def ahora() -> datetime:
    return datetime.now(timezone.utc)
