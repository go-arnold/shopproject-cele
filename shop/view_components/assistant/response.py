# shop/assistant/response.py
"""
Construction de la réponse Gemini finale.
Étape 2 du pipeline : prend l'intention + le contexte produits → génère la réponse.
"""

from google.genai import types

from .constants import (
    SYSTEM_PROMPT,
    MODEL_NAME,
    MAX_TOKENS,
    TEMPERATURE,
    TOP_P,
    MAX_HISTORY_MESSAGES,
)
from .intent import ClientIntent, get_gemini_client


# ── Messages de clarification multilingues ────────────────────────────────────
CLARIFICATION_MESSAGES = {
    "fr": (
        "Je voudrais vous aider à trouver le bon produit 😊\n"
        "Pouvez-vous préciser :\n"
        "- Le type de produit que vous recherchez ?\n"
        "- Votre budget approximatif ?\n"
        "- Une marque ou un modèle en tête ?"
    ),
    "en": (
        "I'd love to help you find the right product 😊\n"
        "Could you please tell me:\n"
        "- What type of product are you looking for?\n"
        "- Your approximate budget?\n"
        "- Any brand or model in mind?"
    ),
    "sw": (
        "Nakufurahi kukusaidia kupata bidhaa nzuri 😊\n"
        "Nisaidie kuelewa zaidi:\n"
        "- Unatafuta bidhaa ya aina gani hasa?\n"
        "- Bei yako ni ngapi approximativement?\n"
        "- Una brand au model unaopenda?"
    ),
}


def build_gemini_response(
    system_prompt: str,
    history: list[dict],
    user_message: str,
    intent: ClientIntent,
) -> str:
    """
    Construit la conversation et appelle Gemini pour générer la réponse.
    Retourne le texte de réponse ou un message d'erreur.
    """

    # Si clarification nécessaire et pas de termes exploitables → demander
    if intent.needs_clarification and not intent.search_terms:
        lang = intent.language if intent.language in CLARIFICATION_MESSAGES else "fr"
        return CLARIFICATION_MESSAGES[lang]

    try:
        client = get_gemini_client()
        conversation = _build_conversation(system_prompt, history, user_message)

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=conversation,
            config=types.GenerateContentConfig(
                temperature=TEMPERATURE,
                top_p=TOP_P,
                max_output_tokens=MAX_TOKENS,
            ),
        )

        reply = getattr(response, "text", None)
        if not reply or not reply.strip():
            return _error_message(intent.language, "empty_response")

        return reply.strip()

    except Exception as e:
        return _error_message(intent.language, "api_error")


# ── Helpers ────────────────────────────────────────────────────────────────────
def _build_conversation(
    system_prompt: str,
    history: list[dict],
    user_message: str,
) -> list[dict]:
    """
    Construit le tableau de messages pour l'API Gemini.
    Le prompt système est injecté comme premier échange user→model (pattern Gemini).
    """
    conversation = [
        {
            "role": "user",
            "parts": [{"text": system_prompt}],
        },
        {
            "role": "model",
            "parts": [{"text": "Compris. Je suis prêt à assister les clients de Celebobo Business."}],
        },
    ]

    # Historique limité aux N derniers messages
    for msg in history[-MAX_HISTORY_MESSAGES:]:
        role = "user" if msg.get("role") == "user" else "model"
        text = str(msg.get("text", "")).strip()
        if text:
            conversation.append({"role": role, "parts": [{"text": text}]})

    # Message courant
    conversation.append({"role": "user", "parts": [{"text": user_message}]})
    return conversation


def _error_message(language: str, error_type: str) -> str:
    """Retourne un message d'erreur dans la langue du client."""
    messages = {
        "fr": "Désolé, je rencontre une difficulté technique. Veuillez réessayer ou contacter Celebobo au +250791449879.",
        "en": "Sorry, I'm having a technical issue. Please try again or contact Celebobo at +250791449879.",
        "sw": "Samahani, kuna tatizo la kiufundi. Tafadhali jaribu tena au wasiliana na Celebobo: +250791449879.",
    }
    lang = language if language in messages else "fr"
    return messages[lang]