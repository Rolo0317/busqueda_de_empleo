import re
import unicodedata
from dataclasses import dataclass

from config import Settings
from models.job_offer import JobOffer


@dataclass(frozen=True)
class OfferAnalysis:
    score: int
    priority: str
    matched_skills: list[str]
    notes: str


class OfferAnalyzer:
    HIGH_VALUE_WORDS = (
        "senior",
        "semi senior",
        "semisenior",
        "remote",
        "remoto",
        "teletrabajo",
        "hibrido",
        "hybrid",
    )

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def analyze(self, offer: JobOffer) -> OfferAnalysis:
        text = self._normalize(" ".join([offer.title, offer.company, offer.city, offer.salary, offer.description]))
        matched_skills = [skill for skill in self.settings.skills if self._matches_skill(skill, text)]
        score = self._calculate_score(text, matched_skills, offer)
        if not self.is_salary_acceptable(offer):
            score = 0
        priority = "alta" if self._is_high_priority(text, offer, score) else "normal"
        notes = self._build_notes(offer, matched_skills, text)
        return OfferAnalysis(score=min(score, 100), priority=priority, matched_skills=matched_skills, notes=notes)

    def is_salary_acceptable(self, offer: JobOffer) -> bool:
        salary_text = self._normalize(offer.salary)
        salary_value = self._salary_value(offer.salary)
        if salary_value >= self.settings.min_salary:
            return True
        return salary_value == 0 and any(word in salary_text for word in ("convenir", "confidencial", "no especificado"))

    def _calculate_score(self, text: str, matched_skills: list[str], offer: JobOffer) -> int:
        score = 25
        score += min(len(matched_skills) * 8, 40)

        if any(self._normalize(location) in text for location in self.settings.locations):
            score += 10
        if any(word in text for word in ("remoto", "remote", "teletrabajo", "hibrido")):
            score += 10
        if any(
            role in text
            for role in (
                "full stack",
                "fullstack",
                "frontend",
                "backend",
                "react",
                "node",
                "software engineer",
                "desarrollador",
                "desarrolladora",
                "desarrollo de software",
                "ingeniero de software",
            )
        ):
            score += 10
        if any(word in text for word in ("senior", "semi senior", "semisenior")):
            score += 5
        salary_value = self._salary_value(offer.salary)
        if salary_value >= self.settings.min_salary:
            score += 10
        if salary_value >= 8_000_000:
            score += 15

        return score

    def _is_high_priority(self, text: str, offer: JobOffer, score: int) -> bool:
        has_seniority = any(word in text for word in self.HIGH_VALUE_WORDS)
        has_high_salary = self._salary_value(offer.salary) >= 8_000_000
        return score >= self.settings.min_match_score and (has_seniority or has_high_salary)

    def _build_notes(self, offer: JobOffer, matched_skills: list[str], text: str) -> str:
        notes = []
        if matched_skills:
            notes.append(f"Skills: {', '.join(matched_skills)}")
        if "remoto" in text or "remote" in text or "teletrabajo" in text:
            notes.append("Remoto")
        if "hibrido" in text:
            notes.append("Hibrido")
        if self._salary_value(offer.salary) >= 8_000_000:
            notes.append("Salario alto")
        if not self.is_salary_acceptable(offer):
            notes.append(f"Salario menor a {self.settings.min_salary}")
        return " | ".join(notes)

    @classmethod
    def _matches_skill(cls, skill: str, text: str) -> bool:
        normalized_skill = cls._normalize(skill).strip()
        explicit_patterns = {
            "ia": r"\b(?:ia|ai)\b|inteligencia artificial",
            "api": r"\bapi(?:s)?\b|\brest\b",
            "apis": r"\bapi(?:s)?\b|\brest\b",
            "node.js": r"\bnode(?:\.js|js)?\b",
            "nodejs": r"\bnode(?:\.js|js)?\b",
            "next.js": r"\bnext(?:\.js|js)?\b",
            "fullstack": r"\bfull\s*stack\b|\bfullstack\b",
            "full stack": r"\bfull\s*stack\b|\bfullstack\b",
            ".net": r"(?:^|[^a-z0-9])(?:\.net|net core|asp\.net)(?:[^a-z0-9]|$)",
            "c#": r"(?:^|[^a-z0-9])(?:c#|c sharp)(?:[^a-z0-9]|$)",
            "sql": r"\bsql\b|sql server|\bmysql\b|\bpostgres(?:ql)?\b|\boracle\b",
        }

        pattern = explicit_patterns.get(normalized_skill)
        if pattern:
            return bool(re.search(pattern, text))

        escaped = re.escape(normalized_skill).replace(r"\ ", r"\s+")
        return bool(re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text))

    @staticmethod
    def _salary_value(salary: str) -> int:
        numbers = [int(value.replace(".", "").replace(",", "")) for value in re.findall(r"\d[\d.,]*", salary)]
        return max(numbers, default=0)

    @staticmethod
    def _normalize(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
        return normalized.lower()
