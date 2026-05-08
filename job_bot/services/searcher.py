from models.job_offer import JobOffer
from platforms.base import BasePlatform


class JobSearcher:
    def __init__(self, platform: BasePlatform, max_offers: int) -> None:
        self.platform = platform
        self.max_offers = max_offers

    def search_many(self, keywords: list[str]) -> list[JobOffer]:
        offers_by_url: dict[str, JobOffer] = {}

        for keyword in keywords:
            for offer in self.platform.search(keyword):
                offers_by_url.setdefault(str(offer.url), offer)
                if len(offers_by_url) >= self.max_offers:
                    return list(offers_by_url.values())

        return list(offers_by_url.values())
