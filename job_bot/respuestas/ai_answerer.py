import json
import logging
import os
import re
from typing import Any
from urllib import error, request
from urllib.parse import quote

from config import Settings


class FreeAiAnswerClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def answer_open_question(self, question: str, profile: dict[str, Any]) -> str | None:
        providers = self._provider_order()
        if not providers:
            logging.info("No hay proveedor IA configurado; usando respuesta local")
            return None

        prompt = self._build_prompt(question, profile)
        for provider in providers:
            try:
                logging.info(f"Intentando responder con {provider.upper()}...")
                answer = self._call_provider(provider, prompt)
            except Exception as error_value:  # noqa: BLE001
                logging.warning(f"Fallo {provider.upper()}: {error_value}")
                continue

            cleaned = self._clean_answer(answer)
            if cleaned:
                logging.info(f"✅ Respuesta generada por {provider.upper()}")
                return cleaned

        logging.info("Todos los proveedores de IA fallaron; usando respuesta local")
        return None

    def _provider_order(self) -> list[str]:
        provider = self.settings.ats_ai_provider.strip().lower()
        providers = ["gemini", "groq"] if provider in {"", "auto"} else [provider]
        return [
            item
            for item in providers
            if (item == "gemini" and self.settings.gemini_api_key)
            or (item == "groq" and self.settings.groq_api_key)
        ]

    def _call_provider(self, provider: str, prompt: str) -> str | None:
        if provider == "gemini":
            return self._call_gemini(prompt)
        if provider == "groq":
            return self._call_groq(prompt)
        return None

    def _call_gemini(self, prompt: str) -> str | None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None

        model = quote(self.settings.gemini_model.strip(), safe="")
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            f"?key={api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 180,
            },
        }
        data = self._post_json(url, payload)
        candidates = data.get("candidates") or []
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        return "\n".join(str(part.get("text", "")).strip() for part in parts if part.get("text")).strip()

    def _call_groq(self, prompt: str) -> str | None:
        payload = {
            "model": self.settings.groq_model,
            "messages": [
                {
                    "role": "system",
                    "content": "Responde formularios de empleo en espanol, primera persona, maximo 3 oraciones y sin inventar datos.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 180,
        }
        headers = {"Authorization": f"Bearer {self.settings.groq_api_key}"}
        data = self._post_json("https://api.groq.com/openai/v1/chat/completions", payload, headers=headers)
        choices = data.get("choices") or []
        if not choices:
            return None
        return str(choices[0].get("message", {}).get("content", "")).strip()

    @staticmethod
    def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                **(headers or {}),
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=20) as response:  # noqa: S310
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as http_error:
            detail = http_error.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"HTTP {http_error.code}: {detail[:300]}") from http_error

    @staticmethod
    def _build_prompt(question: str, profile: dict[str, Any]) -> str:
        profile_json = json.dumps(profile, ensure_ascii=False, indent=2)
        return (
            f"Eres {profile.get('name', 'el candidato')}, {profile.get('title', 'profesional')} "
            f"con {profile.get('experience_years', {}).get('total', 0)} anos de experiencia. "
            "Responde esta pregunta de un formulario de empleo en maximo 3 oraciones, en espanol, "
            "en primera persona, de forma profesional y concisa, basandote solo en el perfil real.\n\n"
            f"Perfil real:\n{profile_json}\n\n"
            f"Pregunta exacta:\n{question}"
        )

    @staticmethod
    def _clean_answer(answer: str | None) -> str | None:
        if not answer:
            return None

        normalized = re.sub(r"\s+", " ", answer).strip().strip('"')
        sentences = re.split(r"(?<=[.!?])\s+", normalized)
        cleaned = " ".join(sentence for sentence in sentences[:3] if sentence).strip()
        return cleaned[:500] if cleaned else None
