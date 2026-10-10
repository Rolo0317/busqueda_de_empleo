import logging

from modelos.job_offer import JobOffer
from utilidades.url_utils import canonicalize_url
from plataformas.base import BasePlatform


class JobSearcher:
    """Busca en todas las plataformas habilitadas y deduplica por URL."""

    def __init__(self, platforms: dict[str, BasePlatform]) -> None:
        self.platforms = platforms

    def search_many(self, keywords: list[str]) -> list[JobOffer]:
        offers_by_url: dict[str, JobOffer] = {}

        for nombre, plataforma in self.platforms.items():
            for keyword in keywords:
                # Una plataforma caida no debe tumbar el ciclo completo: se
                # registra y se sigue con las demas.
                try:
                    encontradas = plataforma.search(keyword)
                except Exception:
                    logging.exception("Fallo la busqueda en %s con '%s'", nombre, keyword)
                    continue

                for offer in encontradas:
                    offers_by_url.setdefault(canonicalize_url(str(offer.url)), offer)

        return list(offers_by_url.values())
