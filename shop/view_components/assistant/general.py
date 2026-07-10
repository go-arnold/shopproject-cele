# shop/view_components/assistant/general.py
"""
Django views for the Celebobo AI assistant.

Endpoints:
  GET  /assistant/          → Render chat page
  POST /assistant/message/  → Stream the reply live (text/plain chunks)

The reply streams directly in the HTTP response as Gemini generates it -
no more queue+poll. Side effects that CAN be deferred (chat log, analytics,
complaint/support email) are dispatched as fire-and-forget Celery tasks once
the stream finishes; see shop/view_components/assistant/tasks.py.
"""

import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from asgiref.sync import async_to_sync

from .constants import MAX_MESSAGE_LENGTH, MAX_STORED_HISTORY, SYSTEM_PROMPT
from .tasks import save_chat_log_task, post_stream_followup_task

logger = logging.getLogger(__name__)

# Maximum length for individual history message (security)
MAX_HISTORY_MSG_LENGTH = 600

FALLBACK_ERROR_MESSAGE = (
    "Désolé, une erreur technique est survenue. "
    "Réessayez ou appelez +250791449879."
)


@login_required
def chat_page(request):
    """
    Render the AI assistant chat page.

    GET /assistant/
    """
    return render(request, "shop/assistant.html")


@login_required
@require_POST
def chat_message(request):
    """
    Receive a user message and stream the assistant's reply back live.

    POST /assistant/message/
    Request body (JSON):
        {
            "message": "Avez-vous des iPhones?",
            "history": [
                {"role": "user", "text": "Bonjour"},
                {"role": "bot", "text": "Bonjour!"}
            ]
        }

    Response: text/plain, chunked - reply text streams in as it's generated.
    """
    user_id = request.user.pk if request.user.is_authenticated else None

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        logger.warning(f"[View] Invalid JSON from user {user_id}")
        return JsonResponse({"error": "Corps de requête invalide."}, status=400)

    user_message = body.get("message", "")
    if not isinstance(user_message, str):
        logger.warning(f"[View] Non-string message from user {user_id}")
        return JsonResponse({"error": "Message invalide."}, status=400)

    user_message = user_message.strip()
    if not user_message:
        logger.debug(f"[View] Empty message from user {user_id}")
        return JsonResponse({"error": "Message vide."}, status=400)

    if len(user_message) > MAX_MESSAGE_LENGTH:
        logger.warning(
            f"[View] Message too long ({len(user_message)} chars) from user {user_id}"
        )
        return JsonResponse(
            {"error": f"Message trop long ({MAX_MESSAGE_LENGTH} caractères max)."},
            status=400,
        )

    history = _sanitize_history(body.get("history", []))

    logger.info(
        f"[View] Streaming reply for user {user_id}, "
        f"message_len={len(user_message)}, history_len={len(history)}"
    )

    response = StreamingHttpResponse(
        _stream_reply(user_message, history, user_id),
        content_type="text/plain; charset=utf-8",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"  # discourage proxy buffering (e.g. nginx)
    return response


def _stream_reply(user_message: str, history: list[dict], user_id):
    """
    Generator: prepares the RAG/history context, then streams reply text
    chunks as Gemini generates them. Dispatches follow-up Celery tasks once
    the reply is complete. Deliberately synchronous (see gemini_stream.py's
    module docstring for why) - Django's StreamingHttpResponse under
    Gunicorn/WSGI iterates this directly.
    """
    from shop.services.assistant_service import prepare_stream_context
    from shop.services.gemini_stream import stream_reply
    from shop.services.config import get_ai_config

    config = get_ai_config()
    chunks: list[str] = []
    matched_product_id = None

    try:
        prompt, matched_product_id = async_to_sync(prepare_stream_context)(
            user_message, history, user_id, None
        )
        for chunk in stream_reply(
            api_key=config.gemini_api_key,
            model=config.gemini_model,
            prompt=prompt,
            system_instruction=SYSTEM_PROMPT,
            temperature=config.temperature,
            top_p=config.top_p,
            max_tokens=config.max_tokens,
            timeout=config.gemini_timeout,
        ):
            chunks.append(chunk)
            yield chunk

    except Exception as e:
        logger.error(f"[View] Streaming failed for user {user_id}: {e}", exc_info=True)
        if not chunks:
            yield FALLBACK_ERROR_MESSAGE

    finally:
        full_reply = "".join(chunks).strip()
        if full_reply:
            save_chat_log_task.delay(
                user_id=user_id, user_message=user_message, bot_reply=full_reply
            )
            post_stream_followup_task.delay(
                user_id=user_id,
                message=user_message,
                reply=full_reply,
                matched_product_id=matched_product_id,
            )


# ── Input Validation & Sanitization ────────────────────────────────────────────


def _sanitize_history(raw_history) -> list[dict]:
    """
    Validate and clean chat history from client.

    Protects against:
    - Injection attacks (truncates content)
    - Oversized history (limits to MAX_STORED_HISTORY)
    - Malformed data (strict type checking)

    Args:
        raw_history: Raw history list from client

    Returns:
        list[dict]: Sanitized history with {role, text}
    """
    if not isinstance(raw_history, list):
        return []

    sanitized = []

    # Limit to most recent N messages
    for item in raw_history[-MAX_STORED_HISTORY:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role", "")
        text = item.get("text", "")

        # Validate role
        if role not in ("user", "bot", "model"):
            continue

        # Validate text is string
        if not isinstance(text, str):
            continue

        # Truncate and validate
        text = text.strip()[:MAX_HISTORY_MSG_LENGTH]
        if not text:
            continue

        sanitized.append({"role": role, "text": text})

    logger.debug(f"[View] Sanitized history: {len(raw_history)} → {len(sanitized)}")
    return sanitized
