"""Computrabajo Colombia sobre Playwright.

La busqueda es publica; la postulacion exige sesion iniciada en el navegador.
Se postula navegando a la URL que el propio boton lleva en su atributo, porque
ese boton es un <span> y pulsarlo depende de que quede visible.
"""
from __future__ import annotations

import logging
import re
from urllib.parse import urljoin

from playwright.sync_api import ElementHandle, TimeoutError as PlaywrightTimeout

from core.url_utils import canonicalize_url
from models.job_offer import JobOffer
from platforms import lectura_oferta as lectura
from platforms.base import BasePlatform
from platforms.cuestionario_computrabajo import CuestionarioComputrabajo
from services.ai_answerer import FreeAiAnswerClient
from services.question_answerer import CandidateQuestionAnswerer


class ComputrabajoPlatform(BasePlatform):
    nombre = "Computrabajo"
    url_inicial = "https://co.computrabajo.com/"
    BASE_URL = "https://co.computrabajo.com"

    TARJETA = "article.box_offer"
    ENLACE_TITULO = "h2 a"
    EMPRESA = "a.t_ellipsis"
    # span.fx_none y span.fwB llevan la calificacion de la empresa, no la ciudad.
    CIUDAD = "p.fs16 span.mr10:not(.fx_none):not(.fwB)"
    # El salario y la modalidad son hermanos de p.fs16, no descendientes.
    EXTRAS = "span.dIB"
    FECHA = "p.fs13"
    PATRON_SALARIO = re.compile(r"\$\s*[\d.,]+")
    PAGINAS_POR_BUSQUEDA = 3

    # El boton de postular es un <span>, no un <button> ni un <a>: buscar solo
    # botones y enlaces era la razon por la que nunca se encontraba.
    SELECTOR_APLICAR = "[data-href-offer-apply]"
    SELECTOR_POSTULADO = "span.tag.postulated, [applied-offer-tag]"
    SELECTOR_ACCESO = "[data-href-access]"

    CONFIRMACIONES = ("te aplicaste correctamente", "hemos adjuntado tu hoja de vida",
                      # Lo que muestra el enlace de postular cuando la postulacion ya
                      # existe. Sin esta frase, 43 ofertas ya postuladas se reabrian
                      # en cada ciclo como "formulario incompleto".
                      "ya aplicaste a esta oferta",
                      "haz seguimiento del proceso", "postulacion enviada", "te has postulado",
                      "ya te postulaste", "hoja de vida enviada", "postulacion exitosa")
    PASOS_ADICIONALES = ("preguntas", "completa tu perfil", "responde")

    # Al terminar, Computrabajo lleva a esta ruta. Es la senal mas fiable:
    # no depende de como redacte el mensaje de exito.
    RUTA_POSTULADO = "/candidate/postapply"

    def __init__(self, navegador, settings, tracker=None) -> None:
        super().__init__(navegador, settings, tracker)
        # El mismo cerebro que decide en Magneto: lo que cambia es el formulario.
        self.question_answerer = CandidateQuestionAnswerer(
            settings.candidate_profile_path,
            ai_client=FreeAiAnswerClient(settings),
        )

    # ------------------------------------------------------------------ busqueda

    def search(self, keyword: str) -> list[JobOffer]:
        """Lee varias paginas de resultados.

        Con solo la primera pagina (20 ofertas) el bot agoto las busquedas en
        tres dias: cada ciclo revisaba las mismas 292 ofertas y no postulaba a
        ninguna. Tres paginas dan 60 ofertas distintas por palabra clave.
        """
        base = f"{self.BASE_URL}/trabajo-de-{lectura.slug(keyword)}"
        ofertas: list[JobOffer] = []
        vistas: set[str] = set()

        for numero in range(1, self.PAGINAS_POR_BUSQUEDA + 1):
            url = base if numero == 1 else f"{base}?p={numero}"
            logging.info("Buscando en Computrabajo: %s", url)
            nuevas = self._leer_pagina(url, vistas)
            ofertas.extend(nuevas)
            if not nuevas:
                break  # la pagina vino vacia o repetida: no hay mas resultados

        logging.info("Computrabajo: %s ofertas extraidas", len(ofertas))
        return ofertas

    def _leer_pagina(self, url: str, vistas: set[str]) -> list[JobOffer]:
        """Las ofertas de una pagina de resultados que aun no se habian visto."""
        if not self.abrir(url):
            return []
        try:
            self.pagina.wait_for_selector(self.TARJETA, timeout=15000)
        except PlaywrightTimeout:
            return []

        nuevas: list[JobOffer] = []
        for tarjeta in self.pagina.query_selector_all(self.TARJETA):
            oferta = self._leer_tarjeta(tarjeta)
            if oferta is None:
                continue
            clave = canonicalize_url(str(oferta.url))
            if clave in vistas:
                continue
            vistas.add(clave)
            nuevas.append(oferta)
        return nuevas

    def _leer_tarjeta(self, tarjeta: ElementHandle) -> JobOffer | None:
        enlace = tarjeta.query_selector(self.ENLACE_TITULO)
        if enlace is None:
            return None

        href = (enlace.get_attribute("href") or "").split("#")[0]
        url = canonicalize_url(urljoin(self.BASE_URL, href))
        titulo = (enlace.inner_text() or "").strip()
        if not url or len(titulo) < 3:
            return None

        extras = [(e.inner_text() or "").strip()
                  for e in tarjeta.query_selector_all(self.EXTRAS)]

        return JobOffer(
            platform=self.nombre,
            title=titulo,
            company=self._texto(tarjeta, self.EMPRESA, "No especificada"),
            url=url,
            city=self._texto(tarjeta, self.CIUDAD, "No especificada"),
            salary=self._salario(extras),
            published_at=self._texto(tarjeta, self.FECHA, ""),
            description=(tarjeta.inner_text() or "").strip(),
        )

    def _salario(self, extras: list[str]) -> str:
        for texto in extras:
            if self.PATRON_SALARIO.search(texto):
                return texto
        return "No especificado"

    @staticmethod
    def _texto(raiz: ElementHandle, selector: str, por_defecto: str) -> str:
        elemento = raiz.query_selector(selector)
        if elemento is None:
            return por_defecto
        return (elemento.inner_text() or "").strip() or por_defecto

    # --------------------------------------------------------------- postulacion

    def apply(self, offer: JobOffer) -> str:
        logging.info("Computrabajo: abriendo %s", offer.url)
        if not self.abrir(str(offer.url)):
            return "no disponible"

        if self._ya_postulado():
            logging.info("Computrabajo: ya estabas postulado a esta oferta")
            return "no disponible"

        enlace = self._enlace_de_postulacion()
        if enlace is None:
            if self._sin_sesion():
                logging.warning("Computrabajo sin sesion iniciada: no se puede postular.")
                return "requiere sesion"
            return "no disponible"

        if not self.abrir(enlace):
            return "no disponible"
        self.pagina.wait_for_timeout(3000)

        self._contestar_preguntas_de_seleccion()
        return self._resultado_postulacion()

    def _contestar_preguntas_de_seleccion(self) -> None:
        """Completa las preguntas previas al envio, si la oferta las pide.

        Sin este paso la postulacion se quedaba en la pantalla del cuestionario
        y nunca llegaba a la empresa.
        """
        cuestionario = CuestionarioComputrabajo(self.pagina)
        if not cuestionario.abierto():
            return

        preguntas = [p for p in cuestionario.leer() if not p.respondida]
        for indice, pregunta in enumerate(preguntas, 1):
            decision = self.question_answerer.answer(pregunta.texto, pregunta.opciones)
            if not decision.should_answer or decision.value is None:
                logging.info("  %s. omitida | %s | opciones=%s",
                             indice, pregunta.texto[:80], pregunta.opciones)
                continue
            valor = str(decision.value)
            puesta = (cuestionario.elegir(pregunta, valor) if pregunta.tipo == "opciones"
                      else cuestionario.escribir(pregunta, valor))
            if puesta:
                logging.info("  %s. respondida | %s -> %s", indice, pregunta.texto[:55], valor[:55])
            else:
                logging.warning("  %s. sin poder responder | %s | opciones=%s",
                                indice, pregunta.texto[:80], pregunta.opciones)

        # Con una pregunta vacia el formulario no se envia y la pagina vuelve sin
        # avisar nada. Mejor decirlo aqui, con la pregunta, que adivinarlo despues.
        vacias = cuestionario.sin_responder()
        if vacias:
            for pregunta in vacias:
                logging.warning("  queda sin responder: %s | opciones=%s",
                                pregunta.texto[:90], pregunta.opciones)
            return

        if not cuestionario.enviar():
            return
        self.pagina.wait_for_timeout(4000)

        # Hay ofertas cuyo formulario se envia sin confirmar nada y devuelve a
        # la misma pantalla. Se deja constancia para no darla por postulada.
        if self.RUTA_POSTULADO not in self.pagina.url:
            logging.warning("Computrabajo no confirmo tras enviar la HdV | url=%s",
                            self.pagina.url[:90])

    def _enlace_de_postulacion(self) -> str | None:
        """Extrae la URL de postulacion del atributo del boton.

        Computrabajo sirve la postulacion por varias rutas segun la oferta
        (/candidate/apply/ o /match/), asi que exigir una ruta concreta dejaba
        sin postular a casi todas. El atributo ya es la señal: si esta, es el
        enlace de postular. Se navega a el en vez de pulsar, porque el control
        es un <a> pegado al de guardar y el clic puede caer en el equivocado.
        """
        for elemento in self.pagina.query_selector_all(self.SELECTOR_APLICAR):
            enlace = (elemento.get_attribute("data-href-offer-apply") or "").strip()
            if enlace:
                return urljoin(self.BASE_URL, enlace)
        return None

    def _ya_postulado(self) -> bool:
        return any(m.is_visible() for m in self.pagina.query_selector_all(self.SELECTOR_POSTULADO))

    def _sin_sesion(self) -> bool:
        """Sin sesion, Computrabajo apunta al acceso en vez de a la postulacion.

        El mismo <a> lleva los dos atributos, acceso y postulacion: mirar solo
        el de acceso daba "sin sesion" en todas las ofertas y no se postulaba
        a ninguna. Manda el de postulacion cuando esta presente.
        """
        if self._enlace_de_postulacion():
            return False
        url = self.pagina.url.lower()
        if "acceso" in url or "account/login" in url:
            return True
        return bool(self.pagina.query_selector(self.SELECTOR_ACCESO))

    def _resultado_postulacion(self) -> str:
        cuerpo = lectura.normalizar(self._texto_pagina())
        url = self.pagina.url.lower()

        if "acceso" in url or "login" in url:
            return "requiere sesion"
        if self.RUTA_POSTULADO in url:
            logging.info("Computrabajo confirmo la postulacion.")
            return "aplicado"
        if any(s in cuerpo for s in self.CONFIRMACIONES):
            return "aplicado"
        if any(s in cuerpo for s in self.PASOS_ADICIONALES):
            logging.info("Computrabajo pide pasos adicionales en esta oferta.")
            return "requiere pasos adicionales"
        if self._ya_postulado():
            return "aplicado"
        return "formulario incompleto"

    def _texto_pagina(self) -> str:
        try:
            return self.pagina.inner_text("body")
        except Exception:
            return ""
