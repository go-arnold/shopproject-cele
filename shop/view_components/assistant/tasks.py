# shop/view_components/assistant/tasks.py
"""
Celery tasks for AI assistant message processing.

This module defines background tasks that:
1. Process user messages asynchronously (no blocking main thread)
2. Call Gemini API via async service
3. Cache results for fast polling
4. Handle support email dispatch
5. Log all operations with structured logging

Key tasks:
- process_chat_message_task: Main pipeline (message → response)
- send_support_email_task: Complaint handling (async, non-blocking)
- save_chat_log_task: Database logging (migrated from thread to Celery)

Design principles:
- Keep individual tasks fast (<30s typically)
- All I/O is delegated to async services
- Results cached immediately for client polling
- Secondary operations (emails, logs) don't block the response
"""

import logging
import asyncio
from celery import shared_task
from django.core.cache import cache
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

CACHE_KEY_PREFIX = "celebobo_chat_"
CACHE_TIMEOUT = 300  # 5 minutes


# ── Main chat message processing task ──────────────────────────────────────────
@shared_task(
    bind=True,
    max_retries=1,
    default_retry_delay=2,
    name="shop.assistant.tasks.process_chat_message",
    time_limit=45,  # Kill if > 45s (prevents stuck workers)
    soft_time_limit=40,
)
def process_chat_message_task(
    self,
    task_id: str,
    user_id: int | None,
    message: str,
    history: list[dict],
) -> None:
    """
    Process user message asynchronously using Gemini.

    Pipeline:
    1. Mark task as "processing" in cache
    2. Call async assistant service (fused intent + response)
    3. Cache result immediately
    4. Dispatch support email if complaint detected (non-blocking)
    5. Log conversation to DB (non-blocking)

    Args:
        task_id: Unique task ID for caching
        user_id: User ID or None
        message: User message text
        history: List of {role, text} dicts

    Returns:
        None (result cached for polling)
    """
    cache_key = f"{CACHE_KEY_PREFIX}{task_id}"

    # Mark task as processing
    cache.set(cache_key, {"status": "processing"}, CACHE_TIMEOUT)
    logger.info(f"[Task] {task_id} started: user={user_id}, msg_len={len(message)}")

    try:
        # Import async service
        from shop.services.assistant_service import process_user_message_async

        # Run async function in sync context (Celery context)
        response = async_to_sync(process_user_message_async)(
            message=message,
            history=history,
            user_id=user_id,
            task_id=task_id,
        )

        reply = response.text
        intent_data = response.intent
        latency_ms = response.latency_ms
        tokens_in = response.tokens_in
        tokens_out = response.tokens_out

        # Cache result immediately (BEFORE secondary tasks)
        # This enables fast client polling
        cache.set(
            cache_key,
            {
                "status": "done",
                "reply": reply,
                "support_sent": False,  # Updated by support task if complaint
                "intent": intent_data,
                "tokens": {"in": tokens_in, "out": tokens_out},
                "latency_ms": latency_ms,
            },
            CACHE_TIMEOUT,
        )

        logger.info(
            f"[Task] {task_id} cached: {tokens_in}→{tokens_out} tokens, "
            f"{latency_ms:.0f}ms, complaint={intent_data.get('is_complaint')}"
        )

        # Secondary operations (non-blocking)
        # Dispatch support email if complaint detected
        if intent_data.get("is_complaint") and intent_data.get("complaint_type"):
            send_support_email_task.delay(
                task_id=task_id,
                cache_key=cache_key,
                complaint_type=intent_data["complaint_type"],
                complaint_summary=intent_data.get("complaint_summary", ""),
                client_message=message,
                user_id=user_id,
            )
            logger.debug(f"[Task] {task_id} support email queued")

        # Log conversation to database (non-blocking)
        save_chat_log_task.delay(
            user_id=user_id,
            user_message=message,
            bot_reply=reply,
        )
        logger.debug(f"[Task] {task_id} chat log queued")

    except Exception as exc:
        logger.error(f"[Task] {task_id} failed: {exc}", exc_info=True)

        try:
            # Retry once on transient errors
            self.retry(exc=exc)
        except Exception:
            # If retry exhausted, cache error state
            cache.set(
                cache_key,
                {
                    "status": "error",
                    "reply": "Désolé, une erreur technique est survenue. "
                    "Réessayez ou appelez +250791449879.",
                },
                CACHE_TIMEOUT,
            )
            logger.error(f"[Task] {task_id} max retries exhausted")


# ── Support email dispatch task ────────────────────────────────────────────────
@shared_task(
    name="shop.assistant.tasks.send_support_email",
    ignore_result=True,
    max_retries=2,
    default_retry_delay=5,
    time_limit=30,
)
def send_support_email_task(
    task_id: str,
    cache_key: str,
    complaint_type: str,
    complaint_summary: str,
    client_message: str,
    user_id: int | None,
) -> None:
    """
    Generate and send support email asynchronously.

    This task runs independently and doesn't block the main response.
    Runs after the chat response is already cached.

    Args:
        task_id: Parent task ID
        cache_key: Cache key for status updates
        complaint_type: Type of complaint
        complaint_summary: Summary text
        client_message: Original message from client
        user_id: User ID or None

    Returns:
        None
    """
    logger.info(
        f"[SupportTask] {task_id} started: type={complaint_type}, user={user_id}"
    )

    try:
        from shop.view_components.assistant.support import (
            _get_mukubwa_emails,
            _send_email,
        )
        from shop.services.assistant_service import generate_support_email_async
        import asyncio

        # Get recipient emails
        mukubwa_emails = _get_mukubwa_emails()
        if not mukubwa_emails:
            logger.warning(f"[SupportTask] {task_id} no recipients in mukubwa group")
            return

        # Generate email content asynchronously
        email_data = async_to_sync(generate_support_email_async)(
            complaint_type=complaint_type,
            client_message=client_message,
            complaint_summary=complaint_summary,
            user_id=user_id,
            task_id=task_id,
        )

        if not email_data:
            logger.warning(f"[SupportTask] {task_id} email generation failed")
            return

        # Send email
        success = _send_email(email_data, mukubwa_emails, user_id)

        if success:
            # Update cache to indicate support email was sent
            current = cache.get(cache_key) or {}
            current["support_sent"] = True
            cache.set(cache_key, current, CACHE_TIMEOUT)
            logger.info(
                f"[SupportTask] {task_id} email sent to {len(mukubwa_emails)} recipients"
            )
        else:
            logger.error(f"[SupportTask] {task_id} email send failed")

    except Exception as e:
        logger.error(f"[SupportTask] {task_id} failed: {e}", exc_info=True)
        # Don't retry - this isn't critical path


# ── Chat log persistence task ─────────────────────────────────────────────────
@shared_task(
    name="shop.assistant.tasks.save_chat_log",
    ignore_result=True,
    max_retries=1,
    default_retry_delay=3,
    time_limit=15,
)
def save_chat_log_task(
    user_id: int | None,
    user_message: str,
    bot_reply: str,
) -> None:
    """
    Save chat conversation to database.

    Migrated from threading to Celery for:
    - Proper error handling
    - Retry logic
    - Monitoring and metrics
    - Non-blocking operation

    Args:
        user_id: User ID or None
        user_message: User's message
        bot_reply: Bot's response

    Returns:
        None
    """
    try:
        from shop.models import ChatLog
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = None

        if user_id:
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                logger.warning(f"[LogTask] User {user_id} not found")

        ChatLog.objects.create(
            user=user,
            user_message=user_message[:500],  # Truncate for storage
            bot_reply=bot_reply[:1000],  # Truncate for storage
        )

        logger.debug(f"[LogTask] Chat log saved for user {user_id}")

    except Exception as e:
        logger.warning(f"[LogTask] Failed to save chat log: {e}")
        # This failure is non-critical, log and continue


# ── Helper: Get cached task result ─────────────────────────────────────────────
def get_task_result(task_id: str) -> dict | None:
    """
    Retrieve task result from cache.

    Used by polling endpoint to fetch task status and result.

    Args:
        task_id: Task ID returned from chat_message endpoint

    Returns:
        dict with status and result, or None if not found
    """
    cache_key = f"{CACHE_KEY_PREFIX}{task_id}"
    return cache.get(cache_key)
