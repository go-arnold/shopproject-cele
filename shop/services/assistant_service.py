"""
Core AI assistant orchestration service.

All AI operations are async-first. This service:
1. Retrieves relevant products via pgvector semantic search (RAG)
2. Calls Gemini with structured (schema-enforced) output
3. Summarizes older conversation history to keep prompts small and cheap
4. Handles support-email generation

Usage:
    from shop.services.assistant_service import process_user_message_async

    response = await process_user_message_async(
        message="Avez-vous des iPhones?",
        history=[...],
        user_id=42,
        task_id="task-uuid",
    )
"""

import hashlib
import json
import logging
from typing import Optional
from dataclasses import dataclass

from asgiref.sync import sync_to_async
from django.core.cache import cache

from shop.services.gemini_async import get_async_gemini_client
from shop.services.config import get_ai_config
from shop.services.embedding_service import embed_query
from shop.selectors.product_search import semantic_search
from shop.view_components.assistant.catalog import format_product_full
from shop.view_components.assistant.constants import (
    SYSTEM_PROMPT,
    SUPPORT_EMAIL_PROMPT,
    HISTORY_SUMMARY_PROMPT,
    FUSED_RESPONSE_SCHEMA,
    EMAIL_RESPONSE_SCHEMA,
    MAX_PRODUCTS_FOCUS,
    HISTORY_SUMMARY_THRESHOLD,
    HISTORY_RECENT_MESSAGES,
)

logger = logging.getLogger(__name__)

HISTORY_SUMMARY_CACHE_PREFIX = "celebobo_history_summary_"


@dataclass
class AssistantResponse:
    """
    Response from assistant processing.

    Attributes:
        text: Generated response text
        intent: Intent analysis results (language, sentiment, complaint fields)
        tokens_in: Input tokens used
        tokens_out: Output tokens generated
        latency_ms: Total latency
        language: Detected user language
        matched_product_id: Top RAG match, if any (for analytics tracking)
    """

    text: str
    intent: dict
    tokens_in: int
    tokens_out: int
    latency_ms: float
    language: str = "fr"
    matched_product_id: Optional[int] = None


async def process_user_message_async(
    message: str,
    history: list[dict],
    user_id: Optional[int] = None,
    task_id: Optional[str] = None,
) -> AssistantResponse:
    """
    Main entry point for processing user messages asynchronously.

    Pipeline:
    1. Embed the user's message and retrieve relevant products (pgvector RAG)
    2. Summarize older history if the conversation has grown long
    3. Call Gemini with the system prompt as system_instruction and a JSON
       response schema (no more regex-parsed free-text JSON)
    4. Return the reply + intent, never falling back to unparsed model output

    Args:
        message: User message to process
        history: Chat history (list of {role, text} dicts)
        user_id: Optional user ID for logging
        task_id: Optional Celery task ID for correlation

    Returns:
        AssistantResponse: Complete response with metrics
    """
    config = get_ai_config()

    logger.info(
        f"[AssistantService] Processing message from user {user_id}, "
        f"task {task_id}, message_len={len(message)}"
    )

    # Step 1: RAG retrieval — embed the query, find relevant products
    products = await _retrieve_relevant_products(message)
    products_ctx = await sync_to_async(_format_products_ctx)(products)
    matched_product_id = products[0].pk if products else None

    # Step 2: Summarize older history if the conversation has grown long
    history_summary, recent_history = await _prepare_history(
        history, user_id, task_id
    )

    # Step 3: Build prompt and call Gemini with structured output
    fused_prompt = _build_fused_prompt(
        products_ctx=products_ctx,
        history_summary=history_summary,
        recent_history=recent_history,
        message=message,
    )
    logger.debug(f"[AssistantService] Fused prompt built, len={len(fused_prompt)}")

    client = await get_async_gemini_client()
    response_data = await client.generate_content(
        model=config.gemini_model,
        prompt=fused_prompt,
        temperature=config.temperature,
        top_p=config.top_p,
        max_tokens=config.max_tokens,
        system_instruction=SYSTEM_PROMPT,
        response_schema=FUSED_RESPONSE_SCHEMA,
        user_id=user_id,
        task_id=task_id,
        event_name="process_user_message",
    )

    # Step 4: Parse structured response. Never show unparsed model text to the user.
    reply, intent_data = _parse_fused_response(response_data["text"])
    if not reply:
        reply = _error_message(intent_data.get("language", "fr"))
        logger.warning("[AssistantService] Could not parse structured reply, using error message")

    result = AssistantResponse(
        text=reply,
        intent=intent_data,
        tokens_in=response_data["tokens_in"],
        tokens_out=response_data["tokens_out"],
        latency_ms=response_data["latency_ms"],
        language=intent_data.get("language", "fr"),
        matched_product_id=matched_product_id,
    )

    logger.info(
        f"[AssistantService] Message processed successfully: "
        f"{result.tokens_in}→{result.tokens_out} tokens, "
        f"{result.latency_ms:.0f}ms latency"
    )

    return result


async def generate_support_email_async(
    complaint_type: str,
    client_message: str,
    complaint_summary: str,
    user_id: Optional[int] = None,
    task_id: Optional[str] = None,
) -> dict:
    """
    Generate support email content asynchronously.

    Falls back to a static HTML template if Gemini generation fails, so a
    complaint never goes unnotified just because the model call errored.

    Returns:
        dict: Email data with "subject", "body_html", "priority" keys
    """
    config = get_ai_config()

    from shop.view_components.assistant.support import (
        COMPLAINT_LABELS,
        _fallback_email_template,
    )

    label = COMPLAINT_LABELS.get(complaint_type, complaint_type)

    try:
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
            response_schema=EMAIL_RESPONSE_SCHEMA,
            user_id=user_id,
            task_id=task_id,
            event_name="generate_support_email",
        )

        email_data = _parse_json_response(response_data["text"])
        if email_data:
            logger.debug("[AssistantService] Support email generated")
            return email_data

    except Exception as e:
        logger.warning(f"[AssistantService] Email generation failed: {e}")

    user = await _get_user(user_id)
    return _fallback_email_template(complaint_type, client_message, complaint_summary, user)


# ── Helpers ────────────────────────────────────────────────────────────────────


async def _get_user(user_id: Optional[int]):
    if not user_id:
        return None
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        return await sync_to_async(User.objects.get)(pk=user_id)
    except User.DoesNotExist:
        return None


def _format_products_ctx(products: list) -> str:
    """Sync: format_product_full touches the ORM (category FK, features, rating aggregate)."""
    if not products:
        return "Aucun produit du catalogue ne correspond clairement à cette question."
    return "\n\n".join(format_product_full(p) for p in products)


async def _retrieve_relevant_products(message: str) -> list:
    """Embed the query and fetch semantically relevant products. Never raises."""
    try:
        query_vector = await embed_query(message)
        return await sync_to_async(semantic_search)(
            query_vector, limit=MAX_PRODUCTS_FOCUS
        )
    except Exception as e:
        logger.warning(f"[AssistantService] Product retrieval failed: {e}")
        return []


async def _prepare_history(
    history: list[dict], user_id: Optional[int], task_id: Optional[str]
) -> tuple[str, list[dict]]:
    """
    Split history into an (optionally cached) summary of older turns plus the
    raw recent turns, so the prompt stays small once a conversation grows.
    """
    if len(history) <= HISTORY_SUMMARY_THRESHOLD:
        return "", history

    older = history[: -HISTORY_RECENT_MESSAGES]
    recent = history[-HISTORY_RECENT_MESSAGES:]
    summary = await _get_or_build_history_summary(older, user_id, task_id)
    return summary, recent


async def _get_or_build_history_summary(
    older: list[dict], user_id: Optional[int], task_id: Optional[str]
) -> str:
    history_text = "\n".join(
        f"{'Client' if m.get('role') == 'user' else 'Assistant'}: {m.get('text', '')}"
        for m in older
    )
    cache_key = HISTORY_SUMMARY_CACHE_PREFIX + hashlib.sha256(
        history_text.encode("utf-8")
    ).hexdigest()

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        config = get_ai_config()
        client = await get_async_gemini_client()
        response_data = await client.generate_content(
            model=config.gemini_model,
            prompt=HISTORY_SUMMARY_PROMPT.format(history_text=history_text),
            temperature=0.1,
            max_tokens=150,
            user_id=user_id,
            task_id=task_id,
            event_name="summarize_history",
        )
        summary = (response_data.get("text") or "").strip()
    except Exception as e:
        logger.warning(f"[AssistantService] History summarization failed: {e}")
        summary = ""

    cache.set(cache_key, summary, config.cache_timeout_seconds)
    return summary


def _build_fused_prompt(
    products_ctx: str,
    history_summary: str,
    recent_history: list[dict],
    message: str,
) -> str:
    """Build the complete fused prompt (system prompt is sent separately as system_instruction)."""
    history_text = "\n".join(
        f"{'Client' if m.get('role') == 'user' else 'Assistant'}: {m.get('text', '')}"
        for m in recent_history
    )

    summary_block = (
        f"RÉSUMÉ DE LA CONVERSATION PRÉCÉDENTE :\n{history_summary}\n\n"
        if history_summary
        else ""
    )

    return f"""─── CATALOGUE PRODUITS PERTINENT ───
{products_ctx}
─────────────────────────

{summary_block}HISTORIQUE RÉCENT :
{history_text}

MESSAGE CLIENT :
{message}
"""


def _parse_fused_response(raw: str) -> tuple[Optional[str], dict]:
    """
    Parse the schema-enforced JSON response. Returns (None, {}) on any failure
    so the caller falls back to a localized error message — never to raw
    unparsed model output.
    """
    try:
        data = json.loads(raw)
        reply = data.get("reply", "").strip()
        intent = data.get("intent", {})
        return (reply or None), intent
    except (json.JSONDecodeError, AttributeError, TypeError):
        logger.warning("[AssistantService] Failed to parse structured response")
        return None, {}


def _parse_json_response(raw: str) -> dict:
    """Parse a schema-enforced JSON response defensively."""
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


def _error_message(language: str = "fr") -> str:
    """Get error message in user's language."""
    messages = {
        "fr": "Désolé, une erreur technique est survenue. Réessayez ou appelez +250791449879.",
        "en": "Sorry, a technical issue occurred. Please try again or call +250791449879.",
        "sw": "Samahani, kuna tatizo la kiufundi. Tafadhali jaribu tena: +250791449879.",
    }
    return messages.get(language, messages["fr"])
