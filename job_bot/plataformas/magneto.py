"""Magneto365 sobre Playwright.

La version anterior con Selenium llenaba el formulario pero no lograba que la
postulacion quedara registrada: los clics iban por JavaScript y React los
descartaba. Playwright pulsa y escribe por el protocolo del navegador, que es
lo mismo que hace una persona.

Esta clase se ocupa de la sesion, la busqueda y la navegacion; el cuestionario
vive en su propio modulo porque es lo que mas cambia.
"""
from __future__ import annotations

import logging
import re
from contextlib import contextmanager
from time import sleep
from urllib.parse import urljoin

from playwright.sync_api import TimeoutError as PlaywrightTimeout

from navegador.navegador import Navegador
from config import Settings
from utilidades.url_utils import canonicalize_url
from modelos.job_offer import JobOffer
from plataformas import lectura_oferta as lectura
from plataformas.base import BasePlatform
from postulacion.memoria_descartes import OfertasConocidas
from plataformas.cuestionario import CuestionarioMagneto, Pregunta
from plataformas.login_magneto import LoginMagneto
from respuestas.ai_answerer import FreeAiAnswerClient
from utilidades.lector_codigos import crear_fuente_de_codigos
from respuestas.question_answerer import CandidateQuestionAnswerer


class MagnetoPlatform(BasePlatform):
    nombre = "Magneto"
    url_inicial = "https://www.magneto365.com/co"
    BASE_URL = "https://www.magneto365.com"

    SELECTOR_OFERTA = 'a[href*="/empleos/"]'
    PATRON_APLICAR = re.compile(r"aplicar|postular", re.IGNORECASE)
    # "Cerrar" no va aqui: es el boton del modal de exito, y cerrarlo antes de
    # leerlo daba por fallida una postulacion que si habia salido.
    CIERRES = ("Aceptar", "Entendido", "Ahora no")

    # Campos con id conocido del formulario de datos personales.
    CAMPOS_CONOCIDOS = ("email", "emailConfirmation", "identificationNumber",
                        "firstName", "lastName", "phone")

    # Magneto confirma con "Se ha enviado tu aplicacion" en un modal propio.
    # Buscar solo variantes de "postulacion" daba por fallidos envios que si salieron.
    CONFIRMACIONES = (
        "se ha enviado tu aplicacion", "tu aplicacion ha sido enviada", "aplicacion enviada",
        # Magneto avisa asi cuando la oferta ya estaba postulada: sin estas
        # marcas el bot la daba por "no disponible" y la volvia a intentar.
        "ya presentaste el cuestionario", "tu postulacion ha sido enviada",
        "ya completaste este paso",
        "postulacion exitosa", "postulacion enviada", "te has postulado",
        "ya te postulaste", "hemos recibido tu postulacion", "gracias por postularte",
        "aplicaste a esta oferta", "postulacion registrada",
    )
    SEGUNDOS_ESPERANDO_CONFIRMACION = 10

    # Magneto pinta primero un encabezado anonimo y luego lo reemplaza por el
    # menu del usuario: leerlo antes da un "sin sesion" falso.
    MARCAS_ANONIMO = ("iniciar sesion", "crear cuenta", "registrate")
    TEXTO_MINIMO_PAGINA = 200
    INTENTOS_SESION = 15
    MS_ESPERA_PAGINA = 4000
    VUELTAS_MAXIMAS = 8

    def __init__(self, navegador: Navegador, settings: Settings, tracker=None) -> None:
        super().__init__(navegador, settings, tracker)
        self.question_answerer = CandidateQuestionAnswerer(
            settings.candidate_profile_path,
            ai_client=FreeAiAnswerClient(settings),
        )
        if self.tracker:
            self.tracker.ensure_questions_table()

    # -------------------------------------------------------------------- sesion

    def ensure_logged_in(self) -> None:
        self.abrir(f"{self.BASE_URL}/co")
        self._cerrar_avisos()

        if self._hay_sesion():
            logging.info("Sesion de Magneto detectada.")
            return

        if self.settings.magneto_email and self._iniciar_sesion_automatica():
            self.abrir(f"{self.BASE_URL}/co")
            if self._hay_sesion():
                logging.info("Sesion de Magneto iniciada automaticamente.")
                return

        # Sin sesion, Magneto sirve el formulario anonimo y toda la corrida se
        # desperdicia. Es preferible detenerse que postular en el vacio.
        raise RuntimeError(
            "No hay sesion de Magneto en el navegador. Inicia sesion en la ventana "
            "abierta por abrir_navegador_bot.ps1; el bot lo reintenta en el siguiente ciclo."
        )

    def _iniciar_sesion_automatica(self) -> bool:
        logging.info("Sin sesion de Magneto: iniciando sesion con codigo al correo...")
        login = LoginMagneto(
            self.pagina,
            self.settings.magneto_email,
            crear_fuente_de_codigos(self.settings.magneto_email, self.settings.correo_codigos_clave_app),
            self.settings.minutos_espera_login_manual,
        )
        resultado = login.iniciar()
        logging.info("Login de Magneto: %s", resultado.motivo)
        return resultado.exito

    def _hay_sesion(self) -> bool:
        for intento in range(self.INTENTOS_SESION):
            texto = self._texto_pagina()
            if len(texto) >= self.TEXTO_MINIMO_PAGINA:
                plano = lectura.normalizar(texto)
                if not any(marca in plano for marca in self.MARCAS_ANONIMO):
                    return True
                logging.debug("Encabezado aun anonimo (intento %s)", intento + 1)
            sleep(1)
        return False

    # ------------------------------------------------------------------ busqueda

    def search(self, keyword: str, conocidas: OfertasConocidas) -> list[JobOffer]:
        url = f"{self.BASE_URL}/co/trabajos/buscar/{lectura.slug(keyword)}"
        logging.info("Buscando en Magneto: %s", url)
        # Una busqueda que no carga no debe tumbar la corrida entera: se sigue
        # con la siguiente palabra clave.
        if not self.abrir(url):
            return []

        ofertas = self._leer_resultados(filtro=None)
        if ofertas:
            return self._sumar_paginas_siguientes(ofertas, conocidas)

        logging.info("Busqueda por URL sin resultados. Usando pagina de ciudad para: %s", keyword)
        ciudad = lectura.slug(self.settings.magneto_city)
        if not self.abrir(f"{self.BASE_URL}/co/trabajos/ofertas-empleo-en-{ciudad}/"):
            return []
        return self._leer_resultados(filtro=keyword)

    def _sumar_paginas_siguientes(self, ofertas: list[JobOffer], conocidas: OfertasConocidas) -> list[JobOffer]:
        """Magneto pagina en el navegador: la URL ?paginator[page]=2 cargada
        directamente devuelve la pagina 1, asi que hay que pulsar el enlace.
        Sigue mientras aparezca algo nuevo, hasta PAGINAS_MAXIMAS."""
        vistas = {str(o.url) for o in ofertas}
        nuevas, numero = ofertas, 1
        while self.seguir_paginando(numero, nuevas, conocidas):
            numero += 1
            enlace = self.pagina.locator(f'a[href*="paginator[page]={numero}"]')
            if not enlace.count():
                break
            try:
                enlace.first.click()
                self.pagina.wait_for_timeout(self.MS_ESPERA_PAGINA)
            except PlaywrightTimeout:
                break
            nuevas = [o for o in self._leer_resultados(filtro=None) if str(o.url) not in vistas]
            vistas.update(str(o.url) for o in nuevas)
            ofertas.extend(nuevas)
        logging.info("Magneto: %s ofertas en total para esta busqueda", len(ofertas))
        return ofertas

    def _leer_resultados(self, filtro: str | None) -> list[JobOffer]:
        try:
            self.pagina.wait_for_selector(self.SELECTOR_OFERTA, timeout=15000)
        except PlaywrightTimeout:
            logging.info("No se encontraron resultados visibles en la busqueda actual.")
            return []

        ofertas: list[JobOffer] = []
        vistas: set[str] = set()

        for enlace in self.pagina.query_selector_all(self.SELECTOR_OFERTA):
            url = canonicalize_url(urljoin(self.BASE_URL, enlace.get_attribute("href") or ""))
            if not url or url in vistas:
                continue

            texto = self._texto_tarjeta(enlace)
            if not lectura.es_ubicacion_valida(texto, self.settings.locations):
                continue
            if filtro and not lectura.coincide_con_busqueda(texto, filtro):
                continue

            ofertas.append(JobOffer(
                title=lectura.limpiar(enlace.inner_text()) or lectura.titulo(texto),
                company=lectura.empresa(texto),
                url=url,
                published_at=lectura.fecha(texto),
                city=lectura.ciudad(texto, self.settings.locations),
                salary=lectura.salario(texto),
                description=lectura.limpiar(texto),
            ))
            vistas.add(url)

        logging.info("Ofertas extraidas de Magneto: %s", len(ofertas))
        return ofertas

    @staticmethod
    def _texto_tarjeta(enlace) -> str:
        """El texto de la tarjeta completa, no solo el del enlace."""
        js = """
            enlace => {
                let caja = enlace.parentElement;
                for (let i = 0; i < 4 && caja; i += 1) {
                    if ((caja.innerText || '').length > 60) return caja.innerText;
                    caja = caja.parentElement;
                }
                return enlace.innerText || '';
            }
        """
        try:
            return (enlace.evaluate(js) or "").strip()
        except Exception:
            return (enlace.inner_text() or "").strip()

    # ---------------------------------------------------------------- postulacion

    def apply(self, offer: JobOffer) -> str:
        logging.info("Abriendo oferta: %s", offer.url)
        if not self.abrir(str(offer.url)):
            return "no disponible"
        self._cerrar_avisos()

        if self._ya_postulado():
            logging.info("La oferta ya figura como postulada.")
            return "aplicado"

        # La pagina no siempre dice lo que paso: cuando la oferta ya estaba
        # postulada, Magneto no muestra nada y solo su API lo reporta.
        with self._escuchar_api() as respuestas:
            pulsado = self._pulsar_aplicar(respuestas)
            estado = self._completar_postulacion() if pulsado else "no disponible"
            return self._veredicto_api(respuestas) or estado

    # La API que decide la postulacion, y lo que responde cuando ya existe.
    API_APLICAR = "jobs/v1/jobs/apply"
    MENSAJE_YA_APLICADA = "ya ha sido aplicada anteriormente"

    @contextmanager
    def _escuchar_api(self):
        """Recoge lo que responde la API de postulacion mientras dura el intento."""
        respuestas: list[tuple[int, str]] = []

        def anotar(respuesta) -> None:
            if self.API_APLICAR not in respuesta.url:
                return
            try:
                respuestas.append((respuesta.status, respuesta.text()[:300]))
            except Exception:
                respuestas.append((respuesta.status, ""))

        self.pagina.on("response", anotar)
        try:
            yield respuestas
        finally:
            try:
                self.pagina.remove_listener("response", anotar)
            except Exception:
                pass

    def _veredicto_api(self, respuestas: list[tuple[int, str]]) -> str | None:
        """Traduce la respuesta del servidor, que manda sobre lo que se ve."""
        for estado, cuerpo in respuestas:
            if estado < 300:
                logging.info("La API acepto la postulacion (HTTP %s).", estado)
                return "aplicado"
            if self.MENSAJE_YA_APLICADA in lectura.normalizar(cuerpo):
                logging.info("La API informa que esta oferta ya estaba postulada.")
                return "aplicado"
            if estado >= 400:
                logging.warning("La API rechazo la postulacion (HTTP %s): %s",
                                estado, cuerpo[:150])
        return None

    def _pulsar_aplicar(self, respuestas: list | None = None) -> bool:
        """Pulsa Aplicar y comprueba que la pagina reacciono.

        La pagina pinta el boton antes de que React le ponga el manejador: al
        pulsarlo de inmediato el clic se perdia y la oferta quedaba sin abrir el
        cuestionario. Se espera a que la carga acabe y, si el primer boton no
        produce nada, se prueba el siguiente.
        """
        try:
            self.pagina.wait_for_load_state("networkidle", timeout=10000)
        except PlaywrightTimeout:
            pass

        botones = self.pagina.get_by_role("button", name=self.PATRON_APLICAR)
        try:
            cuantos = botones.count()
        except Exception:
            cuantos = 0

        if not cuantos:
            logging.info("No hay boton de aplicar visible en la oferta.")
            return False

        for indice in range(cuantos):
            try:
                botones.nth(indice).click(timeout=10000)
            except Exception as error:
                logging.debug("boton %s no se pudo pulsar: %s", indice, str(error)[:60])
                continue

            if self._hubo_reaccion(respuestas):
                logging.info("Aplicar pulsado (boton %s de %s).", indice + 1, cuantos)
                return True
            logging.info("El boton %s no abrio nada; se prueba el siguiente.", indice + 1)

        logging.info("Ningun boton de aplicar produjo respuesta.")
        return False

    def _hubo_reaccion(self, respuestas: list | None = None) -> bool:
        """El clic sirvio si aparece el cuestionario, un formulario o la confirmacion.

        Si la API ya respondio, el clic llego a su destino y esperar mas es
        tiempo perdido: el veredicto lo da el servidor, no la pantalla.
        """
        if respuestas:
            return True
        try:
            self.pagina.wait_for_selector(
                f'{CuestionarioMagneto.SELECTOR_PREGUNTA_CLASE}, textarea, input#email',
                timeout=8000)
            return True
        except PlaywrightTimeout:
            return self._postulacion_confirmada()

    def _completar_postulacion(self) -> str:
        # Hay ofertas sin cuestionario: el clic en Aplicar ya envia la postulacion.
        if self._esperar_confirmacion(segundos=4):
            logging.info("POSTULACION CONFIRMADA sin cuestionario")
            self._cerrar_confirmacion()
            return "aplicado"

        cuestionario = CuestionarioMagneto(self.pagina)
        self._esperar_panel()

        respondidas = 0
        estancado = 0
        ya_contestadas: set[str] = set()

        for vuelta in range(1, self.VUELTAS_MAXIMAS + 1):
            logging.info("Vuelta %s/%s del formulario", vuelta, self.VUELTAS_MAXIMAS)
            self._adjuntar_cv()
            self._rellenar_datos_personales()

            avanzo = self._responder_pendientes(cuestionario, ya_contestadas)
            respondidas += avanzo

            if cuestionario.enviar():
                if self._esperar_confirmacion():
                    logging.info("POSTULACION CONFIRMADA | preguntas respondidas: %s", respondidas)
                    self._cerrar_confirmacion()
                    return "aplicado"
                self._registrar_estado_tras_enviar()
                logging.info("Enviado sin confirmacion visible todavia; se revisa otra vuelta.")

            if not avanzo:
                estancado += 1
                if estancado >= 2:
                    estado = cuestionario.estado_envio()
                    logging.warning(
                        "Formulario detenido | boton existe=%s habilitado=%s | campos vacios=%s de %s",
                        estado.existe, estado.habilitado, estado.campos_vacios, estado.campos_totales)
                    break
            else:
                estancado = 0
            sleep(1)

        return "aplicado" if self._postulacion_confirmada() else "formulario incompleto"

    def _esperar_panel(self) -> None:
        try:
            self.pagina.wait_for_selector(
                'textarea, [class*="jobOfferQuestionnaire_question-title"], input#email',
                timeout=15000)
        except PlaywrightTimeout:
            logging.info("No aparecio panel de preguntas; se intenta el flujo normal.")

    def _responder_pendientes(self, cuestionario: CuestionarioMagneto,
                              ya_contestadas: set[str]) -> int:
        """Contesta las preguntas sin responder. Devuelve cuantas quedaron puestas.

        No se repite una pregunta ya contestada en esta postulacion: volver a
        pulsar una opcion la desmarca, y el formulario no se completa nunca.
        """
        puestas = 0
        for indice, pregunta in enumerate(cuestionario.pendientes(), 1):
            if pregunta.texto in ya_contestadas:
                continue
            decision = self._decidir(pregunta)
            if not decision.should_answer or decision.value is None:
                logging.info("  %s. omitida | %s | %s", indice, decision.reason, pregunta.texto[:90])
                self.registrar_pregunta(pregunta.texto, f"[OMITIDA] {decision.reason}", decision.confidence)
                continue

            valor = str(decision.value)
            puesta = (cuestionario.escribir(pregunta, valor) if pregunta.es_texto_libre
                      else cuestionario.elegir(pregunta, valor))
            if puesta:
                puestas += 1
                ya_contestadas.add(pregunta.texto)
                logging.info("  %s. respondida | %s -> %s", indice, pregunta.texto[:60], valor[:60])
                self.registrar_pregunta(pregunta.texto, valor, decision.confidence)
                self._pausa_de_revision()
            else:
                logging.warning("  %s. sin poder responder | %s", indice, pregunta.texto[:90])
        return puestas

    def _pausa_de_revision(self) -> None:
        """Deja la respuesta en pantalla unos segundos para auditarla en vivo."""
        segundos = self.settings.question_review_seconds
        if segundos:
            logging.info("  pausa de revision: %ss", segundos)
            sleep(segundos)

    def _decidir(self, pregunta: Pregunta):
        """Elige la respuesta, prefiriendo la redactada del perfil en texto libre."""
        decision = self.question_answerer.answer(pregunta.texto, pregunta.opciones)
        if pregunta.tipo != "textarea":
            return decision

        redactada = self.question_answerer.locales.responder(pregunta.texto)
        if redactada and len(str(decision.value or "")) < 40:
            logging.info("  campo de texto libre: se usa respuesta redactada del perfil")
            return type(decision)(redactada, 0.85, "Redactada desde el perfil", True)
        return decision

    # --------------------------------------------------------- datos personales

    def _valor_para_campo(self, campo: str) -> str:
        perfil = self.question_answerer.profile
        nombre = str(perfil.get("name", "")).split()
        mitad = (len(nombre) + 1) // 2
        telefono = "".join(c for c in str(perfil.get("phone", "")) if c.isdigit())

        valores = {
            "email": perfil.get("email", ""),
            "emailConfirmation": perfil.get("email", ""),
            "identificationNumber": str(perfil.get("document_number", "")),
            "firstName": " ".join(nombre[:mitad]),
            "lastName": " ".join(nombre[mitad:]),
            # El formulario pide el numero sin indicativo de pais.
            "phone": telefono[-10:] if len(telefono) > 10 else telefono,
        }
        return str(valores.get(campo, ""))

    def _rellenar_datos_personales(self) -> int:
        llenados = 0
        for campo in self.CAMPOS_CONOCIDOS:
            elemento = self.pagina.query_selector(f"#{campo}")
            if elemento is None or not elemento.is_visible() or not elemento.is_enabled():
                continue

            valor = self._valor_para_campo(campo)
            if not valor:
                continue
            if (elemento.input_value() or "").strip() == valor:
                llenados += 1
                continue

            try:
                elemento.fill(valor)
                elemento.evaluate("c => c.dispatchEvent(new Event('blur', {bubbles: true}))")
                llenados += 1
                logging.info("  campo %s -> %s", campo,
                             valor if campo != "identificationNumber" else "***")
            except Exception as error:
                logging.warning("  no se pudo llenar %s: %s", campo, str(error)[:70])

        if llenados:
            self._marcar_casillas_obligatorias()
        return llenados

    def _marcar_casillas_obligatorias(self) -> None:
        """Acepta terminos y tratamiento de datos, que bloquean el avance."""
        for casilla in self.pagina.query_selector_all("input[type=checkbox]"):
            try:
                if casilla.is_visible() and casilla.is_enabled() and not casilla.is_checked():
                    casilla.check()
            except Exception:
                continue

    def _adjuntar_cv(self) -> None:
        if not self.settings.cv_path.exists():
            return
        for entrada in self.pagina.query_selector_all("input[type=file]"):
            try:
                entrada.set_input_files(str(self.settings.cv_path))
            except Exception:
                logging.debug("No fue posible adjuntar el CV en este paso.")

    # ------------------------------------------------------------------ evidencia

    def _postulacion_confirmada(self) -> bool:
        """Verifica en la pagina que la postulacion realmente salio.

        Un clic en un boton que dice Aplicar no prueba nada: el boton puede estar
        deshabilitado o el formulario incompleto. Esto evita marcar como enviadas
        postulaciones que nunca ocurrieron.
        """
        plano = lectura.normalizar(self._texto_pagina())
        return any(marca in plano for marca in self.CONFIRMACIONES)

    def _esperar_confirmacion(self, segundos: int | None = None) -> bool:
        """Espera el modal de confirmacion en vez de mirar la pagina una sola vez.

        El modal tarda un momento en aparecer: comprobarlo de inmediato daba por
        fallida una postulacion que si habia salido.
        """
        for _ in range(segundos or self.SEGUNDOS_ESPERANDO_CONFIRMACION):
            if self._postulacion_confirmada():
                return True
            sleep(1)
        return False

    def _cerrar_confirmacion(self) -> None:
        """Cierra el modal de exito para dejar la pestana lista para la siguiente."""
        try:
            boton = self.pagina.get_by_role("button", name="Cerrar")
            if boton.count():
                boton.first.click(timeout=3000)
        except Exception:
            pass

    def _ya_postulado(self) -> bool:
        plano = lectura.normalizar(self._texto_pagina())
        return "ya te postulaste" in plano or "ya aplicaste" in plano

    def _registrar_estado_tras_enviar(self) -> None:
        """Deja evidencia de lo que ocurre justo despues de pulsar enviar."""
        for espera in (1, 3):
            sleep(espera)
            lineas = [l.strip() for l in self._texto_pagina().splitlines() if l.strip()]
            logging.info("  [tras enviar +%ss] url=%s", espera, self.pagina.url[:70])
            logging.info("  [tras enviar +%ss] pantalla: %s", espera, " | ".join(lineas[:8])[:220])

            errores = [e.inner_text().strip()[:70]
                       for e in self.pagina.query_selector_all(
                           '[class*="error"], [class*="invalid"], [role="alert"]')
                       if e.is_visible() and (e.inner_text() or "").strip()]
            if errores:
                logging.warning("  [tras enviar] MENSAJES DE ERROR: %s", errores[:4])

        try:
            self.pagina.screenshot(path="tras_enviar.png")
            logging.info("  [tras enviar] captura guardada en tras_enviar.png")
        except Exception:
            pass

    # --------------------------------------------------------------------- apoyo

    def _texto_pagina(self) -> str:
        try:
            return self.pagina.inner_text("body")
        except Exception:
            return ""

    def _cerrar_avisos(self) -> None:
        for etiqueta in self.CIERRES:
            boton = self.pagina.get_by_role("button", name=etiqueta)
            try:
                if boton.count() and boton.first.is_visible():
                    boton.first.click(timeout=2000)
            except Exception:
                continue
