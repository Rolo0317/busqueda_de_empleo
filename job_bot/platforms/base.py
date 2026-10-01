"""Contrato que toda bolsa de empleo debe cumplir."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import ClassVar

from playwright.sync_api import Page

from browser.navegador import Navegador
from config import Settings
from models.job_offer import JobOffer


class BasePlatform(ABC):
    """Una bolsa de empleo: busca ofertas y se postula a ellas.

    El nombre identifica las ofertas que produce, para que el aplicador sepa a
    que plataforma devolverlas sin preguntarle a nadie.
    """

    nombre: ClassVar[str] = "Desconocida"
    url_inicial: ClassVar[str] = ""

    def __init__(self, navegador: Navegador, settings: Settings, tracker=None) -> None:
        self.navegador = navegador
        self.settings = settings
        self.tracker = tracker

    @property
    def pagina(self) -> Page:
        """La pestana propia de esta plataforma, creada la primera vez que se pide."""
        return self.navegador.pagina(self.nombre, self.url_inicial)

    def abrir(self, url: str) -> bool:
        """Navega a la URL. Devuelve False si la pagina ya no existe.

        Una oferta vencida responde con error HTTP y Playwright lo lanza como
        excepcion; para el bot eso no es un fallo, es una oferta menos.
        """
        try:
            respuesta = self.pagina.goto(url, wait_until="domcontentloaded")
        except Exception as error:
            logging.info("No se pudo abrir %s: %s", url[:70], str(error).splitlines()[0][:90])
            return False

        # Magneto responde 500 sirviendo una pagina de error normal: sin mirar el
        # codigo, el bot intentaba rellenar un formulario que no existe y acababa
        # reportando "formulario incompleto" por una caida ajena.
        if respuesta is not None and respuesta.status >= 400:
            logging.info("La oferta respondio HTTP %s: %s", respuesta.status, url[:70])
            return False
        return True

    @abstractmethod
    def search(self, keyword: str) -> list[JobOffer]:
        raise NotImplementedError

    @abstractmethod
    def apply(self, offer: JobOffer) -> str:
        raise NotImplementedError

    def ensure_logged_in(self) -> None:
        """Por defecto no hace falta sesion; quien la necesite lo sobreescribe."""
        return None
