"""El cuestionario de Magneto lee y contesta todos sus tipos de campo.

Usa una pagina local con la misma estructura de clases que Magneto: texto
libre, botones de opcion y desplegable. No toca la red ni la cuenta.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

from platforms.cuestionario import CuestionarioMagneto

HTML = """
<div class="q"><div class="jobOfferQuestionnaire_question-title__x">¿Cuál es tu nivel de inglés?</div>
  <select><option value="">Selecciona</option><option value="1">A1</option>
  <option value="2">A2</option><option value="3">B1</option></select></div>
<div class="q"><div class="jobOfferQuestionnaire_question-title__x">¿Vives en Bogotá?</div>
  <button class="jobOfferQuestionnaire_question-possible-answer-button__y"
          onclick="this.setAttribute('aria-pressed','true')">Si</button>
  <button class="jobOfferQuestionnaire_question-possible-answer-button__y"
          onclick="this.setAttribute('aria-pressed','true')">No</button></div>
<div class="q"><div class="jobOfferQuestionnaire_question-title__x">Cuéntanos tu experiencia</div>
  <textarea></textarea></div>
"""


def main() -> int:
    fallos = 0
    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page()
        pagina.set_content(HTML)
        cuestionario = CuestionarioMagneto(pagina)
        preguntas = {q.texto: q for q in cuestionario.leer()}

        tipos = {texto[:20]: q.tipo for texto, q in preguntas.items()}
        esperados = {"¿Cuál es tu nivel de": "desplegable", "¿Vives en Bogotá?": "opciones",
                     "Cuéntanos tu experie": "textarea"}
        ok = tipos == esperados
        fallos += not ok
        print(f"  [{'ok ' if ok else 'FALLA'}] tipos leidos: {tipos}")

        ingles = preguntas["¿Cuál es tu nivel de inglés?"]
        ok = cuestionario.elegir(ingles, "A2") and pagina.eval_on_selector(
            "select", "s => s.options[s.selectedIndex].text") == "A2"
        fallos += not ok
        print(f"  [{'ok ' if ok else 'FALLA'}] desplegable: elige A2")

        ok = cuestionario.leer()[0].respondida
        fallos += not ok
        print(f"  [{'ok ' if ok else 'FALLA'}] desplegable queda marcado como respondido")

        ok = cuestionario.escribir(preguntas["Cuéntanos tu experiencia"], "Seis años con Python.")
        fallos += not ok
        print(f"  [{'ok ' if ok else 'FALLA'}] texto libre: escribe la respuesta")
        navegador.close()

    print(f"\n  {4 - fallos} de 4 correctos")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
