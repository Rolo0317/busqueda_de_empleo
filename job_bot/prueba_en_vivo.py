"""Postula oferta por oferta mostrando cada pregunta y su respuesta.

Sirve para auditar lo que el bot esta contestando de verdad antes de dejarlo
correr solo: imprime el cuestionario completo de cada oferta y para al final
con un resumen de que se envio y que quedo pendiente.

Uso:  python prueba_en_vivo.py [cuantas]
"""
from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from browser.navegador import Navegador
from config import load_settings
from models.job_offer import JobOffer
from platforms.magneto import MagnetoPlatform
from services.analyzer import OfferAnalyzer
from services.tracker import MySqlApplicationTracker

ANCHO = 88


@dataclass
class Auditoria:
    """Lo que el bot contesto en cada oferta, para revisarlo despues."""

    resultados: list[tuple[str, str]] = field(default_factory=list)
    respuestas: list[tuple[str, str]] = field(default_factory=list)

    def anotar_respuesta(self, pregunta: str, respuesta: str) -> None:
        self.respuestas.append((pregunta, respuesta))
        print(f"    P: {pregunta[:80]}")
        print(f"    R: {respuesta[:80]}")

    def resumen(self) -> None:
        print()
        print("=" * ANCHO)
        print("  RESUMEN")
        print("=" * ANCHO)
        for titulo, estado in self.resultados:
            print(f"  [{estado:<22}] {titulo[:58]}")
        print(f"\n  Preguntas contestadas en total: {len(self.respuestas)}")


def ofertas_pendientes(tracker, settings, cuantas: int) -> list[JobOffer]:
    with tracker._connect() as conexion:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            """SELECT title, company_name, url, salary, location FROM jobs
               WHERE platform = 'Magneto' AND status = 'found' AND match_score >= %s
               ORDER BY match_score DESC LIMIT %s""",
            (settings.min_match_score, cuantas),
        )
        filas = cursor.fetchall()

    return [JobOffer(platform="Magneto", title=f["title"], url=f["url"],
                     company=f["company_name"] or "No especificada",
                     salary=f["salary"] or "No especificado",
                     city=f["location"] or "No especificada") for f in filas]


def todas_caducadas(plataforma: MagnetoPlatform, ofertas: list[JobOffer]) -> bool:
    """Una muestra basta: si las dos primeras no abren, el lote esta vencido."""
    return not any(plataforma.abrir(str(o.url)) for o in ofertas[:2])


def buscar_frescas(plataforma: MagnetoPlatform, tracker, settings, cuantas: int) -> list[JobOffer]:
    """Busca ofertas nuevas y descarta las que ya se trabajaron."""
    from core.url_utils import canonicalize_url

    vistas = {canonicalize_url(u) for u in tracker.get_seen_urls()}
    frescas: list[JobOffer] = []

    for palabra in settings.search_keywords:
        print(f"  buscando: {palabra}")
        for oferta in plataforma.search(palabra):
            if canonicalize_url(str(oferta.url)) in vistas:
                continue
            vistas.add(canonicalize_url(str(oferta.url)))
            frescas.append(oferta)
            if len(frescas) >= cuantas:
                return frescas
    return frescas


def con_auditoria(plataforma: MagnetoPlatform, auditoria: Auditoria) -> None:
    """Envuelve el registro de preguntas para verlas en pantalla."""
    registrar = plataforma._registrar

    def espiar(pregunta: str, respuesta: str, confianza: float) -> None:
        auditoria.anotar_respuesta(pregunta, respuesta)
        registrar(pregunta, respuesta, confianza)

    plataforma._registrar = espiar


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="  . %(message)s")
    cuantas = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    settings = load_settings()
    tracker = MySqlApplicationTracker(settings)
    analyzer = OfferAnalyzer(settings)
    auditoria = Auditoria()

    ofertas = ofertas_pendientes(tracker, settings, cuantas)
    if not ofertas:
        print("No hay ofertas pendientes con el score minimo.")
        return 1

    with Navegador(settings) as navegador:
        plataforma = MagnetoPlatform(navegador=navegador, settings=settings, tracker=tracker)
        con_auditoria(plataforma, auditoria)
        plataforma.ensure_logged_in()

        # Las ofertas guardadas caducan: si ninguna abre, se busca en vivo.
        if not ofertas or todas_caducadas(plataforma, ofertas):
            ofertas = buscar_frescas(plataforma, tracker, settings, cuantas)
            if not ofertas:
                print("La busqueda no devolvio ofertas nuevas.")
                return 1

        for numero, oferta in enumerate(ofertas, 1):
            print()
            print("=" * ANCHO)
            print(f"  {numero}/{len(ofertas)}  {oferta.title[:64]}")
            print(f"  {oferta.company[:40]} | {oferta.salary[:30]}")
            print("=" * ANCHO)

            try:
                estado = plataforma.apply(oferta)
            except Exception as error:
                estado = f"error: {str(error)[:40]}"

            print(f"  --> {estado}")
            auditoria.resultados.append((oferta.title, estado))
            tracker.record(oferta, estado, "Prueba en vivo", analyzer.analyze(oferta))

    auditoria.resumen()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
