"""El cuestionario de Computrabajo marca radios aunque esten fuera de la vista.

Pagina local con la misma estructura de KillerQuestions. El radio queda lejos
del area visible, como en las dos ofertas que el 3 de octubre no se enviaron
por "Element is outside of the viewport". No toca la red ni la cuenta.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

from platforms.cuestionario_computrabajo import CuestionarioComputrabajo

HTML = """
<form style="height: 6000px">
  <input type="hidden" name="KillerQuestions[0].Title"
         value="¿Cuenta con experiencia mínima de 2 años en control de gestión?">
  <input type="hidden" name="KillerQuestions[0].DataOptions[1].Answer"
         value="Sí, más de 3 años de experiencia">
  <input type="hidden" name="KillerQuestions[0].DataOptions[2].Answer"
         value="No cuento con experiencia en estas áreas">
  <div style="position: absolute; top: 5000px; left: -4000px">
    <input type="radio" name="KillerQuestions[0].ClosedQuestion" value="1">
    <input type="radio" name="KillerQuestions[0].ClosedQuestion" value="2">
  </div>
</form>
"""


def main() -> int:
    fallos = 0
    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page()
        pagina.set_content(HTML)
        cuestionario = CuestionarioComputrabajo(pagina)

        preguntas = cuestionario.leer()
        ok = len(preguntas) == 1 and len(preguntas[0].opciones) == 2
        fallos += not ok
        print(f"  [{'ok ' if ok else 'FALLA'}] lee la pregunta cerrada y sus 2 opciones")

        ok = cuestionario.elegir(preguntas[0], "No cuento con experiencia en estas áreas")
        fallos += not ok
        print(f"  [{'ok ' if ok else 'FALLA'}] marca un radio fuera de la vista")

        ok = not cuestionario.sin_responder()
        fallos += not ok
        print(f"  [{'ok ' if ok else 'FALLA'}] la pregunta queda respondida")
        navegador.close()

    print(f"\n  {3 - fallos} de 3 correctos")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
