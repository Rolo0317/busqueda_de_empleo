import logging
from time import sleep

from models.job_offer import JobOffer
from platforms.base import BasePlatform
from services.analyzer import OfferAnalyzer
from services.tracker import ApplicationTracker


class ApplicationSummary:
    def __init__(self) -> None:
        self.reviewed = 0
        self.applied = 0
        self.errors = 0
        self.skipped = 0


class JobApplicant:
    def __init__(
        self,
        platform: BasePlatform,
        tracker: ApplicationTracker,
        analyzer: OfferAnalyzer,
        wait_seconds: int,
        min_match_score: int,
    ) -> None:
        self.platform = platform
        self.tracker = tracker
        self.analyzer = analyzer
        self.wait_seconds = wait_seconds
        self.min_match_score = min_match_score

    def apply_to_offers(self, offers: list[JobOffer]) -> ApplicationSummary:
        summary = ApplicationSummary()
        seen_urls = self.tracker.get_seen_urls()

        for offer in offers:
            summary.reviewed += 1
            analysis = self.analyzer.analyze(offer)

            if str(offer.url) in seen_urls:
                summary.skipped += 1
                logging.info("Oferta duplicada omitida: %s", offer.url)
                continue

            if analysis.score < self.min_match_score:
                summary.skipped += 1
                logging.info(
                    "Oferta descartada | score=%s | minimo=%s | cargo=%s | salario=%s | notas=%s",
                    analysis.score,
                    self.min_match_score,
                    offer.title,
                    offer.salary,
                    analysis.notes,
                )
                self.tracker.record(offer, "descartado", analysis.notes, analysis)
                seen_urls.add(str(offer.url))
                continue

            try:
                status = self.platform.apply(offer)
                self.tracker.record(offer, status, analysis.notes, analysis)
                seen_urls.add(str(offer.url))
                if status == "aplicado":
                    summary.applied += 1
                elif status == "no disponible":
                    summary.skipped += 1
            except Exception as error:
                summary.errors += 1
                logging.exception("Error postulando a %s", offer.url)
                self.tracker.record(offer, "error", str(error), analysis)
                seen_urls.add(str(offer.url))

            sleep(self.wait_seconds)

        return summary
