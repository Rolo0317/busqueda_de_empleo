"""Conexion a Edge con Playwright, con una pestana propia por plataforma.

El bot se engancha por CDP al Edge que abre abrir_navegador_bot.ps1, con la
sesion ya iniciada. Si ese Edge no responde, lo reinicia con el mismo lanzador:
perder la ventana ya no mata la corrida, como pasaba con Selenium.

Playwright ademas emite clics y teclas por el protocolo del navegador, no por
JavaScript, que es lo que React exige para dar por valido un formulario.
"""
from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from config import Settings

PUERTO_POR_DEFECTO = "localhost:9222"
SEGUNDOS_ESPERA_ELEMENTO = 15
SEGUNDOS_ESPERA_CARGA = 45
SEGUNDOS_ENGANCHE = 30

# El mismo lanzador que usa la persona: un solo sitio que sabe abrir el Edge
# del bot con su perfil y sus argumentos.
LANZADOR = Path(__file__).resolve().parents[2] / "abrir_navegador_bot.ps1"


class NavegadorNoDisponible(RuntimeError):
    """El Edge con puerto de depuracion no esta abierto."""


class Navegador:
    """Da a cada plataforma su propia pestana y la mantiene viva.

    El Edge del bot es solo del bot: al conectar cierra pestanas rotas y en
    blanco, y deja una sola pestana por sitio. Nunca cierra la ultima.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._playwright = None
        self._browser: Browser | None = None
        self._contexto: BrowserContext | None = None
        self._por_plataforma: dict[str, Page] = {}

    # ------------------------------------------------------------- ciclo de vida

    def __enter__(self) -> "Navegador":
        self.abrir()
        return self

    def __exit__(self, *_) -> None:
        self.cerrar()

    def abrir(self) -> None:
        direccion = self.settings.edge_debugger_address or PUERTO_POR_DEFECTO
        if not direccion.startswith("http"):
            direccion = f"http://{direccion}"

        # Antes de engancharse: Playwright se queda colgado en pestanas rotas
        # (como "http://de/"), y despues ya no hay forma de cerrarlas.
        self._cerrar_pestanas_basura(direccion)

        try:
            self._enganchar(direccion)
        except NavegadorNoDisponible:
            # Un Edge caido o trabado no debe detener la corrida: se reinicia el
            # del bot (las sesiones viven en el perfil, en disco) y se reintenta.
            logging.warning("No se pudo enganchar al navegador; reiniciando el Edge del bot...")
            if not self._reiniciar_navegador(direccion):
                raise
            self._enganchar(direccion)

    def _enganchar(self, direccion: str) -> None:
        """Se conecta por CDP con tiempo limite.

        Sin limite, un navegador trabado dejaba el bot colgado para siempre:
        paso con un Edge que aceptaba la conexion pero nunca terminaba de entregar
        sus pestanas.
        """
        self._playwright = sync_playwright().start()
        try:
            self._browser = self._playwright.chromium.connect_over_cdp(
                direccion, timeout=SEGUNDOS_ENGANCHE * 1000)
        except Exception as error:
            self._playwright.stop()
            self._playwright = None
            raise NavegadorNoDisponible(
                f"No se pudo usar el navegador en {direccion}. "
                "Abrelo con abrir_navegador_bot.ps1 y deja la ventana abierta."
            ) from error

        # El contexto existente trae las cookies y la sesion del usuario;
        # uno nuevo llegaria en blanco a Magneto y Computrabajo.
        self._contexto = (self._browser.contexts[0] if self._browser.contexts
                          else self._browser.new_context())
        # wait_seconds es la pausa de cortesia entre ofertas (3 s), no el tiempo
        # que tarda una pagina en cargar: usarlo aqui hacia fallar cada goto.
        self._contexto.set_default_timeout(SEGUNDOS_ESPERA_ELEMENTO * 1000)
        self._contexto.set_default_navigation_timeout(SEGUNDOS_ESPERA_CARGA * 1000)
        logging.info("Conectado a Edge en %s | pestanas abiertas: %s",
                     direccion, len(self._contexto.pages))

    def cerrar(self) -> None:
        """Cierra las pestanas del bot y suelta la conexion.

        Nunca cierra la ultima pestana: Edge se cierra con ella, y la siguiente
        corrida (la del boton del panel, por ejemplo) ya no encontraria navegador.
        """
        for nombre, pagina in list(self._por_plataforma.items()):
            if not pagina.is_closed() and self._cerrar_si_no_es_la_ultima(pagina):
                logging.info("Pestana de %s cerrada", nombre)
        self._por_plataforma.clear()

        # El navegador queda abierto: es del usuario, no del bot.
        for recurso in (self._browser, self._playwright):
            try:
                recurso.close() if recurso is self._browser else recurso.stop()
            except Exception:
                pass
        self._browser = self._playwright = self._contexto = None

    # ------------------------------------------------------------------ pestanas

    def pagina(self, plataforma: str, url_inicial: str = "") -> Page:
        """Devuelve la pestana de esa plataforma, creandola si hace falta.

        Si la conexion con el navegador se cayo, se reconecta y se reintenta una
        vez: una corrida de horas no puede terminarse porque el contexto murio.
        """
        try:
            return self._pagina(plataforma, url_inicial)
        except Exception as error:
            if not self._conexion_caida(error):
                raise
            logging.warning("Conexion con el navegador perdida; reconectando...")
            self._reconectar()
            return self._pagina(plataforma, url_inicial)

    @staticmethod
    def _conexion_caida(error: Exception) -> bool:
        marcas = ("target page, context or browser has been closed",
                  "browser has been closed", "connection closed")
        return any(m in str(error).lower() for m in marcas)

    def _reconectar(self) -> None:
        """Suelta lo que quede y vuelve a engancharse al navegador."""
        self._por_plataforma.clear()
        for recurso in (self._browser, self._playwright):
            try:
                recurso.close() if recurso is self._browser else recurso.stop()
            except Exception:
                pass
        self._browser = self._playwright = self._contexto = None
        self.abrir()

    def _pagina(self, plataforma: str, url_inicial: str) -> Page:
        if self._contexto is None:
            raise NavegadorNoDisponible("El navegador no esta abierto. Llama a abrir() primero.")

        pagina = self._por_plataforma.get(plataforma)
        if pagina is not None and not pagina.is_closed():
            return pagina

        pagina = self._reutilizar(plataforma, url_inicial) or self._contexto.new_page()
        if url_inicial and pagina.url in ("about:blank", ""):
            pagina.goto(url_inicial, wait_until="domcontentloaded")
        self._por_plataforma[plataforma] = pagina
        self._cerrar_duplicadas(url_inicial, conservada=pagina)
        logging.info("Pestana propia lista para %s", plataforma)
        return pagina

    def _reutilizar(self, plataforma: str, url_inicial: str) -> Page | None:
        """Aprovecha una pestana que el usuario ya tenga en ese sitio.

        Abrir una segunda pestana de Magneto cuando ya hay una es ruido en
        pantalla y una sesion mas que mantener.
        """
        if not url_inicial:
            return None
        sitio = self._sitio(url_inicial)
        tomadas = {id(p) for p in self._por_plataforma.values()}

        for candidata in self._contexto.pages:
            if id(candidata) in tomadas or candidata.is_closed():
                continue
            if self._sitio(candidata.url) == sitio:
                logging.info("Reutilizando pestana existente de %s", plataforma)
                return candidata
        return None

    # --------------------------------------------------------- higiene de pestanas

    @staticmethod
    def _sitio(url: str) -> str:
        """El dominio registrable: login.magneto365.com y www.magneto365.com son
        el mismo sitio, igual que candidato.co.computrabajo.com y co.computrabajo.com."""
        host = urlparse(url).hostname or ""
        return ".".join(host.split(".")[-2:]) if "." in host else host

    @staticmethod
    def _es_basura(url: str) -> bool:
        """Paginas de error y direcciones que no apuntan a ningun sitio.

        "http://de/" y "http://vida/..." salian de partir por los espacios la
        ruta "hoja de vida" del perfil al abrir Edge.
        """
        if url.startswith(("chrome-error://", "edge-error://")):
            return True
        if url.startswith("http"):
            host = urlparse(url).hostname or ""
            return "." not in host and host != "localhost"
        return False

    @staticmethod
    def _reiniciar_navegador(direccion: str) -> bool:
        """Relanza el Edge del bot con su lanzador. Devuelve si quedo escuchando."""
        if not LANZADOR.exists():
            logging.error("No se encontro el lanzador %s", LANZADOR)
            return False
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(LANZADOR)],
                check=False, timeout=90, capture_output=True,
            )
            with urlopen(f"{direccion}/json/version", timeout=10):
                logging.info("Edge del bot reiniciado.")
                return True
        except Exception as error:
            logging.error("No se pudo reiniciar el Edge del bot: %s", str(error)[:90])
            return False

    @classmethod
    def _cerrar_pestanas_basura(cls, direccion: str) -> None:
        """Cierra paginas de error, direcciones rotas y pestanas en blanco sobrantes.

        Usa la API HTTP de depuracion del navegador, que no necesita engancharse
        a cada pestana. Nunca deja el navegador sin pestanas: se cerraria entero.
        """
        try:
            with urlopen(f"{direccion}/json/list", timeout=5) as respuesta:
                objetivos = json.load(respuesta)
        except Exception:
            return  # Sin navegador; abrir() lo reportara al conectar.

        paginas = [o for o in objetivos if o.get("type") == "page"]
        basura = [o for o in paginas if cls._es_basura(o.get("url", ""))]
        if len(paginas) > 1:
            basura += [o for o in paginas if o.get("url") in ("about:blank", "")]

        cerradas = 0
        for objetivo in basura:
            if len(paginas) - cerradas <= 1:
                break
            try:
                with urlopen(f"{direccion}/json/close/{objetivo['id']}", timeout=5):
                    cerradas += 1
            except Exception:
                continue
        if cerradas:
            logging.info("Pestanas basura cerradas: %s", cerradas)

    def _cerrar_duplicadas(self, url_inicial: str, conservada: Page) -> None:
        """Deja una sola pestana por sitio: la que usa la plataforma."""
        if not url_inicial:
            return
        sitio = self._sitio(url_inicial)
        tomadas = {id(p) for p in self._por_plataforma.values()}
        for pagina in list(self._contexto.pages):
            if pagina is conservada or id(pagina) in tomadas or pagina.is_closed():
                continue
            if self._sitio(pagina.url) == sitio and self._cerrar_si_no_es_la_ultima(pagina):
                logging.info("Pestana duplicada de %s cerrada", sitio)

    def _cerrar_si_no_es_la_ultima(self, pagina: Page) -> bool:
        try:
            abiertas = [p for p in self._contexto.pages if not p.is_closed()]
            if len(abiertas) <= 1:
                return False
            pagina.close()
            return True
        except Exception:
            return False
