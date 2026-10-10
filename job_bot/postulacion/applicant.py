import logging
from collections import Counter
from time import sleep

from modelos.job_offer import JobOffer
from plataformas.base import BasePlatform
from postulacion.analyzer import OfferAnalyzer
from postulacion.relevancia_cargo import Encaje, RelevanciaDelCargo
from postulacion.zona import ciudad_lejana
from almacenamiento.tracker import ApplicationTracker

from utilidades.url_utils import canonicalize_url


class ApplicationSummary:
    # Muestra de cargos no reconocidos por ciclo: basta para auditar el filtro
    # sin llenar el log.
    MUESTRA_NO_RECONOCIDOS = 15

    def __init__(self) -> None:
        self.reviewed = 0
        self.applied = 0
        self.errors = 0
        self.skipped = 0
        self.duplicates = 0
        self.off_profile = 0
        self.low_score = 0
        # Por que se descarto cada oferta fuera del perfil. Sin esto, el motivo
        # numero uno ("cargo no reconocido") paso semanas sin verse.
        self.motivos_descarte: Counter[str] = Counter()
        self.no_reconocidos: list[str] = []

    def registrar_descarte(self, motivo: str, cargo: str, reconocido: bool) -> None:
        self.motivos_descarte[motivo.split(":")[0]] += 1
        if not reconocido and len(self.no_reconocidos) < self.MUESTRA_NO_RECONOCIDOS:
            if cargo not in self.no_reconocidos:
                self.no_reconocidos.append(cargo)


class JobApplicant:
    def __init__(
        self,
        platforms: dict[str, BasePlatform],
        tracker: ApplicationTracker,
        analyzer: OfferAnalyzer,
        wait_seconds: int,
        min_match_score: int,
        supervised: bool = True,
        exhaustive: bool = False,
        max_applications: int = 0,
        relevancia: RelevanciaDelCargo | None = None,
        ciudad_base: str = "",
    ) -> None:
        self.platforms = platforms
        self.tracker = tracker
        self.analyzer = analyzer
        self.wait_seconds = wait_seconds
        self.min_match_score = min_match_score
        self.supervised = supervised
        self.exhaustive = exhaustive
        self.max_applications = max_applications
        self.relevancia = relevancia or RelevanciaDelCargo()
        # Ciudad de la que el candidato no se muda; vacia si acepta reubicarse.
        self.ciudad_base = ciudad_base

    def _confirmar(self, offer: JobOffer, analysis) -> bool:
        """Pide aprobacion antes de enviar. Una postulacion no se puede retirar.

        Sin terminal interactiva devuelve False: es preferible no postular a
        postular sin que nadie lo haya aprobado.
        """
        print('' + "=" * 78)
        print(f"  {offer.title}")
        print(f"  {offer.company}  |  {offer.city}")
        print(f"  {offer.salary}")
        print(f"  score {analysis.score}  |  {offer.platform}")
        print(f"  {offer.url}")
        print("=" * 78)
        try:
            respuesta = input("  Postular? [s = si / n = no / q = terminar]: ").strip().lower()
        except (EOFError, OSError):
            logging.warning("Modo supervisado sin terminal interactiva: no se postula.")
            return False

        if respuesta in ("q", "salir"):
            raise KeyboardInterrupt("Terminado por el operador")
        return respuesta in ("s", "si", "y", "yes")

    def apply_to_offers(self, offers: list[JobOffer]) -> ApplicationSummary:
        summary = ApplicationSummary()
        seen_urls = {canonicalize_url(url) for url in self.tracker.get_seen_urls()}

        for offer in offers:
            # El panel lanza corridas con un tope: sin este corte, el boton de
            # "20 ofertas" postulaba a todo lo que encontraba la busqueda.
            if self.max_applications and summary.applied >= self.max_applications:
                logging.info("Tope de %s postulaciones alcanzado; fin de la corrida.",
                             self.max_applications)
                break

            summary.reviewed += 1
            analysis = self.analyzer.analyze(offer)
            offer_url = canonicalize_url(str(offer.url))

            if offer_url in seen_urls:
                summary.skipped += 1
                summary.duplicates += 1
                # Van al resumen del ciclo: una linea por oferta ya vista llenaba
                # el log con cientos de avisos iguales en cada vuelta.
                logging.debug("Oferta duplicada omitida: %s", offer.url)
                continue

            # Postular a un cargo de otro oficio no suma: vuelve como descarte
            # automatico del filtro de la plataforma y ensucia el historial.
            encaje = self.relevancia.valorar(offer.title)
            if not encaje.vale_la_pena:
                summary.skipped += 1
                summary.off_profile += 1
                summary.registrar_descarte(encaje.motivo, offer.title[:70],
                                           reconocido=encaje.encaje is not Encaje.DESCONOCIDO)
                logging.debug("Fuera del perfil | %s | %s", encaje.motivo, offer.title[:70])
                seen_urls.add(offer_url)
                continue

            lejana = ciudad_lejana(offer, self.ciudad_base) if self.ciudad_base else None
            if lejana:
                summary.skipped += 1
                summary.off_profile += 1
                summary.registrar_descarte("Fuera de zona", offer.title[:70], reconocido=True)
                logging.debug("Fuera de zona (%s, sin reubicacion) | %s", lejana, offer.title[:70])
                seen_urls.add(offer_url)
                continue

            if analysis.score < self.min_match_score and not self.exhaustive:
                summary.skipped += 1
                summary.low_score += 1
                logging.debug(
                    "Descartada por score | score=%s < minimo=%s | cargo=%s | salario=%s",
                    analysis.score, self.min_match_score, offer.title, offer.salary,
                )
                continue

            if analysis.score < self.min_match_score:
                logging.info(
                    "Score bajo aceptado por modo exhaustivo | score=%s | minimo=%s | cargo=%s",
                    analysis.score, self.min_match_score, offer.title,
                )

            record_notes = analysis.notes
            if analysis.score < self.min_match_score:
                record_notes = (
                    f"{analysis.notes} | Score {analysis.score} < minimo {self.min_match_score}"
                    if analysis.notes
                    else f"Score {analysis.score} < minimo {self.min_match_score}"
                )

            try:
                plataforma = self.platforms.get(offer.platform)
                if plataforma is None:
                    logging.warning("Sin plataforma para '%s'; se omite %s", offer.platform, offer.url)
                    summary.skipped += 1
                    continue
                if self.supervised and not self._confirmar(offer, analysis):
                    summary.skipped += 1
                    logging.info("Postulacion cancelada por el operador: %s", offer.url)
                    continue
                status = plataforma.apply(offer)
                self.tracker.record(offer, status, record_notes, analysis)
                seen_urls.add(offer_url)
                if status == "aplicado":
                    summary.applied += 1
                elif status == "no disponible":
                    summary.skipped += 1
            except Exception as error:
                summary.errors += 1
                logging.exception("Error postulando a %s", offer.url)
                self.tracker.record(offer, "error", str(error), analysis)
                seen_urls.add(offer_url)

            sleep(self.wait_seconds)

        return summary
