"""Arranque del bot de empleo.

Abre la conexion al navegador, arma las plataformas habilitadas y corre ciclos
de busqueda y postulacion hasta que se le pide parar.
"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from time import sleep

from browser.navegador import Navegador, NavegadorNoDisponible
from config import PerfilNoEncontrado, Settings, cargar_perfil, load_settings
from platforms import registry
from services.analyzer import OfferAnalyzer
from services.applicant import ApplicationSummary, JobApplicant
from services.relevancia_cargo import RelevanciaDelCargo
from services.searcher import JobSearcher
from services.tracker import MySqlApplicationTracker

CICLOS_ENTRE_REVISIONES_DE_SESION = 5


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            # Con rotacion: sin tope, bot.log llego a 17 MB en unos dias.
            RotatingFileHandler(Path(__file__).with_name("bot.log"), encoding="utf-8",
                                maxBytes=5_000_000, backupCount=2),
        ],
    )


def ciudad_base(perfil: dict) -> str:
    """La ciudad del perfil si el candidato no acepta reubicarse; vacia si si acepta.

    Ante la duda se asume que acepta, para no perder ofertas.
    """
    if perfil.get("availability", {}).get("relocation", True):
        return ""
    return str(perfil.get("city", ""))


def run_cycle(settings: Settings, perfil: dict, platforms: dict,
              tracker: MySqlApplicationTracker) -> ApplicationSummary:
    applicant = JobApplicant(
        platforms=platforms,
        tracker=tracker,
        analyzer=OfferAnalyzer(settings),
        wait_seconds=settings.wait_seconds,
        min_match_score=settings.min_match_score,
        supervised=settings.supervised_apply,
        exhaustive=settings.exhaustive_mode,
        max_applications=settings.max_offers,
        relevancia=RelevanciaDelCargo(perfil.get("cargos")),
        ciudad_base=ciudad_base(perfil),
    )
    ofertas = JobSearcher(platforms=platforms).search_many(settings.search_keywords)
    return applicant.apply_to_offers(ofertas)


def log_summary(summary: ApplicationSummary) -> None:
    logging.info(
        "RESUMEN CICLO | revisadas=%s | aplicadas=%s | errores=%s | omitidas=%s "
        "(ya vistas=%s, fuera del perfil=%s, score bajo=%s)",
        summary.reviewed, summary.applied, summary.errors, summary.skipped,
        summary.duplicates, summary.off_profile, summary.low_score,
    )
    print(
        f"\n{'=' * 78}\n"
        f"  Ofertas revisadas:      {summary.reviewed}\n"
        f"  Postulaciones enviadas: {summary.applied}\n"
        f"  Errores:                {summary.errors}\n"
        f"  Omitidas:               {summary.skipped}"
        f" (ya vistas {summary.duplicates}, fuera del perfil {summary.off_profile},"
        f" score bajo {summary.low_score})\n"
        f"{'=' * 78}\n"
    )


def log_preguntas_aprendidas(tracker: MySqlApplicationTracker) -> None:
    try:
        patrones = tracker.get_question_patterns()
    except Exception as error:
        logging.debug("No se pudieron leer los patrones de preguntas: %s", error)
        return

    if not patrones:
        return
    logging.info("PREGUNTAS FRECUENTES (ultimos 7 dias):")
    for patron, datos in list(patrones.items())[:10]:
        logging.info("  %s... (veces=%s, confianza=%.0f%%)",
                     patron[:80], datos["count"], datos["avg_confidence"] * 100)


def revisar_sesiones(platforms: dict) -> None:
    """Deja solo las plataformas con sesion activa.

    Que caduque la sesion de una no debe parar a las demas: antes, perder la de
    Magneto detenia tambien Computrabajo, que seguia con su sesion intacta.
    """
    for nombre, plataforma in list(platforms.items()):
        try:
            plataforma.ensure_logged_in()
        except Exception as error:
            logging.warning("%s queda fuera de esta corrida: %s", nombre, str(error)[:120])
            del platforms[nombre]
    if not platforms:
        raise RuntimeError("Ninguna plataforma tiene sesion iniciada.")
    logging.info("Plataformas activas: %s", ", ".join(platforms))


def main() -> None:
    configure_logging()
    logging.info("=" * 78)
    logging.info("INICIANDO BOT DE EMPLEO (Playwright)")
    logging.info("=" * 78)

    settings = load_settings()
    try:
        perfil = cargar_perfil(settings)
    except PerfilNoEncontrado as error:
        logging.error("%s", error)
        return
    tracker = MySqlApplicationTracker(settings)
    ciclos = 0

    try:
        with Navegador(settings) as navegador:
            platforms = registry.crear(settings.enabled_platforms, navegador, settings, tracker)
            tracker.ensure_questions_table()

            logging.info("Verificando sesiones...")
            revisar_sesiones(platforms)

            while True:
                ciclos += 1
                logging.info("-" * 78)
                logging.info("Ciclo #%d", ciclos)

                # Una revision de sesion fallida no puede terminar la corrida:
                # asi murio el bot tras cinco ciclos, con el navegador aun vivo.
                if ciclos % CICLOS_ENTRE_REVISIONES_DE_SESION == 0:
                    try:
                        revisar_sesiones(platforms)
                    except Exception as error:
                        logging.warning("No se pudo revisar la sesion: %s", str(error)[:90])

                try:
                    log_summary(run_cycle(settings, perfil, platforms, tracker))
                except Exception:
                    logging.exception("Error en el ciclo #%d", ciclos)

                if not settings.run_continuously:
                    logging.info("Modo de ejecucion unica: terminando.")
                    break

                logging.info("Esperando %ss para el siguiente ciclo...", settings.loop_interval_seconds)
                sleep(settings.loop_interval_seconds)

    except NavegadorNoDisponible as error:
        logging.error("%s", error)
    except KeyboardInterrupt:
        logging.info("Bot detenido por el usuario.")
    except Exception:
        logging.exception("Error fatal")
    finally:
        log_preguntas_aprendidas(tracker)
        logging.info("Bot terminado. Ciclos completados: %d", ciclos)


if __name__ == "__main__":
    main()
