"""
Analyse d'intention : détermine ce que veut le client avant de répondre.
Étape 1 du pipeline : rapide, peu de tokens, décision binaire.
"""

import json
import re
from dataclasses import dataclass, field
from google import genai
from google.genai import types
from django.conf import settings

from .constants import INTENT_ANALYSIS_PROMPT, MODEL_NAME


_gemini_client = None


def get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _gemini_client


@dataclass
class ClientIntent:
    needs_product_search: bool = False
    search_terms: list = field(default_factory=list)
    category_hint: str | None = None
    is_complaint: bool = False
    complaint_type: str | None = None
    complaint_summary: str | None = None
    needs_clarification: bool = False
    clarification_reason: str | None = None
    language: str = "fr"
    sentiment: str = "neutral"


def analyze_intent(message: str, history: list[dict]) -> ClientIntent:
    """
    Appelle Gemini avec un prompt minimaliste pour analyser l'intention.
    Retourne un ClientIntent. Ne lève jamais d'exception (fallback sur défaut).
    """
    try:
        history_summary = _build_history_summary(history)
        prompt = INTENT_ANALYSIS_PROMPT.format(
            message=message,
            history_summary=history_summary,
        )

        client = get_gemini_client()
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[{"role": "user", "parts": [{"text": prompt}]}],
            config=types.GenerateContentConfig(
                temperature=0.1,         
                max_output_tokens=300,
                top_p=0.95,
            ),
        )

        raw = getattr(response, "text", "") or ""
        return _parse_intent_response(raw)

    except Exception:
        # Fallback silencieux : intention neutre
        return ClientIntent()


def _build_history_summary(history: list[dict]) -> str:
    """Résume les 4 derniers échanges pour le contexte d'analyse."""
    if not history:
        return "Aucun historique."
    recent = history[-4:]
    parts = []
    for msg in recent:
        role = "Client" if msg.get("role") == "user" else "Assistant"
        text = str(msg.get("text", ""))[:100]
        parts.append(f"{role}: {text}")
    return " | ".join(parts)


def _parse_intent_response(raw: str) -> ClientIntent:
    """Parse le JSON retourné par Gemini, robuste aux variations de format."""
    try:
        cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()

        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            return ClientIntent()

        data = json.loads(match.group())

        return ClientIntent(
            needs_product_search=bool(data.get("needs_product_search", False)),
            search_terms=list(data.get("search_terms", [])),
            category_hint=data.get("category_hint"),
            is_complaint=bool(data.get("is_complaint", False)),
            complaint_type=data.get("complaint_type"),
            complaint_summary=data.get("complaint_summary"),
            needs_clarification=bool(data.get("needs_clarification", False)),
            clarification_reason=data.get("clarification_reason"),
            language=data.get("language", "fr"),
            sentiment=data.get("sentiment", "neutral"),
        )

    except (json.JSONDecodeError, Exception):
        return ClientIntent()