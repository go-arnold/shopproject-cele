"""
Core AI assistant orchestration service.

Used by two paths:
1. The live streaming chat endpoint (general.chat_stream) - calls
   build_prompt() + _retrieve_relevant_products()/_prepare_history() to
   prepare the prompt, then streams the reply itself via
   shop/services/gemini_stream.py (sync, see that module for why).
2. A post-stream Celery follow-up (tasks.post_stream_followup_task) - calls
   classify_reply() to get language/sentiment/complaint fields for the
   already-generated reply, and generate_support_email_async() if needed.
"""

import hashlib
import json
import logging
from typing import Optional

from asgiref.sync import sync_to_async
from django.core.cache import cache

from shop.services.gemini_async import get_async_gemini_client
from shop.services.config import get_ai_config
from shop.services.embedding_service import embed_query
from shop.selectors.product_search import semantic_search
from shop.view_components.assistant.catalog import format_product_full
from shop.view_components.assistant.constants import (
    SUPPORT_EMAIL_PROMPT,
    HISTORY_SUMMARY_PROMPT,
    INTENT_CLASSIFY_PROMPT,
    INTENT_RESPONSE_SCHEMA,
    EMAIL_RESPONSE_SCHEMA,
    MAX_PRODUCTS_FOCUS,
    HISTORY_SUMMARY_THRESHOLD,
    HISTORY_RECENT_MESSAGES,
)

logger = logging.getLogger(__name__)

HISTORY_SUMMARY_CACHE_PREFIX = "celebobo_history_summary_"


async def prepare_stream_context(
    message: str, history: list[dict], user_id: Optional[int], task_id: Optional[str]
) -> tuple[str, Optional[int]]:
    """
    Everything needed before streaming can start: RAG retrieval + history
    summarization, fused into the final prompt text. Called once via
    async_to_sync at the top of the streaming view, before any bytes are
    written to the response.

    Returns:
        (prompt, matched_product_id)
    """
    products = await _retrieve_relevant_products(message)
    products_ctx = await sync_to_async(_format_products_ctx)(products)
    matched_product_id = products[0].pk if products else None

    history_summary, recent_history = await _prepare_history(history, user_id, task_id)

    prompt = build_prompt(
        products_ctx=products_ctx,
        history_summary=history_summary,
        recent_history=recent_history,
        message=message,
    )
    return prompt, matched_product_id


async def classify_reply(
    message: str,
    reply: str,
    user_id: Optional[int] = None,
    task_id: Optional[str] = None,
) -> dict:
    """
    Classify an already-generated reply: language, sentiment, complaint
    fields. Runs AFTER the reply has been streamed to the user (see
    tasks.post_stream_followup_task) - never blocks the visible response.
    """
    config = get_ai_config()
    try:
        prompt = INTENT_CLASSIFY_PROMPT.format(message=message, reply=reply[:800])
        client = await get_async_gemini_client()
        response_data = await client.generate_content(
            model=config.gemini_model,
            prompt=prompt,
            temperature=0.1,
            max_tokens=200,
            response_schema=INTENT_RESPONSE_SCHEMA,
            user_id=user_id,
            task_id=task_id,
            event_name="classify_reply",
        )
        return _parse_json_response(response_data["text"])
    except Exception as e:
        logger.warning(f"[AssistantService] Reply classification failed: {e}")
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


def build_prompt(
    products_ctx: str,
    history_summary: str,
    recent_history: list[dict],
    message: str,
) -> str:
    """Build the user-turn prompt text (system prompt is sent separately as system_instruction)."""
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


def _parse_json_response(raw: str) -> dict:
    """Parse a schema-enforced JSON response defensively."""
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}
