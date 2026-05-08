from typing import Any, Protocol

import mysql.connector
from mysql.connector import MySQLConnection

from config import Settings
from models.job_offer import JobOffer
from services.analyzer import OfferAnalysis


class ApplicationTracker(Protocol):
    def get_seen_urls(self) -> set[str]:
        ...

    def get_applied_urls(self) -> set[str]:
        ...

    def record(self, offer: JobOffer, status: str, notes: str = "", analysis: OfferAnalysis | None = None) -> None:
        ...


class MySqlApplicationTracker:
    STATUS_MAP = {
        "aplicado": "applied",
        "descartado": "discarded",
        "no disponible": "no_available",
        "error": "error",
        "applied": "applied",
        "discarded": "discarded",
        "no_available": "no_available",
    }

    APPLICATION_STATUSES = {"applied", "error", "no_available"}
    FINAL_JOB_STATUSES = {"applied", "discarded"}

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def get_seen_urls(self) -> set[str]:
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT url FROM jobs WHERE status IN (%s, %s)",
                tuple(self.FINAL_JOB_STATUSES),
            )
            return {str(row[0]) for row in cursor.fetchall() if row[0]}
        finally:
            cursor.close()
            connection.close()

    def get_applied_urls(self) -> set[str]:
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT url FROM jobs WHERE status = %s", ("applied",))
            return {str(row[0]) for row in cursor.fetchall() if row[0]}
        finally:
            cursor.close()
            connection.close()

    def record(self, offer: JobOffer, status: str, notes: str = "", analysis: OfferAnalysis | None = None) -> None:
        db_status = self._to_db_status(status)
        connection = self._connect()
        try:
            cursor = connection.cursor()
            company_id = self._upsert_company(cursor, offer.company)
            job_id = self._upsert_job(cursor, company_id, offer, db_status, notes, analysis)
            self._sync_skills(cursor, job_id, analysis.matched_skills if analysis else [])

            if db_status in self.APPLICATION_STATUSES:
                self._record_application(cursor, job_id, db_status, notes)

            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def _connect(self) -> MySQLConnection:
        return mysql.connector.connect(
            host=self.settings.db_host,
            port=self.settings.db_port,
            user=self.settings.db_user,
            password=self.settings.db_password,
            database=self.settings.db_name,
        )

    def _upsert_company(self, cursor: Any, name: str) -> int:
        company_name = name or "Confidencial"
        cursor.execute(
            """
            INSERT INTO companies (name)
            VALUES (%s)
            ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP
            """,
            (company_name,),
        )
        cursor.execute("SELECT id FROM companies WHERE name = %s", (company_name,))
        return int(cursor.fetchone()[0])

    def _upsert_job(
        self,
        cursor: Any,
        company_id: int,
        offer: JobOffer,
        status: str,
        notes: str,
        analysis: OfferAnalysis | None,
    ) -> int:
        score = analysis.score if analysis else 0
        priority = analysis.priority if analysis else "normal"
        recommendation = self._recommendation(status)
        description = self._append_notes(offer.description, notes)
        cursor.execute(
            """
            INSERT INTO jobs
              (company_id, platform, title, company_name, salary, location, modality,
               published_at, url, description, match_score, priority, recommendation, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              company_id = VALUES(company_id),
              platform = VALUES(platform),
              title = VALUES(title),
              company_name = VALUES(company_name),
              salary = VALUES(salary),
              location = VALUES(location),
              published_at = VALUES(published_at),
              description = VALUES(description),
              match_score = VALUES(match_score),
              priority = VALUES(priority),
              recommendation = VALUES(recommendation),
              status = VALUES(status),
              last_seen_at = CURRENT_TIMESTAMP,
              updated_at = CURRENT_TIMESTAMP
            """,
            (
                company_id,
                offer.platform,
                offer.title,
                offer.company,
                offer.salary,
                offer.city,
                "No especificada",
                offer.published_at,
                str(offer.url),
                description,
                score,
                priority,
                recommendation,
                status,
            ),
        )
        cursor.execute("SELECT id FROM jobs WHERE url = %s", (str(offer.url),))
        return int(cursor.fetchone()[0])

    def _sync_skills(self, cursor: Any, job_id: int, skills: list[str]) -> None:
        for skill in skills:
            cursor.execute(
                "INSERT INTO skills (name) VALUES (%s) ON DUPLICATE KEY UPDATE name = VALUES(name)",
                (skill,),
            )
            cursor.execute("SELECT id FROM skills WHERE name = %s", (skill,))
            skill_id = int(cursor.fetchone()[0])
            cursor.execute(
                "INSERT IGNORE INTO job_skills (job_id, skill_id) VALUES (%s, %s)",
                (job_id, skill_id),
            )

    def _record_application(self, cursor: Any, job_id: int, status: str, response: str) -> None:
        cursor.execute(
            """
            INSERT INTO applications (job_id, status, response)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
              status = VALUES(status),
              response = VALUES(response),
              updated_at = CURRENT_TIMESTAMP
            """,
            (job_id, status, response),
        )

    def _to_db_status(self, status: str) -> str:
        normalized = status.strip().lower()
        return self.STATUS_MAP.get(normalized, "error")

    @staticmethod
    def _recommendation(status: str) -> str:
        if status == "discarded":
            return "Descartar por baja coincidencia"
        if status == "applied":
            return "Postulacion enviada"
        if status == "no_available":
            return "No disponible para aplicar"
        return "Revisar error"

    @staticmethod
    def _append_notes(description: str, notes: str) -> str:
        if not notes:
            return description
        if not description:
            return f"Notas: {notes}"
        return f"{description}\n\nNotas: {notes}"
