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

    def record_question(self, question: str, answer: str, confidence: float, job_id: int | None = None) -> None:
        """Guardar pregunta respondida en la BD para análisis posterior."""
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO questions (question_text, answer_given, confidence_score, job_id)
                VALUES (%s, %s, %s, %s)
                """,
                (question, answer, confidence, job_id),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def get_question_patterns(self) -> dict[str, dict]:
        """Obtener patrones de preguntas frecuentes para optimizar respuestas."""
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT 
                    SUBSTRING_INDEX(question_text, '?', 1) AS pattern,
                    COUNT(*) as count,
                    AVG(confidence_score) as avg_confidence
                FROM questions
                WHERE created_at > DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY pattern
                ORDER BY count DESC
                LIMIT 20
                """
            )
            patterns = {}
            for row in cursor.fetchall():
                patterns[row[0]] = {
                    "count": row[1],
                    "avg_confidence": row[2]
                }
            return patterns
        finally:
            cursor.close()
            connection.close()

    def ensure_questions_table(self) -> None:
        """Crear tabla de preguntas si no existe."""
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS questions (
                    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    job_id BIGINT UNSIGNED NULL,
                    question_text VARCHAR(1000) NOT NULL,
                    answer_given VARCHAR(500) NOT NULL,
                    confidence_score DECIMAL(3,2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE SET NULL,
                    INDEX idx_created_at (created_at),
                    INDEX idx_question_text (question_text(100))
                )
                """
            )
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def _append_notes(description: str, notes: str) -> str:
        if not notes:
            return description
        if not description:
            return f"Notas: {notes}"
        return f"{description}\n\nNotas: {notes}"
