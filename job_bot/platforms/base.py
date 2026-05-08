from abc import ABC, abstractmethod

from models.job_offer import JobOffer


class BasePlatform(ABC):
    @abstractmethod
    def search(self, keyword: str) -> list[JobOffer]:
        raise NotImplementedError

    @abstractmethod
    def apply(self, offer: JobOffer) -> str:
        raise NotImplementedError
