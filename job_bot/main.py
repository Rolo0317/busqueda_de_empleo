import logging
from pathlib import Path
from time import sleep

from selenium.webdriver.support.ui import WebDriverWait

from browser.driver import create_browser_driver
from config import Settings, load_settings
from platforms.magneto import MagnetoPlatform
from services.analyzer import OfferAnalyzer
from services.applicant import ApplicationSummary, JobApplicant
from services.searcher import JobSearcher
from services.tracker import MySqlApplicationTracker


def configure_logging() -> None:
    log_path = Path(__file__).with_name("bot.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
    )


def run_cycle(settings: Settings, platform: MagnetoPlatform, tracker: MySqlApplicationTracker) -> ApplicationSummary:
    analyzer = OfferAnalyzer(settings)
    searcher = JobSearcher(platform=platform, max_offers=settings.max_offers)
    applicant = JobApplicant(
        platform=platform,
        tracker=tracker,
        analyzer=analyzer,
        wait_seconds=settings.wait_seconds,
        min_match_score=settings.min_match_score,
    )

    offers = searcher.search_many(settings.search_keywords)
    return applicant.apply_to_offers(offers)


def log_summary(summary: ApplicationSummary) -> None:
    logging.info(
        "📊 RESUMEN CICLO | 👀 revisadas=%s | ✅ aplicadas=%s | ❌ errores=%s | ⏭️ omitidas=%s",
        summary.reviewed,
        summary.applied,
        summary.errors,
        summary.skipped,
    )
    print(
        f"\n{'='*80}\n"
        f"📊 RESUMEN CICLO:\n"
        f"  👀 Ofertas revisadas: {summary.reviewed}\n"
        f"  ✅ Postulaciones enviadas: {summary.applied}\n"
        f"  ❌ Errores: {summary.errors}\n"
        f"  ⏭️ Omitidas: {summary.skipped}\n"
        f"{'='*80}\n"
    )


def main() -> None:
    configure_logging()
    logging.info("=" * 80)
    logging.info("INICIANDO BOT DE EMPLEO - %s", Path(__file__).resolve())
    logging.info("=" * 80)
    
    settings = load_settings()
    driver = create_browser_driver(settings)
    cycle_count = 0
    login_check_interval = 5  # Verificar login cada 5 ciclos

    try:
        wait = WebDriverWait(driver, max(20, settings.wait_seconds))
        platform = MagnetoPlatform(driver=driver, wait=wait, settings=settings, tracker=tracker)
        tracker.ensure_questions_table()

        logging.info("Verificando login inicial...")
        platform.ensure_logged_in()
        logging.info("✅ Login verificado al inicio")

        while True:
            cycle_count += 1
            logging.info("-" * 80)
            logging.info("Iniciando ciclo #%d", cycle_count)

            # Verificar login periódicamente
            if cycle_count % login_check_interval == 0:
                logging.info("Verificando estado de login (cada %d ciclos)...", login_check_interval)
                try:
                    platform.ensure_logged_in()
                    logging.info("✅ Login renovado exitosamente")
                except Exception as login_error:
                    logging.error("❌ Error al renovar login: %s", login_error)
                    logging.info("Intentando reconectar...")
                    driver.refresh()
                    sleep(5)
                    platform.ensure_logged_in()

            try:
                summary = run_cycle(settings, platform, tracker)
                log_summary(summary)
            except Exception as cycle_error:
                logging.exception("❌ Error en ciclo #%d: %s", cycle_count, cycle_error)

            if not settings.run_continuously:
                logging.info("Modo de ejecución única - terminando bot")
                break

            logging.info("Esperando %s segundos para el siguiente ciclo...", settings.loop_interval_seconds)
            sleep(settings.loop_interval_seconds)
            
    except KeyboardInterrupt:
        logging.info("⚠️ Bot detenido por el usuario (Ctrl+C)")
    except Exception as fatal_error:
        logging.exception("❌ Error fatal: %s", fatal_error)
    finally:
        logging.info("Limpiando recursos...")
        try:
            driver.quit()
            logging.info("✅ Driver de navegador cerrado")
        except Exception as cleanup_error:
            logging.error("Error al cerrar driver: %s", cleanup_error)
        
        # Mostrar resumen de preguntas aprendidas
        try:
            patterns = tracker.get_question_patterns()
            if patterns:
                logging.info("=" * 80)
                logging.info("📚 PREGUNTAS FRECUENTES DETECTADAS (últimos 7 días):")
                for pattern, stats in list(patterns.items())[:10]:
                    logging.info(
                        "  • %s... (veces=%s, confianza=%.2f%%)",
                        pattern[:80],
                        stats["count"],
                        stats["avg_confidence"] * 100,
                    )
                logging.info("=" * 80)
        except Exception as e:
            logging.debug("Error obteniendo patrones de preguntas: %s", e)
        
        logging.info("=" * 80)
        logging.info("Bot terminado. Ciclos completados: %d", cycle_count)
        logging.info("=" * 80)


if __name__ == "__main__":
    main()
