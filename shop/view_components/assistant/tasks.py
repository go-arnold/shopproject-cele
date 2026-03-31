# shop/assistant/tasks.py
"""
Tâche Celery principale — pipeline OPTIMISÉ pour la vitesse.

OPTIMISATIONS vs version précédente :
─────────────────────────────────────
1. FUSION EN 1 SEUL APPEL GEMINI
   - Avant : intent (appel 1) → response (appel 2) = 2× latence API
   - Maintenant : 1 prompt unique → JSON structuré + réponse en même temps
   - Gain attendu : -15 à -30 secondes

2. CATALOGUE INTELLIGENT (DB uniquement, pas Gemini)
   - Recherche rapide par mots-clés côté Python avant l'appel Gemini
   - Si message court / général → catalogue limité à 20 lignes compactes
   - Si produit détecté → recherche DB ciblée (< 5ms)

3. SUPPORT EMAIL ASYNCHRONE
   - Envoi email délégué à une sous-tâche Celery séparée
   - N'est plus dans le chemin critique de la réponse

4. CACHE RÉSULTAT IMMÉDIAT
   - Dès que Gemini répond → cache mis à jour sans attendre le log DB
"""

import json
import logging
import re
import threading

from celery import shared_task
from django.core.cache import cache

logger = logging.getLogger(__name__)

CACHE_KEY_PREFIX = "celebobo_chat_"
CACHE_TIMEOUT = 300  # 5 minutes


# ── Tâche principale ───────────────────────────────────────────────────────────
@shared_task(
    bind=True,
    max_retries=1,
    default_retry_delay=2,
    name="shop.assistant.tasks.process_chat_message",
    time_limit=45,       # Kill si > 45s (évite les workers bloqués)
    soft_time_limit=40,
)
def process_chat_message_task(
    self,
    task_id: str,
    user_id: int | None,
    message: str,
    history: list[dict],
) -> None:
    """1 appel Gemini → intent détecté + réponse générée simultanément."""
    cache_key = f"{CACHE_KEY_PREFIX}{task_id}"
    cache.set(cache_key, {"status": "processing"}, CACHE_TIMEOUT)

    try:
        from .constants import SYSTEM_PROMPT, MAX_PRODUCTS_FOCUS
        from .catalog import quick_search, get_compact_catalog

        # ── Étape 1 : Recherche DB rapide (Python pur, < 10ms) ────────────────
        # On détecte les mots-clés dans le message SANS appel Gemini
        search_terms = _extract_keywords(message)
        if search_terms:
            products_ctx = quick_search(search_terms, limit=MAX_PRODUCTS_FOCUS + 2)
        else:
            products_ctx = get_compact_catalog(limit=20)

        # ── Étape 2 : 1 SEUL appel Gemini (intent + réponse fusionnés) ────────
        result = _single_gemini_call(
            system_prompt=SYSTEM_PROMPT,
            products_ctx=products_ctx,
            history=history,
            message=message,
        )

        reply = result.get("reply", "")
        intent_data = result.get("intent", {})

        if not reply:
            reply = _error_message(message)

        # ── Étape 3 : Cache immédiat (AVANT les tâches secondaires) ───────────
        cache.set(
            cache_key,
            {
                "status": "done",
                "reply": reply,
                "support_sent": False,  # Mis à jour par la sous-tâche si plainte
                "intent": intent_data,
            },
            CACHE_TIMEOUT,
        )

        # ── Étape 4 : Tâches secondaires en arrière-plan (non-bloquantes) ─────
        # Support email → sous-tâche Celery séparée (ne bloque pas la réponse)
        if intent_data.get("is_complaint") and intent_data.get("complaint_type"):
            send_support_email_task.delay(
                task_id=task_id,
                cache_key=cache_key,
                complaint_type=intent_data["complaint_type"],
                complaint_summary=intent_data.get("complaint_summary", ""),
                client_message=message,
                user_id=user_id,
            )

        # Log DB en thread background (ne bloque pas)
        threading.Thread(
            target=_save_chat_log,
            args=(user_id, message, reply),
            daemon=True,
        ).start()

    except Exception as exc:
        logger.error(f"[Task] failed: {exc}", exc_info=True)
        try:
            self.retry(exc=exc)
        except Exception:
            cache.set(
                cache_key,
                {"status": "error", "reply": _error_message(message)},
                CACHE_TIMEOUT,
            )


# ── Tâche support email (séparée, non-bloquante) ──────────────────────────────
@shared_task(name="shop.assistant.tasks.send_support_email", ignore_result=True)
def send_support_email_task(
    task_id: str,
    cache_key: str,
    complaint_type: str,
    complaint_summary: str,
    client_message: str,
    user_id: int | None,
) -> None:
    """Envoie l'email de support APRÈS que la réponse soit déjà en cache."""
    try:
        from .support import send_support_alert
        user = _get_user(user_id)
        sent = send_support_alert(
            complaint_type=complaint_type,
            client_message=client_message,
            complaint_summary=complaint_summary,
            user=user,
        )
        if sent:
            # Mettre à jour le flag dans le cache
            current = cache.get(cache_key) or {}
            current["support_sent"] = True
            cache.set(cache_key, current, CACHE_TIMEOUT)
    except Exception as e:
        logger.warning(f"[SupportTask] Email failed: {e}")


def get_task_result(task_id: str) -> dict | None:
    """Récupère le résultat d'une tâche depuis le cache."""
    return cache.get(f"{CACHE_KEY_PREFIX}{task_id}")


# ── Appel Gemini fusionné ──────────────────────────────────────────────────────
def _single_gemini_call(
    system_prompt: str,
    products_ctx: str,
    history: list[dict],
    message: str,
) -> dict:
    """
    Un seul appel Gemini qui :
    1. Détecte l'intention (complaint, language, sentiment)
    2. Génère la réponse client
    Retourne {"reply": str, "intent": dict}
    """
    from .intent import get_gemini_client
    from .constants import MODEL_NAME, MAX_TOKENS, TEMPERATURE, TOP_P, MAX_HISTORY_MESSAGES
    from google.genai import types

    FUSED_PROMPT = f"""{system_prompt}

─── CATALOGUE PRODUITS ───
{products_ctx}
─────────────────────────

INSTRUCTION INTERNE (invisible pour le client) :
Réponds en JSON avec exactement cette structure :
{{
  "reply": "Ta réponse au client ici (texte complet, formaté pour le chat)",
  "intent": {{
    "language": "fr" | "en" | "sw",
    "is_complaint": true | false,
    "complaint_type": "livraison" | "produit_defectueux" | "commande" | "paiement" | "plateforme" | "autre" | null,
    "complaint_summary": "résumé bref" | null,
    "sentiment": "positive" | "neutral" | "negative" | "frustrated"
  }}
}}

RÈGLES IMPÉRATIVES :
- "reply" = réponse complète au client, formatée avec des sauts de ligne si nécessaire.
- Retourne UNIQUEMENT ce JSON, aucun texte autour, aucun markdown.
- La réponse doit respecter toutes les règles du prompt système ci-dessus.
"""

    conversation = [
        {"role": "user", "parts": [{"text": FUSED_PROMPT}]},
        {"role": "model", "parts": [{"text": '{"reply": "'}]},  # Prefill → force le JSON
    ]

    # Historique (limité)
    for msg in history[-(MAX_HISTORY_MESSAGES):]:
        role = "user" if msg.get("role") == "user" else "model"
        text = str(msg.get("text", "")).strip()
        if text:
            conversation.insert(-1, {"role": role, "parts": [{"text": text}]})

    # Message courant
    conversation.insert(-1, {"role": "user", "parts": [{"text": message}]})

    client = get_gemini_client()
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=conversation,
        config=types.GenerateContentConfig(
            temperature=TEMPERATURE,
            top_p=TOP_P,
            max_output_tokens=MAX_TOKENS,
        ),
    )

    raw = getattr(response, "text", "") or ""
    return _parse_fused_response(raw)


def _parse_fused_response(raw: str) -> dict:
    """Parse le JSON fusionné retourné par Gemini. Robuste aux variations."""
    try:
        cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        # Gemini peut avoir commencé avec le prefill → compléter si besoin
        if not cleaned.startswith("{"):
            cleaned = '{"reply": "' + cleaned

        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return {
                "reply": str(data.get("reply", "")).strip(),
                "intent": data.get("intent", {}),
            }
    except (json.JSONDecodeError, Exception):
        pass

    # Fallback : si JSON cassé, utiliser le texte brut comme reply
    fallback_reply = re.sub(r'\{.*?"reply"\s*:\s*"', "", raw, flags=re.DOTALL)
    fallback_reply = re.sub(r'",?\s*"intent".*', "", fallback_reply, flags=re.DOTALL).strip()
    if not fallback_reply:
        fallback_reply = raw.strip()

    return {"reply": fallback_reply or "", "intent": {}}


# ── Extraction de mots-clés (Python pur, sans Gemini) ─────────────────────────
_STOP_WORDS = {
    "fr": {"le", "la", "les", "un", "une", "des", "du", "de", "et", "ou", "est",
            "je", "tu", "il", "vous", "nous", "on", "que", "qui", "quoi", "quel",
            "quelle", "comment", "combien", "avez", "avons", "avoir", "quel", "est",
            "ce", "pour", "avec", "sans", "dans", "sur", "par", "en", "au", "aux"},
    "en": {"the", "a", "an", "is", "are", "do", "does", "i", "you", "he", "she",
            "we", "they", "what", "how", "which", "have", "has", "can", "your"},
    "sw": {"na", "ya", "wa", "kwa", "ni", "si", "je", "la", "za"},
}
_ALL_STOPS = set().union(*_STOP_WORDS.values())

# Indicateurs qu'il s'agit d'une demande de produit
_PRODUCT_TRIGGERS = {
    "prix", "price", "combien", "how much", "bei", "produit", "product",
    "téléphone", "phone", "samsung", "iphone", "ordinateur", "laptop",
    "casque", "écouteur", "montre", "watch", "tablette", "tablet",
    "chargeur", "charger", "habit", "vêtement", "soulier", "chaussure",
    "disponible", "available", "stock", "vendre", "vente", "acheter", "buy",
}


def _extract_keywords(message: str) -> list[str]:
    """
    Extrait les mots-clés significatifs d'un message sans appel Gemini.
    Retourne une liste vide si le message n'est pas une demande produit.
    """
    words = re.findall(r"\b\w{3,}\b", message.lower())
    # Vérifier si c'est une demande produit
    if not any(w in _PRODUCT_TRIGGERS for w in words):
        return []
    # Filtrer les stop words
    return [w for w in words if w not in _ALL_STOPS and len(w) >= 3]


# ── Helpers ────────────────────────────────────────────────────────────────────
def _get_user(user_id: int | None):
    if not user_id:
        return None
    try:
        from django.contrib.auth import get_user_model
        return get_user_model().objects.get(pk=user_id)
    except Exception:
        return None


def _save_chat_log(user_id: int | None, user_message: str, bot_reply: str) -> None:
    try:
        from shop.models import ChatLog
        ChatLog.objects.create(
            user=_get_user(user_id),
            user_message=user_message,
            bot_reply=bot_reply,
        )
    except Exception as e:
        logger.warning(f"[Task] ChatLog save failed: {e}")


def _error_message(message: str = "") -> str:
    msg = message.lower()
    if any(w in msg for w in ["the", "what", "how", "can", "is ", "are "]):
        return "Sorry, a technical issue occurred. Please try again or call +250791449879."
    if any(w in msg for w in ["ninaweza", "nataka", "karibu", "sawa", "niko"]):
        return "Samahani, kuna tatizo la kiufundi. Tafadhali jaribu tena: +250791449879."
    return "Désolé, une erreur technique est survenue. Réessayez ou appelez le +250791449879."