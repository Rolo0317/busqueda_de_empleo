import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from services.anios_tecnologia import anios_de, pregunta_por_algo_especifico, tecnologia_ajena
from services.criterio_situacional import elegir as elegir_por_criterio
from services.eleccion_opciones import EleccionDeOpciones
from services.respuestas_locales import RespuestasLocales
from services.zona import AREAS


@dataclass(frozen=True)
class AnswerDecision:
    value: str | None
    confidence: float
    reason: str
    should_answer: bool


class CandidateQuestionAnswerer:
    def __init__(self, profile_path: Path, ai_client: Any | None = None) -> None:
        self.profile = self._load_profile(profile_path)
        self.ai_client = ai_client
        # Respuestas deterministas desde el perfil: no dependen de cuota de IA.
        self.locales = RespuestasLocales(self.profile)
        self.opciones = EleccionDeOpciones(self.profile)

    def answer(self, question: str, options: list[str]) -> AnswerDecision:
        raw_question = re.sub(r"\s+", " ", question or "").strip()
        normalized = self._normalize(question)
        normalized_options = [self._normalize(option) for option in options]

        if self._looks_like_option_text(normalized) or self._looks_like_noise_text(normalized):
            return self._skip("Texto visible no parece pregunta")

        if self._has_any(normalized, self.profile.get("never_answer_keywords", [])):
            return self._answer_sensitive_question(options, normalized_options)

        # Donde vive y las escalas numericas se deciden antes que nada: son datos
        # exactos del perfil que los fallbacks contestaban mal ("No" a su propia
        # ciudad, o un parrafo donde pedian un numero del 1 al 5).
        residencia = self._answer_residence(normalized)
        if residencia.should_answer:
            if options and residencia.value:
                # Si/No se casa con opciones booleanas; la ciudad, con la opcion que la nombra.
                elegida = (self._match_boolean_option(options, normalized_options,
                                                      residencia.value, residencia.reason)
                           if residencia.value in ("Si", "No")
                           else self._match_option(options, normalized_options,
                                                   self._formas_ciudad(), residencia.reason))
                if elegida.should_answer:
                    return elegida
            return residencia

        # Condiciones que el perfil declara: se contestan antes que el "No"
        # conservador, que descartaba al candidato por cosas que si acepta.
        for regla in (self._answer_contract_terms, self._answer_immediate_start,
                      self._answer_work_mode, self._answer_offered_salary):
            condicion = regla(normalized)
            if not condicion.should_answer:
                continue
            if options:
                elegida = self._match_boolean_option(options, normalized_options,
                                                     condicion.value, condicion.reason)
                if elegida.should_answer:
                    return elegida
            return condicion

        escala = self.locales.responder(raw_question) if self._es_escala(normalized) else None
        if escala:
            return AnswerDecision(escala, 0.9, "Nivel en la escala pedida", True)

        boolean_like = self._looks_like_boolean_question(normalized, normalized_options)
        boolean_answer = self._answer_boolean(normalized, normalized_options)
        if boolean_answer.should_answer:
            if options and boolean_answer.value:
                option_answer = self._match_boolean_option(options, normalized_options, boolean_answer.value, boolean_answer.reason)
                if option_answer.should_answer:
                    return option_answer
            return boolean_answer

        # Las preguntas de criterio piden un enfoque, no un dato: si se dejan a la
        # regla de tecnologias, gana la opcion que nombra una herramienta conocida.
        criterio = elegir_por_criterio(raw_question, options)
        if criterio:
            return AnswerDecision(criterio[0], 0.85, criterio[1], True)

        # If the field is a finite choice, never fall through to free-text/numeric
        # answers. This prevents typing "5" into a Si/No style question.
        if options:
            option_answer = self._answer_option(normalized, options, normalized_options)
            if option_answer.should_answer:
                return option_answer
            return self._answer_option_fallback(normalized, options, normalized_options)

        if boolean_like:
            # Antes de contestar "No" a ciegas se mira si el perfil tiene el dato:
            # "¿Nivel de ingles?" parece si/no y en realidad pide una respuesta.
            local = self.locales.responder(raw_question)
            if local:
                return AnswerDecision(local, 0.85, "Dato del perfil pese a parecer si/no", True)
            return AnswerDecision("No", 0.45, "Fallback conservador para pregunta si/no sin dato exacto", True)

        numeric_answer = self._answer_numeric(normalized)
        if numeric_answer.should_answer:
            return numeric_answer

        text_answer = self._answer_text(raw_question, normalized)
        if text_answer.should_answer:
            return text_answer

        return self._fallback_text_answer()

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

        agentes = self._answer_agents_boolean(question)
        if agentes.should_answer:
            return agentes

        tech_answer = self._answer_technology_boolean(question)
        if tech_answer.should_answer:
            return tech_answer

        for patterns, value, reason in rules:
            if value is not None and self._has_any(question, patterns):
                return AnswerDecision("Si" if value else "No", 0.95, reason, True)

        return self._skip("Pregunta si/no no mapeada")

    # Preguntas que indagan donde vive el candidato, no si quiere trasladarse.
    MARCAS_RESIDENCIA = ("vives en", "vive en", "resides en", "reside en", "vives o",
                         "radicado en", "te encuentras en", "vives cerca", "vives actualmente")
    PATRON_ESCALA = re.compile(r"escala de\s*1\s*a\s*[0-9]+")

    @classmethod
    def _es_escala(cls, question: str) -> bool:
        return bool(cls.PATRON_ESCALA.search(question))

    def _answer_residence(self, question: str) -> AnswerDecision:
        """Responde si vive en la ciudad que menciona la pregunta.

        El fallback conservador contestaba "No" a "vives en Bogota?" siendo esa
        su ciudad: una sola palabra que lo descarta de la vacante de entrada.
        """
        if not self._has_any(question, self.MARCAS_RESIDENCIA):
            return self._skip("No pregunta por residencia")

        ciudad = self._normalize(self.profile.get("city", ""))
        partes = [p for p in re.split(r"[,\s]+", ciudad) if len(p) > 3]
        if not partes:
            return self._skip("Sin ciudad en el perfil")

        if any(parte in question for parte in partes):
            return AnswerDecision("Si", 0.95, f"Reside en {self.profile.get('city')}", True)

        # "¿En que ciudad vives?" no nombra ninguna: pide la ciudad, no un si/no.
        # Se contestaba "No" (3 de octubre).
        if not self._nombra_una_ciudad(question):
            return AnswerDecision(str(self.profile.get("city", "")), 0.95, "Ciudad del perfil", True)

        # Menciona otra ciudad: se dice la verdad, y donde si vive.
        return AnswerDecision("No", 0.9, f"Reside en {self.profile.get('city')}", True)

    @staticmethod
    def _nombra_una_ciudad(question: str) -> bool:
        return any(re.search(r"(?<![a-z])" + re.escape(lugar) + r"(?![a-z])", question)
                   for lugares in AREAS.values() for lugar in lugares)

    MARCAS_CONTRATO = ("contrato", "termino fijo", "obra o labor", "obra labor",
                       "temporal", "prestacion de servicios")
    MARCAS_ACEPTAR = ("aceptas", "acepta", "estas de acuerdo", "esta de acuerdo", "de acuerdo con",
                      "te interesa", "le interesa", "estarias dispuesto", "estaria dispuesto")

    MARCAS_INMEDIATA = ("ingreso inmediato", "disponibilidad inmediata", "incorporacion inmediata",
                        "inicio inmediato", "vinculacion inmediata", "ingresar de inmediato",
                        "start immediately", "immediate availability")

    def _answer_immediate_start(self, question: str) -> AnswerDecision:
        """"¿Disponibilidad de ingreso inmediato?" sale de availability.start_immediately.

        Caia en el "No" conservador teniendo disponibilidad inmediata (3 de octubre).
        """
        if not self._has_any(question, self.MARCAS_INMEDIATA):
            return self._skip("No pregunta por ingreso inmediato")
        disponible = self.profile.get("availability", {}).get("start_immediately")
        if disponible is None:
            return self._skip("El perfil no dice si puede ingresar de inmediato")
        return AnswerDecision("Si" if disponible else "No", 0.9,
                              "Disponibilidad de ingreso segun el perfil", True)

    MODALIDADES = (("hibrid", "hybrid"), ("presencial", "onsite"), ("remot", "remote"),
                   ("teletrabajo", "remote"), ("home office", "remote"))

    def _answer_work_mode(self, question: str) -> AnswerDecision:
        """"¿Esta de acuerdo con la modalidad hibrida?" sale de availability.

        Se contestaba "No" con hybrid = true en el perfil (3 de octubre).
        """
        if not self._has_any(question, self.MARCAS_ACEPTAR):
            return self._skip("No pide aceptar una modalidad")
        disponibilidad = self.profile.get("availability", {})
        nombradas = [clave for marca, clave in self.MODALIDADES if marca in question]
        if not nombradas:
            return self._skip("No nombra una modalidad")
        acepta = all(disponibilidad.get(clave, False) for clave in nombradas)
        return AnswerDecision("Si" if acepta else "No", 0.9,
                              f"Modalidad segun el perfil: {', '.join(nombradas)}", True)

    MARCAS_SALARIO_OFRECIDO = ("asignacion economica", "salario ofrecido", "salario definido",
                               "rango salarial", "propuesta salarial", "remuneracion ofrecida",
                               "salario de", "salario es de", "compensacion ofrecida")

    def _answer_offered_salary(self, question: str) -> AnswerDecision:
        """"¿Esta de acuerdo con la asignacion economica definida?" -> Si.

        Es aceptar una condicion para seguir en el proceso, no afirmar un hecho;
        el monto se negocia despues. Quien no quiera aceptar a ciegas lo declara
        en availability.accept_offered_salary = false.
        """
        if not (self._has_any(question, self.MARCAS_SALARIO_OFRECIDO)
                and self._has_any(question, self.MARCAS_ACEPTAR)):
            return self._skip("No pide aceptar el salario ofrecido")
        acepta = self.profile.get("availability", {}).get("accept_offered_salary", True)
        return AnswerDecision("Si" if acepta else "No", 0.8,
                              "Acepta el salario ofrecido segun el perfil", True)

    def _answer_contract_terms(self, question: str) -> AnswerDecision:
        """"¿Aceptas un contrato fijo a 6 meses?" se responde con el perfil.

        Sin esta regla caia en el "No" conservador y descartaba al candidato por
        una condicion que si acepta (3 de octubre). Quien no acepte contratos
        temporales lo declara en availability.fixed_term_contract = false.
        """
        if not (self._has_any(question, self.MARCAS_CONTRATO)
                and self._has_any(question, self.MARCAS_ACEPTAR)):
            return self._skip("No pregunta por condiciones de contrato")
        acepta = self.profile.get("availability", {}).get("fixed_term_contract", True)
        return AnswerDecision("Si" if acepta else "No", 0.85,
                              "Condiciones de contrato segun el perfil", True)

    def _answer_agents_boolean(self, question: str) -> AnswerDecision:
        """Preguntas si/no sobre agentes de IA, RPA y automatizacion.

        El fallback conservador contestaba "No" a haber puesto controles en un
        sistema agentico, cuando el perfil registra un agente RPA en produccion
        con validacion, registro de corridas y aprobacion humana.
        """
        if not self.locales._es_agentes_ia(question):
            return self._skip("No pregunta por agentes ni automatizacion")

        anios = self.profile.get("experience_years", {})
        respaldo = max(anios.get("rpa", 0) or 0, anios.get("generative_ai", 0) or 0)
        if respaldo <= 0:
            return self._skip("Sin experiencia registrada en agentes")

        return AnswerDecision("Si", 0.9, "Agente RPA en produccion registrado en el perfil", True)

    def _answer_technology_boolean(self, question: str) -> AnswerDecision:
        if not self._has_any(question, ("experiencia", "conocimiento", "manejo", "dominio", "sabe", "trabajado", "desarrollado", "utilizando", "usando")):
            return self._skip("No pregunta tecnologia")

        mencion = anios_de(question, self.profile)
        if mencion is not None:
            keyword, value = mencion
            return AnswerDecision("Si" if self._cumple(question, value) else "No", 0.9,
                                  f"Experiencia registrada en {keyword}: {value:g}", True)

        return self._skip("Tecnologia no registrada")

    NUMEROS_EN_LETRAS = {"un": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
                         "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10}
    PATRON_MINIMO = re.compile(
        r"(minimo|al menos|mas de|mayor a|superior a|at least|more than)\s+"
        r"(\d+|un|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez)\s*(\+)?\s*"
        r"(anos|ano|years|year)"
        r"|(\d+)\s*(\+|o mas)?\s*(anos|years)\s*(o mas|or more|\+)?"
    )

    @classmethod
    def _anios_exigidos(cls, question: str) -> tuple[float, bool] | None:
        """El minimo de anos que pide la pregunta y si es estricto ("mas de 3").

        Sin esto, "al menos 8 anos?" se contestaba "Si" con 6 registrados: una
        afirmacion falsa que se cae en la primera entrevista.
        """
        texto = cls._normalize(question)
        texto = texto.replace("años", "anos")
        coincidencia = cls.PATRON_MINIMO.search(texto)
        if not coincidencia:
            return None
        if coincidencia.group(2):
            numero = coincidencia.group(2)
            cantidad = float(cls.NUMEROS_EN_LETRAS.get(numero, numero) if not numero.isdigit() else numero)
            estricto = coincidencia.group(1) in ("mas de", "mayor a", "superior a", "more than")
            return cantidad, estricto
        return float(coincidencia.group(5)), False

    @classmethod
    def _cumple(cls, question: str, anios: float) -> bool:
        """Si los anos registrados alcanzan lo que pide la pregunta."""
        exigido = cls._anios_exigidos(question)
        if exigido is None:
            return anios > 0
        minimo, estricto = exigido
        return anios > minimo if estricto else anios >= minimo

    # Verbos con los que la oferta pide que se explaye, no que cuantifique.
    PIDEN_RELATO = ("cuentanos", "cuentenos", "describe", "descripcion", "brevemente",
                    "explica", "explique", "detalla", "detalle", "comenta", "menciona los",
                    "que lenguajes", "cuales lenguajes", "tell us", "describe your")

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

        if self._has_any(question, ("edad",)):
            age = self._age_from_birth_date()
            if age is not None:
                return AnswerDecision(str(age), 0.95, "Edad calculada desde fecha de nacimiento", True)

        # "Cuentanos brevemente tu experiencia y los lenguajes que manejas" pide
        # un relato, no una cifra: contestar "6" desperdicia la pregunta.
        if self._has_any(question, self.PIDEN_RELATO):
            return self._skip("Pide una descripcion, no un numero")

        # Solo cuando preguntan una cantidad. Con la sola palabra "experiencia",
        # "¿Que experiencia tiene con CI/CD?" se contestaba "6".
        if re.search(r"\b(anos|años|tiempo)\b", question) or "cuanta experiencia" in question:
            mencion = anios_de(question, self.profile)
            if mencion is not None:
                keyword, value = mencion
                return AnswerDecision(f"{value:g}", 0.9, f"Experiencia en {keyword}", True)
            # Antes caia a los anos totales con cualquier tecnologia: "¿cuantos
            # anos tienes en Java?" se contestaba "6" sin haber usado Java (09/10).
            ajena = tecnologia_ajena(question)
            if ajena:
                return AnswerDecision("0", 0.85, f"El perfil no registra {ajena}", True)
            if pregunta_por_algo_especifico(question):
                return self._skip("Piden anos en algo que el perfil no registra")
            if years.get("total") is not None:
                return AnswerDecision(str(years["total"]), 0.75, "Experiencia total", True)

        return self._skip("No es numerica conocida")

    def _answer_option(self, question: str, options: list[str], normalized_options: list[str]) -> AnswerDecision:
        if not options:
            return self._skip("Sin opciones")

        # Las preguntas de vinculo laboral se resuelven contra el perfil antes que
        # nada: una afirmacion falsa de empleo cuesta mas que cualquier otro error.
        vinculo = self.opciones.elegir(question, options)
        if vinculo and "vinculo" in vinculo[1].lower():
            return AnswerDecision(vinculo[0], 0.9, vinculo[1], True)

        # En ingles la pregunta dice "english": sin esa palabra caia en "la primera
        # opcion visible" y respondia A1 teniendo A2.
        if self._has_any(question, ("nivel de ingles", "ingles", "english")):
            return self._match_option(options, normalized_options,
                                      [self._nivel_ingles(), "basico", "basic", "elementary"],
                                      "Nivel de ingles")

        if self._has_any(question, ("ciudad", "ubicacion", "residencia")):
            return self._match_option(options, normalized_options, self._formas_ciudad(), "Ubicacion")

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

        if self._has_any(question, ("nivel educativo", "formacion", "titulo", "estudios")):
            education_levels = [edu.get("degree", "").lower() for edu in self.profile.get("education", [])]
            if any("tecnico" in level for level in education_levels):
                return self._match_option(options, normalized_options, ["tecnico"], "Nivel educativo del perfil")
            elif any("tecnologo" in level for level in education_levels):
                return self._match_option(options, normalized_options, ["tecnologo"], "Nivel educativo del perfil")
            elif any("profesional" in level or "ingeniero" in level or "licenciado" in level for level in education_levels):
                return self._match_option(options, normalized_options, ["profesional"], "Nivel educativo del perfil")

        skill_option = self._answer_skill_option(question, options, normalized_options)
        if skill_option.should_answer:
            return skill_option

        return self._skip("Opcion no mapeada")

    def _answer_skill_option(self, question: str, options: list[str], normalized_options: list[str]) -> AnswerDecision:
        # El perfil manda: elegir por nivel evita respuestas como "solo backend"
        # o "sin experiencia" cuando el perfil registra anos en esa tecnologia.
        por_perfil = self.opciones.elegir(question, options)
        # Nivel o rango de anos respaldado por el perfil: esa eleccion manda.
        if por_perfil and any(k in por_perfil[1].lower() for k in ("nivel", "rango")):
            return AnswerDecision(por_perfil[0], 0.9, por_perfil[1], True)

        mencion = anios_de(question, self.profile)
        if mencion is not None:
            keyword, value = mencion

            if self._has_any(question, ("nivel", "dominio")):
                preferred = self._experience_level_preferences(value)
                level_match = self._match_option(options, normalized_options, preferred, f"Nivel registrado en {keyword}: {value}")
                if level_match.should_answer:
                    return level_match
                return self._skip(f"No hay opcion de nivel compatible para {keyword}")

            cumple = self._cumple(question, value)
            preferred = ("si", "tengo", "cuento") if cumple else ("no", "no tengo", "sin experiencia")
            avoided = ("no", "no tengo", "sin experiencia") if cumple else ("si", "tengo", "cuento")
            for option, normalized_option in zip(options, normalized_options):
                if any(word in normalized_option for word in preferred) and not any(word in normalized_option for word in avoided):
                    return AnswerDecision(option, 0.9, f"Opcion por experiencia registrada en {keyword}: {value}", True)

            # Las opciones pueden ser frases y no etiquetas: "Si" no coincidiria
            # con ninguna y la pregunta quedaria sin responder.
            por_alcance = self.opciones.elegir_por_afirmacion(question, options)
            if por_alcance:
                return AnswerDecision(por_alcance[0], 0.88, por_alcance[1], True)

            return AnswerDecision("Si" if cumple else "No", 0.9, f"Experiencia registrada en {keyword}: {value}", True)

        return self._skip("No hay skill opcion mapeada")

    def _answer_text(self, raw_question: str, question: str) -> AnswerDecision:
        texts = self.profile.get("short_texts", {})
        phone = self.profile.get("phone")
        city = self.profile.get("city")
        document_number = self.profile.get("document_number")
        email = self.profile.get("email")
        birth_date = self.profile.get("birth_date")
        linkedin = self.profile.get("linkedin")

        # "Whatsapp" es la forma mas comun de pedir el celular en estas ofertas,
        # y sin ella la pregunta caia en el resumen de experiencia.
        pide_telefono = self._has_any(question, (
            "telefono", "celular", "numero de contacto", "whatsapp", "wpp", "wasap",
            "numero movil",
            # "Dejar linea de contacto" caia en la regla de motivacion por
            # la palabra "interesad@".
            "linea de contacto", "dejar linea", "datos de contacto", "medio de contacto"))
        pide_correo = self._has_any(question, ("correo", "email", "e-mail"))

        # Muchas ofertas piden ambos en un mismo campo; dar solo uno deja a la
        # empresa sin la via de contacto que iba a usar.
        if pide_telefono and pide_correo and phone and email:
            return AnswerDecision(f"{phone} / {email}", 0.98, "Contacto del perfil", True)

        if pide_telefono and phone:
            return AnswerDecision(str(phone), 0.98, "Telefono del perfil", True)

        if self._has_any(question, ("ciudad", "donde vives", "lugar de residencia", "residencia")) and city:
            return AnswerDecision(str(city), 0.95, "Ciudad del perfil", True)

        if self._has_any(question, ("correo", "email", "e-mail")) and email:
            return AnswerDecision(str(email), 0.98, "Email del perfil", True)

        if self._has_any(question, ("cedula", "documento", "identificacion")) and document_number:
            return AnswerDecision(str(document_number), 0.95, "Documento del perfil", True)

        if self._has_any(question, ("fecha de nacimiento", "nacimiento")) and birth_date:
            return AnswerDecision(str(birth_date), 0.95, "Fecha de nacimiento del perfil", True)

        if self._has_any(question, ("linkedin", "linked in")) and linkedin:
            return AnswerDecision(str(linkedin), 0.95, "LinkedIn del perfil", True)

        if self._has_any(question, ("por que", "porque", "motivacion", "interesa")) and texts.get("motivation"):
            return AnswerDecision(texts["motivation"], 0.8, "Motivacion aprobada", True)

        # Las respuestas especificas del perfil van antes que el resumen: la regla
        # del resumen se activa con la palabra "experiencia", que aparece en casi
        # todas las preguntas, y tapaba el pipeline, las tecnologias, el ETL...
        local = self.locales.responder(raw_question)
        if local:
            return AnswerDecision(local, 0.85, "Respuesta construida desde el perfil", True)

        if self._has_any(question, ("perfil", "resumen", "experiencia")) and texts.get("profile_summary"):
            return AnswerDecision(texts["profile_summary"], 0.8, "Resumen aprobado", True)

        if self._has_any(question, ("fortaleza", "habilidad", "competencia")) and texts.get("strengths"):
            return AnswerDecision(texts["strengths"], 0.8, "Fortalezas aprobadas", True)

        if self.ai_client:
            answer = self.ai_client.answer_open_question(raw_question, self.profile)
            if answer:
                return AnswerDecision(answer, 0.72, "Respuesta abierta generada por IA gratuita", True)

        return self._fallback_text_answer()

    def _answer_sensitive_question(self, options: list[str], normalized_options: list[str]) -> AnswerDecision:
        if options:
            answer = self._match_option(
                options,
                normalized_options,
                ["prefiero no responder", "no aplica", "ninguna", "ninguno", "no"],
                "Pregunta sensible sin dato exacto",
            )
            if answer.should_answer:
                return answer
        return AnswerDecision("No especificado", 0.45, "Pregunta sensible sin dato exacto en perfil", True)

    @classmethod
    def _pide_tiempo_de_experiencia(cls, question: str) -> bool:
        return cls._has_any(question, ("cuanto tiempo", "cuantos anos", "cuantos años",
                                       "anos de experiencia", "años de experiencia",
                                       "how many years", "years of experience"))

    def _answer_option_fallback(
        self,
        question: str,
        options: list[str],
        normalized_options: list[str],
    ) -> AnswerDecision:
        preferences: list[str] = []
        if self._has_any(question, ("salario", "aspiracion", "pretension", "compensacion")):
            preferences.extend(self._formas_salario() + ["negociable", "a convenir"])
        if self._has_any(question, ("ciudad", "ubicacion", "residencia")):
            preferences.extend(self._formas_ciudad())
        if self._has_any(question, ("ingles",)):
            preferences.extend([self._nivel_ingles(), "basico", "basic"])
        if self._has_any(question, ("modalidad",)):
            preferences.extend(["remoto", "hibrido", "presencial"])

        # Antes de cualquier heuristica ciega: que el perfil decida.
        # La lista de preferencias incluia "sin experiencia" y "si", y por eso
        # respondia que no sabia SQL teniendo seis anos, o afirmaba empleos falsos.
        elegida = self.opciones.elegir(question, options)
        if elegida:
            valor, motivo = elegida
            return AnswerDecision(valor, 0.88, motivo, True)

        # Piden cuantos anos en algo que el perfil no registra: cualquier opcion
        # ("1 ano", "Mas de 2") seria inventada. Mejor sin responder que mentir.
        if self._pide_tiempo_de_experiencia(question) and anios_de(question, self.profile) is None:
            return self._skip("Piden anos en una tecnologia que el perfil no registra")

        preferences.extend(["no aplica", "ninguna", "ninguno", "no"])
        answer = self._match_option(options, normalized_options, preferences, "Fallback de seleccion multiple")
        if answer.should_answer:
            return AnswerDecision(answer.value, 0.5, answer.reason, True)

        first_option = next((option for option in options if option and option.strip()), None)
        if first_option:
            return AnswerDecision(first_option, 0.35, "Fallback: primera opcion visible", True)
        return self._skip("Opciones vacias")

    def _fallback_text_answer(self) -> AnswerDecision:
        texts = self.profile.get("short_texts", {})
        fallback = texts.get("open_question_fallback") or texts.get("profile_summary")
        if fallback:
            return AnswerDecision(str(fallback), 0.55, "Fallback de texto basado en perfil", True)
        return AnswerDecision(
            "Cuento con disponibilidad inmediata y experiencia en desarrollo, analisis de datos y automatizacion para aportar valor al equipo.",
            0.45,
            "Fallback general basado en perfil",
            True,
        )

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

    def _age_from_birth_date(self) -> int | None:
        birth_date = self.profile.get("birth_date")
        if not birth_date:
            return None
        try:
            born = date.fromisoformat(str(birth_date))
        except ValueError:
            return None
        today = date.today()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    @staticmethod
    def _experience_level_preferences(years: int | float) -> list[str]:
        if years >= 3:
            return ["avanzado", "intermedio avanzado", "intermedio - avanzado", "alto", "experto"]
        if years > 0:
            return ["intermedio", "medio", "basico", "estoy aprendiendo"]
        return ["sin experiencia", "no tengo experiencia", "basico", "muy basico"]

    # ------------------------------------------------- datos del perfil para opciones

    def _formas_ciudad(self) -> list[str]:
        """La ciudad del perfil como suelen escribirla las opciones, de lo exacto al pais.

        "Bogota, D.C., Colombia" -> ["bogota d.c. colombia", "bogota", "colombia"].
        """
        ciudad = self._normalize(self.profile.get("city", ""))
        # Sin las partes cortas: "d.c." sola casaria con cualquier distrito.
        partes = [p.strip() for p in ciudad.split(",") if len(p.strip()) > 3]
        pais = self._normalize(self.profile.get("country", ""))
        formas = [ciudad.replace(",", " "), *partes, pais]
        return [f for f in dict.fromkeys(" ".join(f.split()) for f in formas) if f]

    def _formas_salario(self) -> list[str]:
        """La aspiracion del perfil en los formatos de numero que usan las opciones."""
        monto = int(self.profile.get("minimum_salary_cop", 0) or 0)
        if not monto:
            return []
        return [str(monto), f"{monto:,}".replace(",", "."), f"{monto:,}"]

    def _nivel_ingles(self) -> str:
        return self._normalize(self.profile.get("languages", {}).get("english", "")) or "basico"

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
