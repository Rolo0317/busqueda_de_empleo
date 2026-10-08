"""Tracker sobre Supabase: cada operacion es una funcion public.empleo_*.

La transaccion de record() (empresa, vacante, habilidades y postulacion) la
hace Postgres dentro de empleo_registrar_oferta, en un solo viaje de red.
"""
from __future__ import annotations

from config import Settings
from models.job_offer import JobOffer
from services.analyzer import OfferAnalysis
from services.supabase_cliente import ClienteSupabase
from services.tracker import ReglasDeRegistro


class SupabaseApplicationTracker(ReglasDeRegistro):
    def __init__(self, settings: Settings, cliente: ClienteSupabase | None = None) -> None:
        self.settings = settings
        self.cliente = cliente or ClienteSupabase.desde_settings(settings)

    def get_seen_urls(self) -> set[str]:
        filas = self.cliente.rpc("empleo_urls_vistas", {
            "p_estados_finales": sorted(self.FINAL_JOB_STATUSES),
            "p_estados_reintento": sorted(self.RETRY_JOB_STATUSES),
            "p_horas_reintento": self.RETRY_AFTER_HOURS,
        })
        return {str(url) for url in filas or [] if url}

    def get_applied_urls(self) -> set[str]:
        filas = self.cliente.rpc("empleo_urls_con_estado", {"p_estado": "applied"})
        return {str(url) for url in filas or [] if url}

    def record(self, offer: JobOffer, status: str, notes: str = "", analysis: OfferAnalysis | None = None) -> None:
        db_status = self._to_db_status(status)
        self.cliente.rpc("empleo_registrar_oferta", {
            "p_oferta": {
                "platform": offer.platform,
                "title": offer.title,
                "company_name": offer.company,
                "salary": offer.salary,
                "location": offer.city,
                "modality": self.MODALIDAD_DESCONOCIDA,
                "published_at": offer.published_at,
                "url": str(offer.url),
                "description": self._append_notes(offer.description, notes),
                "match_score": analysis.score if analysis else 0,
                "priority": analysis.priority if analysis else "normal",
                "recommendation": self._recommendation(db_status),
                "status": db_status,
                "response": notes,
            },
            "p_habilidades": analysis.matched_skills if analysis else [],
            "p_registrar_postulacion": db_status in self.APPLICATION_STATUSES,
        })

    def record_question(self, question: str, answer: str, confidence: float, job_id: int | None = None) -> None:
        self.cliente.rpc("empleo_registrar_pregunta", {
            "p_pregunta": question,
            "p_respuesta": answer,
            "p_confianza": round(confidence, 2),
            "p_job_id": job_id,
        })

    def get_question_patterns(self) -> dict[str, dict]:
        return self.cliente.rpc("empleo_patrones_preguntas") or {}

    def ensure_questions_table(self) -> None:
        """El esquema lo crea la migracion de Supabase; aqui no hay nada que hacer."""

    def ofertas_pendientes(self, plataforma: str, min_score: int, limite: int) -> list[JobOffer]:
        filas = self.cliente.rpc("empleo_ofertas_pendientes", {
            "p_plataforma": plataforma, "p_min_score": min_score, "p_limite": limite,
        })
        return [self._oferta_desde_fila(fila, plataforma) for fila in filas or []]
