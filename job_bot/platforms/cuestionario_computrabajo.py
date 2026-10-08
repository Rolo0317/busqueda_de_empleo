"""Las "preguntas de seleccion" que Computrabajo pide antes de enviar la HdV.

Tienen su propio DOM, distinto del de Magneto, pero la decision de que
responder es la misma: por eso este modulo solo lee y escribe, y quien decide
sigue siendo CandidateQuestionAnswerer.

Sin esto, la postulacion se quedaba a un paso del final y el bot la reportaba
como "requiere pasos adicionales".
"""
from __future__ import annotations

import logging
import unicodedata

from playwright.sync_api import Page

from platforms.cuestionario import Pregunta

SELECTOR_CAMPO = 'textarea[id^="KillerQuestions_"]'
SELECTOR_ENVIAR = "#btnKiller"
RUTA = "/candidate/kq"

# El enunciado esta en un ancestro del campo, junto al aviso del limite.
JS_ENUNCIADO = r"""
    campo => {
        let caja = campo.parentElement;
        for (let i = 0; i < 4 && caja; i += 1) {
            const texto = (caja.innerText || '').trim();
            if (texto.length > 15) return texto;
            caja = caja.parentElement;
        }
        return '';
    }
"""

RUIDO = "(máximo"

# Preguntas cerradas: un grupo de radios KillerQuestions[n].ClosedQuestion. El
# enunciado va en un campo oculto (.Title) y el texto de cada opcion en
# DataOptions[m].Answer, con m igual al value del radio. Solo se leen enunciado
# y textos: el puntaje oculto de cada opcion no se usa para elegir.
JS_CERRADAS = r"""
() => {
  const grupos = {};
  document.querySelectorAll('input[type=radio][name$=".ClosedQuestion"]').forEach(r => {
    const m = r.name.match(/KillerQuestions\[(\d+)\]/);
    if (!m) return;
    const n = m[1];
    const valor = sel => (document.querySelector('input[name="' + sel + '"]') || {}).value || '';
    if (!grupos[n]) {
      grupos[n] = {indice: n, titulo: valor('KillerQuestions[' + n + '].Title'), opciones: [], marcada: false};
    }
    grupos[n].opciones.push({valor: r.value, texto: valor('KillerQuestions[' + n + '].DataOptions[' + r.value + '].Answer')});
    if (r.checked) grupos[n].marcada = true;
  });
  return Object.values(grupos);
}
"""


JS_MARCAR = r"""
r => {
  r.checked = true;
  for (const tipo of ['click', 'input', 'change']) {
    r.dispatchEvent(new Event(tipo, {bubbles: true}));
  }
}
"""


def _plano(texto: str) -> str:
    base = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode("ascii")
    return " ".join(base.lower().split())


class CuestionarioComputrabajo:
    """Lee y contesta las preguntas de seleccion de una oferta.

    Hay dos clases de pregunta: abiertas (textarea) y cerradas (radios). Antes
    solo se contestaban las abiertas; con una cerrada sin marcar el formulario
    no se enviaba, y 72 postulaciones quedaron sin confirmar por eso.
    """

    def __init__(self, pagina: Page) -> None:
        self.pagina = pagina
        # indice de la pregunta cerrada -> {texto de la opcion: value del radio}
        self._valores: dict[str, dict[str, str]] = {}

    def abierto(self) -> bool:
        return RUTA in self.pagina.url or bool(self.pagina.query_selector(SELECTOR_CAMPO))

    def leer(self) -> list[Pregunta]:
        preguntas = self._leer_abiertas() + self._leer_cerradas()
        if preguntas:
            logging.info("Preguntas de seleccion: %s (%s cerradas)", len(preguntas),
                         sum(p.tipo == "opciones" for p in preguntas))
        return preguntas

    def _leer_cerradas(self) -> list[Pregunta]:
        preguntas: list[Pregunta] = []
        for grupo in self.pagina.evaluate(JS_CERRADAS):
            indice = str(grupo["indice"])
            radio = self.pagina.query_selector(
                f'input[type=radio][name="KillerQuestions[{indice}].ClosedQuestion"]')
            if radio is None or not grupo["titulo"]:
                continue
            opciones = [o["texto"] for o in grupo["opciones"] if o["texto"]]
            self._valores[indice] = {o["texto"]: o["valor"] for o in grupo["opciones"]}
            preguntas.append(Pregunta(
                texto=grupo["titulo"].strip(),
                contenedor=radio,
                tipo="opciones",
                opciones=opciones,
                respondida=bool(grupo["marcada"]),
                clave=indice,
            ))
        return preguntas

    def elegir(self, pregunta: Pregunta, valor: str) -> bool:
        """Marca la opcion cuyo texto corresponde al valor decidido."""
        opciones = self._valores.get(pregunta.clave, {})
        buscado = _plano(valor)
        elegida = next((t for t in opciones if _plano(t) == buscado), None)
        if elegida is None:
            elegida = next((t for t in opciones
                            if buscado and (buscado in _plano(t) or _plano(t) in buscado)), None)
        if elegida is None:
            logging.warning("  ninguna opcion corresponde a %r entre %s", valor, list(opciones))
            return False

        radio = self.pagina.locator(
            f'input[type=radio][name="KillerQuestions[{pregunta.clave}].ClosedQuestion"]'
            f'[value="{opciones[elegida]}"]')
        try:
            # El radio real suele estar oculto bajo un estilo propio.
            radio.check(force=True)
            radio.dispatch_event("change")
        except Exception as error:
            # "Element is outside of the viewport": el radio oculto no siempre se
            # deja pulsar. Se marca en la pagina con los eventos que el
            # formulario escucha. Dos postulaciones quedaron sin enviar por esto.
            logging.info("  marcando %r desde la pagina (%s)", elegida, str(error)[:50])
            try:
                radio.evaluate(JS_MARCAR)
            except Exception as error_js:
                logging.warning("  no se pudo marcar %r: %s", elegida, str(error_js)[:70])
                return False
        return radio.is_checked()

    def sin_responder(self) -> list[Pregunta]:
        """Las preguntas que siguen vacias: si hay alguna, el envio fallara."""
        return [p for p in self.leer() if not p.respondida]

    def _leer_abiertas(self) -> list[Pregunta]:
        preguntas: list[Pregunta] = []
        for campo in self.pagina.query_selector_all(SELECTOR_CAMPO):
            try:
                enunciado = self._enunciado(campo)
            except Exception:
                continue
            if not enunciado:
                continue
            preguntas.append(Pregunta(
                texto=enunciado,
                contenedor=campo,
                tipo="textarea",
                respondida=bool((campo.input_value() or "").strip()),
            ))
        return preguntas

    @staticmethod
    def _enunciado(campo) -> str:
        """El enunciado sin el aviso del limite, que no es parte de la pregunta."""
        crudo = str(campo.evaluate(JS_ENUNCIADO) or "")
        lineas = [l.strip() for l in crudo.splitlines() if l.strip() and RUIDO not in l]
        return " ".join(lineas).strip()

    def escribir(self, pregunta: Pregunta, texto: str) -> bool:
        """Escribe la respuesta respetando el maximo que declara el campo."""
        campo = pregunta.contenedor
        try:
            limite = int(campo.get_attribute("maxlength") or 0)
        except (TypeError, ValueError):
            limite = 0

        recortado = self._recortar(texto, limite) if limite > 0 else texto
        try:
            campo.scroll_into_view_if_needed()
            campo.fill(recortado)
            # Su validacion escucha el teclado: con solo asignar el valor, el
            # formulario se daba por vacio y el envio se perdia sin decir nada.
            campo.dispatch_event("input")
            campo.dispatch_event("keyup")
            campo.dispatch_event("change")
            campo.dispatch_event("blur")
        except Exception as error:
            logging.warning("  no se pudo escribir: %s", str(error)[:70])
            return False
        return bool((campo.input_value() or "").strip())

    @staticmethod
    def _recortar(texto: str, limite: int) -> str:
        if len(texto) <= limite:
            return texto
        recorte = texto[:limite]
        corte = recorte.rfind(" ")
        if corte > limite * 0.5:
            recorte = recorte[:corte]
        recorte = recorte.rstrip(" ,;.")
        logging.info("  respuesta recortada de %s a %s caracteres (limite %s)",
                     len(texto), len(recorte), limite)
        return recorte

    def enviar(self) -> bool:
        """Pulsa 'Enviar mi HdV', que es lo que cierra la postulacion."""
        boton = self.pagina.query_selector(SELECTOR_ENVIAR)
        if boton is None or not boton.is_visible():
            logging.warning("No aparece el boton de enviar la hoja de vida.")
            return False
        try:
            boton.scroll_into_view_if_needed()
            boton.click()
            logging.info("Enviar mi HdV pulsado.")
            return True
        except Exception as error:
            logging.warning("No se pudo enviar la hoja de vida: %s", str(error)[:70])
            return False
