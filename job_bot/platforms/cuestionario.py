"""El cuestionario de Magneto como objeto propio.

Estaba disuelto en la clase de la plataforma junto con la busqueda y el login,
y con cinco extractores de preguntas encadenados que se tapaban los errores
entre si. Aqui vive solo lo que la pagina real usa: leer las preguntas, llenar
los campos respetando su limite, elegir opciones y pulsar enviar.
"""
from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass, field

from playwright.sync_api import ElementHandle, Page

# Magneto marca cada pregunta con esta clase.
SELECTOR_PREGUNTA = '[class*="jobOfferQuestionnaire_question-title"]'
SELECTOR_OPCION = '[class*="question-possible-answer-button"]'
SELECTOR_DESPLEGABLE = "select"
SELECTOR_CAMPO = "textarea, input:not([type=hidden]):not([type=checkbox]):not([type=radio])"

# El boton de envio aparece con dos nombres de clase segun el estado del modal:
# buscar solo uno de ellos dejaba el formulario lleno y sin enviar.
SELECTOR_ENVIAR = '[class*="send-answer-btn"], [class*="send-btn"]'

# El limite de caracteres no esta en maxlength: lo muestra un contador
# de React con la forma "609 de 140".
SELECTOR_CONTADOR = '[class*="limitInputText_input-limit__limit-text"]'
PATRON_LIMITE = re.compile(r"de\s*([0-9]+)\s*$")

# Sube desde un elemento hasta el ancestro que contiene el campo de respuesta.
JS_CONTENEDOR = r"""
    (elemento, selectores) => {
        let caja = elemento.parentElement;
        for (let i = 0; i < 4 && caja; i += 1) {
            if (caja.querySelector(selectores)) return caja;
            caja = caja.parentElement;
        }
        return caja;
    }
"""

JS_CONTADOR = r"""
    (campo, selector) => {
        let caja = campo.parentElement;
        for (let i = 0; i < 5 && caja; i += 1) {
            const contador = caja.querySelector(selector);
            if (contador) return (contador.innerText || '').trim();
            caja = caja.parentElement;
        }
        return null;
    }
"""


def sin_tildes(valor: str) -> str:
    plano = unicodedata.normalize("NFKD", valor or "")
    return " ".join(plano.encode("ascii", "ignore").decode("ascii").lower().split())


@dataclass
class Pregunta:
    """Una pregunta del cuestionario con lo necesario para contestarla."""

    texto: str
    contenedor: ElementHandle
    tipo: str = "desconocido"
    opciones: list[str] = field(default_factory=list)
    respondida: bool = False
    # Identificador de la pregunta dentro de su formulario, cuando la
    # plataforma lo necesita para marcar la respuesta (p. ej. el indice n
    # de KillerQuestions[n] en Computrabajo).
    clave: str = ""

    @property
    def es_texto_libre(self) -> bool:
        return self.tipo in ("textarea", "input")


@dataclass(frozen=True)
class EstadoEnvio:
    """Por que se puede o no pulsar enviar, en terminos de la pagina."""

    existe: bool
    habilitado: bool = False
    texto: str = ""
    campos_vacios: int = 0
    campos_totales: int = 0

    @property
    def listo(self) -> bool:
        return self.existe and self.habilitado


class CuestionarioMagneto:
    """Lee y contesta el cuestionario que Magneto muestra al postularse."""

    # Expuesto para que la plataforma sepa reconocer el cuestionario sin
    # repetir el selector: un solo sitio donde cambiarlo si Magneto lo cambia.
    SELECTOR_PREGUNTA_CLASE = SELECTOR_PREGUNTA

    def __init__(self, pagina: Page) -> None:
        self.pagina = pagina

    # -------------------------------------------------------------------- estado

    def abierto(self) -> bool:
        return bool(self.pagina.query_selector(SELECTOR_PREGUNTA)) or bool(
            self.pagina.query_selector(SELECTOR_ENVIAR)
        )

    def leer(self) -> list[Pregunta]:
        """Devuelve las preguntas del cuestionario en el orden de la pagina."""
        preguntas: list[Pregunta] = []
        selectores = SELECTOR_CAMPO + ", " + SELECTOR_OPCION + ", " + SELECTOR_DESPLEGABLE

        for titulo in self.pagina.query_selector_all(SELECTOR_PREGUNTA):
            texto = (titulo.inner_text() or "").strip()
            if not texto:
                continue

            caja = titulo.evaluate_handle(JS_CONTENEDOR, selectores).as_element()
            if caja is None:
                continue

            campo = caja.query_selector(SELECTOR_CAMPO)
            desplegable = caja.query_selector(SELECTOR_DESPLEGABLE)
            if desplegable is not None:
                # Un <select>: las opciones son sus <option>, sin el marcador vacio.
                opciones = [t.strip() for t in desplegable.evaluate(
                    "s => Array.from(s.options).filter(o => o.value).map(o => o.text)")]
                preguntas.append(Pregunta(
                    texto=texto, contenedor=caja, tipo="desplegable",
                    opciones=[o for o in opciones if o][:15],
                    respondida=bool(desplegable.evaluate("s => Boolean(s.value)")),
                ))
                continue
            opciones = [
                (o.inner_text() or "").strip()
                for o in caja.query_selector_all(SELECTOR_OPCION)
            ]
            preguntas.append(Pregunta(
                texto=texto,
                contenedor=caja,
                tipo=self._tipo(campo, opciones),
                opciones=[o for o in opciones if o][:8],
                respondida=self._respondida(caja, campo),
            ))
        return preguntas

    # Como marca Magneto la opcion elegida, segun el tipo de control.
    JS_OPCION_ELEGIDA = r"""
        (caja, selector) => {
            const botones = Array.from(caja.querySelectorAll(selector));
            return botones.some((b) => {
                // Solo senales explicitas. Una clase con "active" suele ser el
                // estilo por defecto del boton, y darla por seleccionada hacia
                // saltar preguntas que seguian sin contestar.
                if (b.getAttribute('aria-pressed') === 'true') return true;
                if (b.getAttribute('aria-checked') === 'true') return true;
                if (/__selected|--selected|is-selected/i.test((b.className || '').toString())) return true;
                const marca = b.querySelector('input[type=checkbox], input[type=radio]');
                return Boolean(marca && marca.checked);
            });
        }
    """

    def _respondida(self, caja: ElementHandle, campo: ElementHandle | None) -> bool:
        """Una pregunta de opciones tambien esta respondida, aunque no tenga campo.

        Mirando solo el valor del campo, las preguntas de opcion parecian siempre
        pendientes: el bot las volvia a pulsar en cada vuelta y el segundo clic
        desmarcaba la respuesta, dejando el envio deshabilitado para siempre.
        """
        if campo is not None:
            return bool((campo.input_value() or "").strip())
        try:
            return bool(caja.evaluate(self.JS_OPCION_ELEGIDA, SELECTOR_OPCION))
        except Exception:
            return False

    @staticmethod
    def _tipo(campo: ElementHandle | None, opciones: list[str]) -> str:
        if campo is not None:
            return str(campo.evaluate("c => c.tagName.toLowerCase()"))
        return "opciones" if opciones else "desconocido"

    def pendientes(self) -> list[Pregunta]:
        preguntas = self.leer()
        sin_responder = [p for p in preguntas if not p.respondida]
        if preguntas:
            logging.info("Cuestionario: %s preguntas (%s sin responder)",
                         len(preguntas), len(sin_responder))
        return sin_responder

    # ------------------------------------------------------------------ respuesta

    def escribir(self, pregunta: Pregunta, texto: str) -> bool:
        """Escribe en el campo de la pregunta respetando su limite real."""
        campo = pregunta.contenedor.query_selector(SELECTOR_CAMPO)
        if campo is None:
            return False

        recortado = self._ajustar_al_limite(campo, texto)
        try:
            campo.scroll_into_view_if_needed()
            campo.fill(recortado)
        except Exception as error:
            logging.warning("  no se pudo escribir: %s", str(error)[:70])
            return False

        # React puede ignorar un valor que no vino acompanado de blur.
        campo.evaluate("c => c.dispatchEvent(new Event('blur', {bubbles: true}))")
        return bool((campo.input_value() or "").strip())

    def elegir(self, pregunta: Pregunta, valor: str) -> bool:
        """Pulsa la opcion cuyo texto corresponde al valor decidido."""
        buscado = sin_tildes(valor)
        if not buscado:
            return False

        desplegable = pregunta.contenedor.query_selector(SELECTOR_DESPLEGABLE)
        if desplegable is not None:
            return self._elegir_en_desplegable(desplegable, pregunta.opciones, buscado)

        candidatos = list(pregunta.contenedor.query_selector_all(SELECTOR_OPCION))
        # Algunos cuestionarios usan etiquetas o botones sueltos en vez de los propios.
        candidatos += list(pregunta.contenedor.query_selector_all("label, button"))

        for elemento in candidatos:
            if not self._coincide(sin_tildes(elemento.inner_text() or ""), buscado):
                continue
            try:
                elemento.scroll_into_view_if_needed()
                elemento.click()
                return True
            except Exception as error:
                logging.debug("no se pudo pulsar la opcion: %s", str(error)[:60])
        return False

    def _elegir_en_desplegable(self, desplegable: ElementHandle, opciones: list[str],
                               buscado: str) -> bool:
        elegida = next((o for o in opciones if sin_tildes(o) == buscado), None) or next(
            (o for o in opciones if self._coincide(sin_tildes(o), buscado)), None)
        if elegida is None:
            logging.warning("  ninguna opcion del desplegable corresponde a %r: %s", buscado, opciones)
            return False
        try:
            desplegable.select_option(label=elegida)
            desplegable.dispatch_event("change")
            return True
        except Exception as error:
            logging.warning("  no se pudo elegir en el desplegable: %s", str(error)[:70])
            return False

    @staticmethod
    def _coincide(texto: str, buscado: str) -> bool:
        if not texto:
            return False
        return texto == buscado or (len(buscado) > 2 and buscado in texto) or (
            len(texto) > 2 and texto in buscado
        )

    # --------------------------------------------------------------------- envio

    def estado_envio(self) -> EstadoEnvio:
        boton = self._boton_enviar()
        if boton is None:
            return EstadoEnvio(existe=False)

        campos = [c for c in self.pagina.query_selector_all(SELECTOR_CAMPO) if c.is_visible()]
        vacios = [c for c in campos if not (c.input_value() or "").strip()]
        clases = boton.get_attribute("class") or ""
        return EstadoEnvio(
            existe=True,
            habilitado=boton.is_enabled() and "disabled-btn" not in clases,
            texto=(boton.inner_text() or "").strip(),
            campos_vacios=len(vacios),
            campos_totales=len(campos),
        )

    def enviar(self) -> bool:
        """Pulsa Enviar respuestas solo si el formulario lo habilito."""
        estado = self.estado_envio()
        if not estado.existe:
            return False
        if not estado.habilitado:
            logging.warning("Boton '%s' deshabilitado | campos sin llenar: %s de %s",
                            estado.texto or "Enviar respuestas",
                            estado.campos_vacios, estado.campos_totales)
            return False

        boton = self._boton_enviar()
        if boton is None:
            return False
        try:
            boton.scroll_into_view_if_needed()
            boton.click()
            logging.info("Enviar respuestas pulsado | texto='%s'", estado.texto[:30])
            return True
        except Exception as error:
            logging.warning("No se pudo pulsar enviar: %s", str(error)[:70])
            return False

    def _boton_enviar(self) -> ElementHandle | None:
        """El boton visible cuyo texto habla de enviar, no cualquiera del DOM."""
        for boton in self.pagina.query_selector_all(SELECTOR_ENVIAR):
            if boton.is_visible() and "enviar" in sin_tildes(boton.inner_text() or ""):
                return boton
        return None

    # --------------------------------------------------------------------- apoyo

    def _ajustar_al_limite(self, campo: ElementHandle, texto: str) -> str:
        """Recorta la respuesta al limite de ESE campo, sin cortar palabras."""
        limite = self._limite(campo)
        if limite is None or len(texto) <= limite:
            return texto

        recorte = texto[:limite]
        corte = recorte.rfind(" ")
        if corte > limite * 0.5:
            recorte = recorte[:corte]
        recorte = recorte.rstrip(" ,;.")
        logging.info("  respuesta recortada de %s a %s caracteres (limite %s)",
                     len(texto), len(recorte), limite)
        return recorte

    def _limite(self, campo: ElementHandle) -> int | None:
        """Lee el maximo de caracteres del contador que acompana al campo.

        Buscarlo en toda la pagina tomaba el de otra pregunta: un campo de 140
        recibia el limite de uno de 2500 y la respuesta se pasaba igual.
        """
        crudo = campo.get_attribute("maxlength")
        try:
            limite = int(crudo)
            if limite > 0:
                return limite
        except (TypeError, ValueError):
            pass

        try:
            texto = campo.evaluate(JS_CONTADOR, SELECTOR_CONTADOR)
        except Exception:
            return None

        encontrado = PATRON_LIMITE.search((texto or "").strip())
        return int(encontrado.group(1)) if encontrado else None
