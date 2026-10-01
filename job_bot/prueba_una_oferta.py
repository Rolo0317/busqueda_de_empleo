"""Postula a UNA sola oferta, con traza detallada.

Sirve para comprobar de verdad si la postulacion queda registrada, sin gastar
una corrida completa del bot. Acepta la URL de la oferta como argumento; sin
argumento toma la mejor oferta pendiente de la base de datos.
"""
from __future__ import annotations

import logging
import sys

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from browser.navegador import Navegador
from config import load_settings
from models.job_offer import JobOffer
from platforms.magneto import MagnetoPlatform
from services.tracker import MySqlApplicationTracker


def mejor_pendiente(tracker, settings) -> JobOffer | None:
    with tracker._connect() as conexion:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            """SELECT title, company_name, url, salary, location FROM jobs
               WHERE platform = 'Magneto' AND status = 'found' AND match_score >= %s
               ORDER BY match_score DESC LIMIT 1""",
            (settings.min_match_score,),
        )
        fila = cursor.fetchone()

    if not fila:
        return None
    return JobOffer(
        platform="Magneto", title=fila["title"], company=fila["company_name"] or "No especificada",
        url=fila["url"], salary=fila["salary"] or "No especificado",
        city=fila["location"] or "No especificada",
    )


def desde_url(url: str) -> JobOffer:
    return JobOffer(platform="Magneto", title="(oferta indicada a mano)", company="?",
                    url=url, salary="?", city="?")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s", datefmt="%H:%M:%S")
    settings = load_settings()
    tracker = MySqlApplicationTracker(settings)

    oferta = desde_url(sys.argv[1]) if len(sys.argv) > 1 else mejor_pendiente(tracker, settings)
    if oferta is None:
        print("No hay ofertas de Magneto pendientes.")
        return 1

    print("=" * 74)
    print(f"  OFERTA:  {oferta.title[:60]}")
    print(f"  EMPRESA: {oferta.company[:50]}")
    print(f"  URL:     {oferta.url}")
    print("=" * 74)

    with Navegador(settings) as navegador:
        plataforma = MagnetoPlatform(navegador=navegador, settings=settings, tracker=tracker)
        plataforma.ensure_logged_in()
        print("Sesion verificada.\n")

        estado = plataforma.apply(oferta)

        print()
        print("=" * 74)
        print(f"  RESULTADO: {estado}")
        print(f"  URL FINAL: {plataforma.pagina.url[:70]}")
        print("=" * 74)
        plataforma.pagina.screenshot(path="prueba_formulario.png")
        print("Captura: prueba_formulario.png")

    return 0 if estado == "aplicado" else 2


if __name__ == "__main__":
    raise SystemExit(main())
