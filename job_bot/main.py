"""Arranque del bot de empleo.

Abre la conexion al navegador, arma las plataformas habilitadas y corre ciclos
de busqueda y postulacion hasta que se le pide parar.
"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from time import sleep, time

from navegador.navegador import Navegador, NavegadorNoDisponible
from config import PerfilNoEncontrado, Settings, cargar_perfil, load_settings
from plataformas import registry
from postulacion.analyzer import OfferAnalyzer
from postulacion.applicant import ApplicationSummary, JobApplicant
from postulacion.relevancia_cargo import RelevanciaDelCargo
from postulacion.searcher import JobSearcher
from almacenamiento.tracker import ApplicationTracker, crear_tracker
from seguimiento.seguimiento_correo import crear_seguimiento

CARPETA_LOGS = Path(__file__).resolve().parent / "logs"
CICLOS_ENTRE_REVISIONES_DE_SESION = 5
# Una plataforma que perdio la sesion se reintenta, pero no mas de una vez por
# hora: cada intento de Magneto manda un codigo al correo.
MINUTOS_ENTRE_REINTENTOS_DE_SESION = 60


def configure_logging() -> None:
    CARPETA_LOGS.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            # Con rotacion: sin tope, bot.log llego a 17 MB en unos dias.
            RotatingFileHandler(CARPETA_LOGS / "bot.log", encoding="utf-8",
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
              tracker: ApplicationTracker) -> ApplicationSummary:
    applicant = JobApplicant(
        platforms=platforms,
        tracker=tracker,
        analyzer=OfferAnalyzer(settings),
        wait_seconds=settings.wait_seconds,
        min_match_score=settings.min_match_score,
        supervised=settings.supervised_apply,
        exhaustive=settings.exhaustive_mode,
        max_applications=settings.max_offers,
        relevancia=RelevanciaDelCargo(
            perfil.get("cargos"),
            acepta_vacantes_de_inclusion=bool(perfil.get("safe_booleans", {}).get("has_disability")),
        ),
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
    for motivo, veces in summary.motivos_descarte.most_common(6):
        logging.info("  descarte | %4d | %s", veces, motivo)
    if summary.no_reconocidos:
        logging.info("  cargos no reconocidos (muestra): %s", " · ".join(summary.no_reconocidos))
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


def log_preguntas_aprendidas(tracker: ApplicationTracker) -> None:
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


def con_sesion(platforms: dict) -> dict:
    """Las plataformas que tienen (o logran iniciar) sesion.

    Que caduque la sesion de una no debe parar a las demas: antes, perder la de
    Magneto detenia tambien Computrabajo, que seguia con su sesion intacta.
    """
    activas = {}
    for nombre, plataforma in platforms.items():
        try:
            plataforma.ensure_logged_in()
            activas[nombre] = plataforma
        except Exception as error:
            logging.warning("%s sin sesion por ahora: %s", nombre, str(error)[:120])
    return activas


class ControlDeSesiones:
    """Decide que plataformas trabajan en cada ciclo.

    Antes, una plataforma sin sesion al arrancar quedaba fuera de TODA la
    corrida continua aunque luego se iniciara sesion (07/10). Ahora se
    reintenta, pero no en cada ciclo: cada intento de Magneto manda un codigo
    al correo y puede esperar a la persona varios minutos.
    """

    def __init__(self, todas: dict) -> None:
        self.todas = todas
        self.activas: dict = {}
        self._ultimo_intento: dict[str, float] = {}

    def revisar_todas(self) -> dict:
        self._marcar_intento(self.todas)
        self.activas = con_sesion(self.todas)
        self._informar()
        return self.activas

    def reintentar_caidas(self) -> dict:
        limite = time() - MINUTOS_ENTRE_REINTENTOS_DE_SESION * 60
        caidas = {n: p for n, p in self.todas.items()
                  if n not in self.activas and self._ultimo_intento.get(n, 0) < limite}
        if caidas:
            self._marcar_intento(caidas)
            recuperadas = con_sesion(caidas)
            if recuperadas:
                self.activas = {**self.activas, **recuperadas}
                self._informar()
        return self.activas

    def _marcar_intento(self, plataformas: dict) -> None:
        for nombre in plataformas:
            self._ultimo_intento[nombre] = time()

    def _informar(self) -> None:
        logging.info("Plataformas activas: %s", ", ".join(self.activas) or "ninguna")


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
    tracker = crear_tracker(settings)
    # Solo el tracker de Supabase tiene cliente: con MySQL no hay donde guardar eventos.
    seguimiento = crear_seguimiento(settings.magneto_email, settings.correo_codigos_clave_app,
                                    getattr(tracker, "cliente", None))
    ciclos = 0

    try:
        with Navegador(settings) as navegador:
            sesiones = ControlDeSesiones(
                registry.crear(settings.enabled_platforms, navegador, settings, tracker))
            tracker.ensure_questions_table()

            logging.info("Verificando sesiones...")
            if not sesiones.revisar_todas():
                raise RuntimeError("Ninguna plataforma tiene sesion iniciada.")

            while True:
                ciclos += 1
                logging.info("-" * 78)
                logging.info("Ciclo #%d", ciclos)

                # Una revision de sesion fallida no puede terminar la corrida:
                # asi murio el bot tras cinco ciclos, con el navegador aun vivo.
                try:
                    if ciclos % CICLOS_ENTRE_REVISIONES_DE_SESION == 0:
                        sesiones.revisar_todas()
                    else:
                        sesiones.reintentar_caidas()
                except Exception as error:
                    logging.warning("No se pudo revisar la sesion: %s", str(error)[:90])

                try:
                    if sesiones.activas:
                        log_summary(run_cycle(settings, perfil, sesiones.activas, tracker))
                    else:
                        logging.warning("Ninguna plataforma con sesion en este ciclo.")
                except Exception:
                    logging.exception("Error en el ciclo #%d", ciclos)

                # El seguimiento del correo es accesorio: nunca tumba un ciclo.
                if seguimiento:
                    try:
                        seguimiento.revisar_si_toca()
                    except Exception as error:
                        logging.warning("Seguimiento del correo fallo: %s", str(error)[:90])

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
