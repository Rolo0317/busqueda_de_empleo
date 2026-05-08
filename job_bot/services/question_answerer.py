import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AnswerDecision:
    value: str | None
    confidence: float
    reason: str
    should_answer: bool


class CandidateQuestionAnswerer:
    def __init__(self, profile_path: Path) -> None:
        self.profile = self._load_profile(profile_path)

    def answer(self, question: str, options: list[str]) -> AnswerDecision:
        normalized = self._normalize(question)
        normalized_options = [self._normalize(option) for option in options]

        if self._looks_like_option_text(normalized) or self._looks_like_noise_text(normalized):
            return self._skip("Texto visible no parece pregunta")

        if self._has_any(normalized, self.profile.get("never_answer_keywords", [])):
            return self._skip("Pregunta sensible fuera del perfil")

        boolean_like = self._looks_like_boolean_question(normalized, normalized_options)
        boolean_answer = self._answer_boolean(normalized, normalized_options)
        if boolean_answer.should_answer:
            if options and boolean_answer.value:
                option_answer = self._match_boolean_option(options, normalized_options, boolean_answer.value, boolean_answer.reason)
                if option_answer.should_answer:
                    return option_answer
            return boolean_answer

        # If the field is a finite choice, never fall through to free-text/numeric
        # answers. This prevents typing "5" into a Si/No style question.
        if options:
            option_answer = self._answer_option(normalized, options, normalized_options)
            if option_answer.should_answer:
                return option_answer
            return self._skip("Opciones visibles sin regla confiable")

        if boolean_like:
            return self._skip("Pregunta si/no sin regla confiable")

        numeric_answer = self._answer_numeric(normalized)
        if numeric_answer.should_answer:
            return numeric_answer

        text_answer = self._answer_text(normalized)
        if text_answer.should_answer:
            return text_answer

        return self._skip("Sin regla confiable")

    def _answer_boolean(self, question: str, normalized_options: list[str]) -> AnswerDecision:
        if not self._looks_like_boolean_question(question, normalized_options):
            return self._skip("No es pregunta si/no")

        safe_booleans = self.profile.get("safe_booleans", {})
        availability = self.profile.get("availability", {})

        rules = [
            (("tratamiento de datos", "datos personales", "politica de privacidad", "autorizo"), safe_booleans.get("accept_data_processing"), "Autorizacion de datos"),
            (("vinculo", "parentesco", "conyuge", "consejo directivo", "familiar", "empleado de la compania"), safe_booleans.get("has_family_in_company"), "Vinculo familiar/laboral"),
            (("conflicto de interes", "inhabilidad", "sancionado", "investigacion disciplinaria"), safe_booleans.get("has_conflict_of_interest"), "Conflicto de interes"),
            (("antecedentes", "judicial", "penal", "criminal"), safe_booleans.get("has_criminal_record"), "Antecedentes"),
            (("discapacidad",), safe_booleans.get("has_disability"), "Discapacidad"),
            (("remoto", "teletrabajo", "trabajo remoto"), availability.get("remote"), "Disponibilidad remoto"),
            (("hibrido", "alternancia"), availability.get("hybrid"), "Disponibilidad hibrido"),
            (("presencial",), availability.get("onsite"), "Disponibilidad presencial"),
            (("traslad", "reubic", "mudarse", "cambio de residencia"), availability.get("relocation"), "Reubicacion"),
            (("viajar", "viajes"), availability.get("travel"), "Disponibilidad para viajar"),
            (("inmediata", "inmediatamente", "iniciar de inmediato"), availability.get("start_immediately"), "Disponibilidad inmediata"),
            (("estudiante", "estudiando actualmente"), safe_booleans.get("is_currently_student"), "Estado estudiante"),
            (("formacion", "estudios", "titulo", "graduado", "finalizada"), safe_booleans.get("education_completed"), "Formacion finalizada"),
        ]

        english_level = self._normalize(self.profile.get("languages", {}).get("english", ""))
        if "ingles" in question and self._has_any(question, ("b2", "c1", "c2", "avanzado", "fluido", "bilingue")):
            return AnswerDecision("No", 0.95, f"Ingles del perfil: {english_level or 'no especificado'}", True)

        if "certificacion" in question or "certificado" in question:
            has_certification = self._has_matching_certification(question)
            return AnswerDecision("Si" if has_certification else "No", 0.9, "Certificaciones del perfil", True)

        if self._has_any(question, ("formacion profesional en ingenieria", "profesional en ingenieria")):
            return AnswerDecision("No", 0.85, "No hay titulo profesional de ingenieria en perfil", True)

        tech_answer = self._answer_technology_boolean(question)
        if tech_answer.should_answer:
            return tech_answer

        for patterns, value, reason in rules:
            if value is not None and self._has_any(question, patterns):
                return AnswerDecision("Si" if value else "No", 0.95, reason, True)

        return self._skip("Pregunta si/no no mapeada")

    def _answer_technology_boolean(self, question: str) -> AnswerDecision:
        if not self._has_any(question, ("experiencia", "conocimiento", "manejo", "dominio", "sabe", "trabajado", "desarrollado", "utilizando", "usando")):
            return self._skip("No pregunta tecnologia")

        years = self.profile.get("experience_years", {})
        skill_map = {
            "react": years.get("react"),
            "node": years.get("node"),
            "nodejs": years.get("node"),
            "javascript": years.get("javascript"),
            "typescript": years.get("javascript"),
            "angular": years.get("angular"),
            ".net": years.get("dotnet"),
            "net core": years.get("dotnet"),
            "c#": years.get("dotnet"),
            "c sharp": years.get("dotnet"),
            "microservicio": years.get("microservices"),
            "microservicios": years.get("microservices"),
            "liderazgo": years.get("leadership"),
            "liderando": years.get("leadership"),
            "python": years.get("python"),
            "sql": years.get("sql"),
            "power bi": years.get("power_bi"),
            "excel": years.get("excel"),
            "html": years.get("html"),
            "css": years.get("css"),
            "api": years.get("apis_rest"),
            "apis": years.get("apis_rest"),
            "full stack": years.get("full_stack"),
            "fullstack": years.get("full_stack"),
            "docker": years.get("docker"),
        }
        for keyword, value in skill_map.items():
            if keyword in question and value is not None:
                return AnswerDecision("Si" if value > 0 else "No", 0.9, f"Experiencia registrada en {keyword}: {value}", True)

        return self._skip("Tecnologia no registrada")

    def _answer_numeric(self, question: str) -> AnswerDecision:
        years = self.profile.get("experience_years", {})
        salary = self.profile.get("minimum_salary_cop")

        if self._has_any(
            question,
            (
                "aspiracion salarial",
                "expectativa salarial",
                "pretension salarial",
                "pretensiones salariales",
                "salario aspirado",
                "salario minimo",
                "compensacion esperada",
            ),
        ) and salary:
            return AnswerDecision(str(salary), 0.95, "Salario minimo del perfil", True)

        if re.search(r"\b(anos|años|tiempo|experiencia)\b", question):
            skill_map = {
                "react": years.get("react"),
                "node": years.get("node"),
                "nodejs": years.get("node"),
                "javascript": years.get("javascript"),
                "typescript": years.get("javascript"),
                "angular": years.get("angular"),
                ".net": years.get("dotnet"),
                "net core": years.get("dotnet"),
                "c#": years.get("dotnet"),
                "c sharp": years.get("dotnet"),
                "microservicio": years.get("microservices"),
                "microservicios": years.get("microservices"),
                "liderazgo": years.get("leadership"),
                "liderando": years.get("leadership"),
                "python": years.get("python"),
                "sql": years.get("sql"),
                "power bi": years.get("power_bi"),
                "excel": years.get("excel"),
                "html": years.get("html"),
                "css": years.get("css"),
                "api": years.get("apis_rest"),
                "apis": years.get("apis_rest"),
                "full stack": years.get("full_stack"),
                "fullstack": years.get("full_stack"),
                "docker": years.get("docker"),
            }
            for keyword, value in skill_map.items():
                if keyword in question and value is not None:
                    return AnswerDecision(str(value), 0.9, f"Experiencia en {keyword}", True)
            if years.get("total") is not None:
                return AnswerDecision(str(years["total"]), 0.75, "Experiencia total", True)

        return self._skip("No es numerica conocida")

    def _answer_option(self, question: str, options: list[str], normalized_options: list[str]) -> AnswerDecision:
        if not options:
            return self._skip("Sin opciones")

        if self._has_any(question, ("nivel de ingles", "ingles")):
            return self._match_option(options, normalized_options, ["a2", "basico", "basic"], "Nivel de ingles")

        if self._has_any(question, ("ciudad", "ubicacion", "residencia")):
            return self._match_option(options, normalized_options, ["bogota", "bogota d c", "colombia"], "Ubicacion")

        if self._has_any(question, ("modalidad",)):
            availability = self.profile.get("availability", {})
            preferred = []
            if availability.get("remote"):
                preferred.extend(["remoto", "teletrabajo"])
            if availability.get("hybrid"):
                preferred.append("hibrido")
            if availability.get("onsite"):
                preferred.append("presencial")
            return self._match_option(options, normalized_options, preferred, "Modalidad")

        skill_option = self._answer_skill_option(question, options, normalized_options)
        if skill_option.should_answer:
            return skill_option

        return self._skip("Opcion no mapeada")

    def _answer_skill_option(self, question: str, options: list[str], normalized_options: list[str]) -> AnswerDecision:
        years = self.profile.get("experience_years", {})
        skill_map = {
            "angular": years.get("angular"),
            ".net": years.get("dotnet"),
            "net core": years.get("dotnet"),
            "c#": years.get("dotnet"),
            "microservicio": years.get("microservices"),
            "microservicios": years.get("microservices"),
            "liderazgo": years.get("leadership"),
            "liderando": years.get("leadership"),
            "sql": years.get("sql"),
            "nosql": years.get("sql"),
            "react": years.get("react"),
            "python": years.get("python"),
            "javascript": years.get("javascript"),
        }
        for keyword, value in skill_map.items():
            if keyword not in question or value is None:
                continue

            if self._has_any(question, ("nivel", "dominio")):
                preferred = self._experience_level_preferences(value)
                level_match = self._match_option(options, normalized_options, preferred, f"Nivel registrado en {keyword}: {value}")
                if level_match.should_answer:
                    return level_match
                return self._skip(f"No hay opcion de nivel compatible para {keyword}")

            preferred = ("si", "tengo", "cuento") if value > 0 else ("no", "no tengo", "sin experiencia")
            avoided = ("no", "no tengo", "sin experiencia") if value > 0 else ("si", "tengo", "cuento")
            for option, normalized_option in zip(options, normalized_options):
                if any(word in normalized_option for word in preferred) and not any(word in normalized_option for word in avoided):
                    return AnswerDecision(option, 0.9, f"Opcion por experiencia registrada en {keyword}: {value}", True)

            return AnswerDecision("Si" if value > 0 else "No", 0.9, f"Experiencia registrada en {keyword}: {value}", True)

        return self._skip("No hay skill opcion mapeada")

    def _answer_text(self, question: str) -> AnswerDecision:
        texts = self.profile.get("short_texts", {})
        phone = self.profile.get("phone")
        city = self.profile.get("city")
        document_number = self.profile.get("document_number")
        email = self.profile.get("email")

        if self._has_any(question, ("telefono", "celular", "numero de contacto")) and phone:
            return AnswerDecision(str(phone), 0.98, "Telefono del perfil", True)

        if self._has_any(question, ("ciudad", "donde vives", "lugar de residencia", "residencia")) and city:
            return AnswerDecision(str(city), 0.95, "Ciudad del perfil", True)

        if self._has_any(question, ("correo", "email", "e-mail")) and email:
            return AnswerDecision(str(email), 0.98, "Email del perfil", True)

        if self._has_any(question, ("cedula", "documento", "identificacion")) and document_number:
            return AnswerDecision(str(document_number), 0.95, "Documento del perfil", True)

        if self._has_any(question, ("por que", "porque", "motivacion", "interesa")) and texts.get("motivation"):
            return AnswerDecision(texts["motivation"], 0.8, "Motivacion aprobada", True)

        if self._has_any(question, ("perfil", "resumen", "experiencia")) and texts.get("profile_summary"):
            return AnswerDecision(texts["profile_summary"], 0.8, "Resumen aprobado", True)

        if self._has_any(question, ("fortaleza", "habilidad", "competencia")) and texts.get("strengths"):
            return AnswerDecision(texts["strengths"], 0.8, "Fortalezas aprobadas", True)

        return self._skip("Texto no mapeado")

    def _match_option(
        self,
        options: list[str],
        normalized_options: list[str],
        preferred_values: list[str],
        reason: str,
    ) -> AnswerDecision:
        normalized_preferred = [self._normalize(value) for value in preferred_values]
        for wanted in normalized_preferred:
            for option, normalized_option in zip(options, normalized_options):
                if wanted == normalized_option or wanted in normalized_option:
                    return AnswerDecision(option, 0.9, reason, True)
        return self._skip(f"No hay opcion compatible: {reason}")

    def _match_boolean_option(
        self,
        options: list[str],
        normalized_options: list[str],
        value: str,
        reason: str,
    ) -> AnswerDecision:
        wanted = self._normalize(value)
        for option, normalized_option in zip(options, normalized_options):
            if re.search(rf"^{re.escape(wanted)}\b", normalized_option):
                return AnswerDecision(option, 0.9, reason, True)
        return self._skip(f"No hay opcion booleana compatible: {reason}")

    @staticmethod
    def _experience_level_preferences(years: int | float) -> list[str]:
        if years >= 3:
            return ["avanzado", "intermedio avanzado", "intermedio - avanzado", "alto", "experto"]
        if years > 0:
            return ["intermedio", "medio", "basico", "estoy aprendiendo"]
        return ["sin experiencia", "no tengo experiencia", "basico", "muy basico"]

    @staticmethod
    def _load_profile(profile_path: Path) -> dict[str, Any]:
        if not profile_path.exists():
            return {}
        return json.loads(profile_path.read_text(encoding="utf-8"))

    def _has_matching_certification(self, question: str) -> bool:
        certifications = [self._normalize(value) for value in self.profile.get("certifications", [])]
        cert_keywords = [word for word in re.findall(r"[a-z0-9#.+]+", question) if len(word) >= 3]
        ignored = {"certificacion", "certificado", "cuentas", "tienes", "con", "rol", "otras", "ejemplo"}
        relevant = [word for word in cert_keywords if word not in ignored]
        return any(all(word in certification for word in relevant[:3]) for certification in certifications) if relevant else False

    @staticmethod
    def _looks_like_option_text(text: str) -> bool:
        option_patterns = (
            r"^sin experiencia$",
            r"^no tengo experiencia",
            r"^si,? tengo experiencia",
            r"^si tengo experiencia",
        )
        return any(re.search(pattern, text) for pattern in option_patterns)

    @classmethod
    def _looks_like_noise_text(cls, text: str) -> bool:
        noise_patterns = (
            "crear cuenta",
            "magneto para:",
            "eres empresa",
            "descubre nuestras soluciones",
            "requisitos para aplicar",
            "cancelar enviar respuestas",
            "ofertas de empleo",
            "buscar por cargo",
            "buscar por ubicacion",
        )
        return cls._has_any(text, noise_patterns)

    @classmethod
    def _looks_like_boolean_question(cls, question: str, normalized_options: list[str]) -> bool:
        option_set = set(normalized_options)
        if {"si", "no"}.issubset(option_set):
            return True
        if any(option == "si" or option.startswith("si ") for option in option_set) and any(
            option == "no" or option.startswith("no ") for option in option_set
        ):
            return True

        if re.search(r"\bsi\b.*\bno\b|\bno\b.*\bsi\b", question):
            return True

        stripped = re.sub(r"^[^a-z0-9]+", "", question)
        boolean_starters = (
            "acepta",
            "aceptas",
            "autoriza",
            "autorizas",
            "certifica",
            "cuenta",
            "cuentas",
            "declara",
            "dispone",
            "dispones",
            "eres",
            "esta",
            "estas",
            "ha",
            "has",
            "posee",
            "puede",
            "puedes",
            "tiene",
            "tienes",
        )
        numeric_or_choice_words = ("anos", "cuanto", "cuanta", "cuantos", "cuantas", "cual", "nivel", "tiempo")
        return stripped.startswith(boolean_starters) and not cls._has_any(question, numeric_or_choice_words)

    @classmethod
    def _has_any(cls, text: str, patterns: Any) -> bool:
        return any(cls._normalize(str(pattern)) in text for pattern in patterns)

    @staticmethod
    def _normalize(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
        return re.sub(r"\s+", " ", normalized).strip().lower()

    @staticmethod
    def _skip(reason: str) -> AnswerDecision:
        return AnswerDecision(None, 0.0, reason, False)
