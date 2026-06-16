"""
Core AI assistant orchestration service.

All AI operations are async-first. This service:
1. Orchestrates calls to Gemini API
2. Manages caching and context retrieval
3. Handles intent analysis, response generation, email generation
4. Provides structured, observable operations

Usage:
    from shop.services.assistant_service import process_user_message_async

    response = await process_user_message_async(
        message="Avez-vous des iPhones?",
        history=[...],
        user_id=42,
        task_id="task-uuid",
    )
"""

import json
import re
import logging
from typing import Optional
from dataclasses import dataclass

from shop.services.gemini_async import get_async_gemini_client
from shop.services.config import get_ai_config
from shop.services.ai_logger import ai_logger
from shop.view_components.assistant.constants import (
    SYSTEM_PROMPT,
    INTENT_ANALYSIS_PROMPT,
    SUPPORT_EMAIL_PROMPT,
)
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


@dataclass
class AssistantResponse:
    """
    Response from assistant processing.

    Attributes:
        text: Generated response text
        intent: Intent analysis results
        tokens_in: Input tokens used
        tokens_out: Output tokens generated
        latency_ms: Total latency
        language: Detected user language
    """

    text: str
    intent: dict
    tokens_in: int
    tokens_out: int
    latency_ms: float
    language: str = "fr"


async def process_user_message_async(
    message: str,
    history: list[dict],
    user_id: Optional[int] = None,
    task_id: Optional[str] = None,
) -> AssistantResponse:
    """
    Main entry point for processing user messages asynchronously.

    Pipeline:
    1. Extract keywords from message (pure Python, <10ms)
    2. Search catalog using keywords (async DB via sync_to_async)
    3. Build fused prompt (system + catalog + history + message)
    4. Call Gemini asynchronously
    5. Parse response and return metrics
    6. Track product question (async, fire-and-forget)

    Args:
        message: User message to process
        history: Chat history (list of {role, text} dicts)
        user_id: Optional user ID for logging
        task_id: Optional Celery task ID for correlation

    Returns:
        AssistantResponse: Complete response with metrics

    Raises:
        ValueError: If configuration is missing
        httpx.TimeoutException: If Gemini request times out
    """
    config = get_ai_config()

    try:
        logger.info(
            f"[AssistantService] Processing message from user {user_id}, "
            f"task {task_id}, message_len={len(message)}"
        )

        # Step 1: Extract keywords (pure Python, fast)
        keywords = _extract_keywords(message)
        logger.debug(f"[AssistantService] Extracted keywords: {keywords}")

        # Step 2: Fetch catalog context (async DB)
        from shop.view_components.assistant.catalog import (
            quick_search,
            get_compact_catalog,
        )

        if keywords:
            products_ctx = await sync_to_async(quick_search)(keywords, limit=5)
            logger.debug(f"[AssistantService] Found products by keyword search")
        else:
            products_ctx = await sync_to_async(get_compact_catalog)(limit=20)
            logger.debug(f"[AssistantService] Using compact catalog")

        # Step 3: Build fused prompt
        fused_prompt = _build_fused_prompt(
            system_prompt=SYSTEM_PROMPT,
            products_ctx=products_ctx,
            history=history,
            message=message,
            max_history=config.max_history_messages,
        )
        logger.debug(f"[AssistantService] Fused prompt built, len={len(fused_prompt)}")

        # Step 4: Call Gemini asynchronously
        client = await get_async_gemini_client()
        response_data = await client.generate_content(
            model=config.gemini_model,
            prompt=fused_prompt,
            temperature=config.temperature,
            top_p=config.top_p,
            max_tokens=config.max_tokens,
            user_id=user_id,
            task_id=task_id,
            event_name="process_user_message",
        )

        # Step 5: Parse response
        reply, intent_data = _parse_fused_response(response_data["text"])

        if not reply:
            reply = _error_message(intent_data.get("language", "fr"))
            logger.warning(f"[AssistantService] Empty reply, using error message")

        result = AssistantResponse(
            text=reply,
            intent=intent_data,
            tokens_in=response_data["tokens_in"],
            tokens_out=response_data["tokens_out"],
            latency_ms=response_data["latency_ms"],
            language=intent_data.get("language", "fr"),
        )

        logger.info(
            f"[AssistantService] Message processed successfully: "
            f"{result.tokens_in}→{result.tokens_out} tokens, "
            f"{result.latency_ms:.0f}ms latency"
        )

        # Step 6: Track product question asynchronously (fire-and-forget)
        # This runs without blocking the main response
        try:
            await sync_to_async(_track_product_question)(
                message=message,
                response=reply,
                user_id=user_id,
                keywords=keywords,
                intent=intent_data,
            )
        except Exception as e:
            logger.warning(f"[AssistantService] Failed to track question: {e}")

        return result

    except Exception as e:
        logger.error(
            f"[AssistantService] Error processing message: {e}", exc_info=True
        )
        raise


async def analyze_intent_async(
    message: str,
    history: list[dict],
    user_id: Optional[int] = None,
    task_id: Optional[str] = None,
) -> dict:
    """
    Analyze user intent asynchronously (lightweight call).

    Returns a dict with intent fields:
    - language: "fr" | "en" | "sw"
    - is_complaint: bool
    - complaint_type: str or None
    - sentiment: "positive" | "neutral" | "negative" | "frustrated"
    - needs_product_search: bool
    - search_terms: list[str]
    - etc.

    Args:
        message: User message to analyze
        history: Chat history
        user_id: Optional user ID for logging
        task_id: Optional Celery task ID

    Returns:
        dict: Intent analysis results
    """
    config = get_ai_config()

    try:
        history_summary = _build_history_summary(history)
        prompt = INTENT_ANALYSIS_PROMPT.format(
            message=message,
            history_summary=history_summary,
        )

        client = await get_async_gemini_client()
        response_data = await client.generate_content(
            model=config.gemini_model,
            prompt=prompt,
            temperature=0.1,
            top_p=0.95,
            max_tokens=300,
            user_id=user_id,
            task_id=task_id,
            event_name="analyze_intent",
        )

        intent = _parse_intent_response(response_data["text"])
        logger.debug(
            f"[AssistantService] Intent analyzed: {intent.get('language')}, "
            f"complaint={intent.get('is_complaint')}"
        )
        return intent

    except Exception as e:
        logger.warning(f"[AssistantService] Intent analysis failed: {e}")
        return {}


async def generate_support_email_async(
    complaint_type: str,
    client_message: str,
    complaint_summary: str,
    user_id: Optional[int] = None,
    task_id: Optional[str] = None,
) -> dict:
    """
    Generate support email content asynchronously.

    Args:
        complaint_type: Type of complaint
        client_message: Original client message
        complaint_summary: Summary of the issue
        user_id: Optional user ID
        task_id: Optional Celery task ID

    Returns:
        dict: Email data with "subject" and "body_html" keys
    """
    config = get_ai_config()

    try:
        from shop.view_components.assistant.support import COMPLAINT_LABELS

        label = COMPLAINT_LABELS.get(complaint_type, complaint_type)
        prompt = SUPPORT_EMAIL_PROMPT.format(
            complaint_type=label,
            client_message=client_message[:500],
            complaint_summary=complaint_summary,
        )

        client = await get_async_gemini_client()
        response_data = await client.generate_content(
            model=config.gemini_model,
            prompt=prompt,
            temperature=0.2,
            max_tokens=800,
            user_id=user_id,
            task_id=task_id,
            event_name="generate_support_email",
        )

        email_data = _parse_json_response(response_data["text"])
        logger.debug(f"[AssistantService] Support email generated")
        return email_data

    except Exception as e:
        logger.warning(f"[AssistantService] Email generation failed: {e}")
        return {}


# ── Helpers ────────────────────────────────────────────────────────────────────


def _extract_keywords(message: str) -> list[str]:
    """
    Extract product keywords from message (Python only, no AI call).

    Quickly identifies if message mentions products by checking for
    trigger words (prix, phone, téléphone, etc.).

    Args:
        message: User message

    Returns:
        list[str]: Extracted keywords, or empty list if not a product query
    """
    words = re.findall(r"\b\w{3,}\b", message.lower())

    product_triggers = {
        "prix",
        "price",
        "combien",
        "how much",
        "bei",
        "produit",
        "product",
        "téléphone",
        "phone",
        "samsung",
        "iphone",
        "ordinateur",
        "laptop",
        "casque",
        "écouteur",
        "montre",
        "watch",
        "tablette",
        "tablet",
        "disponible",
        "available",
        "stock",
    }

    # If no product trigger, return empty (not a product query)
    if not any(w in product_triggers for w in words):
        return []

    stop_words = {
        "le",
        "la",
        "les",
        "un",
        "une",
        "des",
        "du",
        "de",
        "et",
        "ou",
        "est",
        "the",
        "a",
        "an",
        "is",
        "are",
        "do",
        "what",
        "how",
    }

    return [w for w in words if w not in stop_words and len(w) >= 3]


def _build_fused_prompt(
    system_prompt: str,
    products_ctx: str,
    history: list[dict],
    message: str,
    max_history: int,
) -> str:
    """Build the complete fused prompt."""
    history_text = ""
    for msg in history[-max_history:]:
        role = "Client" if msg.get("role") == "user" else "Assistant"
        history_text += f"{role}: {msg.get('text', '')}\n"

    return f"""{system_prompt}

─── CATALOGUE PRODUITS ───
{products_ctx}
─────────────────────────

HISTORIQUE RÉCENT :
{history_text}

MESSAGE CLIENT :
{message}

INSTRUCTION INTERNE :
Réponds en JSON avec exactement cette structure :
{{
  "reply": "Ta réponse au client ici (texte complet, formaté pour le chat)",
  "intent": {{
    "language": "fr" | "en" | "sw",
    "sentiment": "positive" | "neutral" | "negative" | "frustrated"
  }}
}}

Retourne UNIQUEMENT ce JSON, aucun texte autour, aucun markdown.
"""


def _build_history_summary(history: list[dict]) -> str:
    """Build a short summary of recent history."""
    if not history:
        return "Aucun historique."
    recent = history[-4:]
    parts = []
    for msg in recent:
        role = "Client" if msg.get("role") == "user" else "Assistant"
        text = str(msg.get("text", ""))[:100]
        parts.append(f"{role}: {text}")
    return " | ".join(parts)


def _parse_fused_response(raw: str) -> tuple[str, dict]:
    """Parse fused JSON response (reply + intent)."""
    try:
        cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        if not cleaned.startswith("{"):
            cleaned = '{"reply": "' + cleaned

        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return data.get("reply", "").strip(), data.get("intent", {})
    except (json.JSONDecodeError, Exception):
        pass

    return raw.strip(), {}


def _parse_intent_response(raw: str) -> dict:
    """Parse intent-only JSON response."""
    try:
        cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, Exception):
        pass

    return {}


def _parse_json_response(raw: str) -> dict:
    """Parse any JSON response robustly."""
    try:
        cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, Exception):
        pass

    return {}


def _error_message(language: str = "fr") -> str:
    """Get error message in user's language."""
    messages = {
        "fr": "Désolé, une erreur technique est survenue. Réessayez ou appelez +250791449879.",
        "en": "Sorry, a technical issue occurred. Please try again or call +250791449879.",
        "sw": "Samahani, kuna tatizo la kiufundi. Tafadhali jaribu tena: +250791449879.",
    }
    return messages.get(language, messages["fr"])


def _track_product_question(
    message: str,
    response: str,
    user_id: Optional[int],
    keywords: list[str],
    intent: dict,
) -> None:
    """
    Track a product question in the database (sync, called via sync_to_async).
    
    This runs asynchronously and does not block the main response.
    Called after the response is returned to the user.
    
    Args:
        message: User's question
        response: Assistant's response
        user_id: User ID (if available)
        keywords: Extracted keywords
        intent: Intent analysis results
    """
    from shop.models import ProductQuestion
    from shop.view_components.assistant.catalog import get_product_by_keywords
    
    try:
        # Try to find the product being asked about
        product = None
        if keywords:
            product = get_product_by_keywords(keywords, limit=1)
            if isinstance(product, list) and product:
                product = product[0]
        
        # Store the question
        pq = ProductQuestion.objects.create(
            user_id=user_id,
            product=product,
            question_text=message,
            response_text=response,
            language=intent.get("language", "fr"),
            sentiment=intent.get("sentiment", "neutral"),
            keywords=keywords,
        )
        logger.debug(f"[AssistantService] Tracked product question: {pq.id}")
    except Exception as e:
        logger.warning(f"[AssistantService] Failed to track question: {e}")
