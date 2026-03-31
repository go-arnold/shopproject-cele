# shop/views_assistant.py
"""
Vues Django pour l'assistant conversationnel Celebobo.

Endpoints :
  GET  /assistant/          → page du chat
  POST /assistant/message/  → envoie un message, lance la tâche Celery
  GET  /assistant/poll/<id>/→ poll du résultat (long-polling léger)
"""

import json
import uuid
import html
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .tasks import process_chat_message_task, get_task_result
from .constants import MAX_MESSAGE_LENGTH, MAX_STORED_HISTORY

logger = logging.getLogger(__name__)

# Longueur max d'un message d'historique stocké (sécurité)
MAX_HISTORY_MSG_LENGTH = 600


@login_required
def chat_page(request):
    """Affiche la page du chat assistant."""
    return render(request, "shop/assistant.html")


@login_required
@require_POST
def chat_message(request):
    """
    Reçoit le message du client, valide, lance la tâche Celery.
    Retourne immédiatement un task_id pour que le client commence à poller.
    """
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Corps de requête invalide."}, status=400)

    # ── Validation du message ──────────────────────────────────────────────────
    user_message = body.get("message", "")
    if not isinstance(user_message, str):
        return JsonResponse({"error": "Message invalide."}, status=400)

    user_message = user_message.strip()

    if not user_message:
        return JsonResponse({"error": "Message vide."}, status=400)

    if len(user_message) > MAX_MESSAGE_LENGTH:
        return JsonResponse(
            {"error": f"Message trop long ({MAX_MESSAGE_LENGTH} caractères max)."},
            status=400,
        )

    # ── Sanitisation de l'historique ──────────────────────────────────────────
    raw_history = body.get("history", [])
    history = _sanitize_history(raw_history)

    # ── Lancement de la tâche Celery ──────────────────────────────────────────
    task_id = str(uuid.uuid4())

    try:
        process_chat_message_task.delay(
            task_id=task_id,
            user_id=request.user.pk if request.user.is_authenticated else None,
            message=user_message,
            history=history,
        )
    except Exception as e:
        logger.error(f"[View] Celery task dispatch failed: {e}")
        return JsonResponse(
            {"error": "Service temporairement indisponible. Veuillez réessayer."},
            status=503,
        )

    return JsonResponse({"task_id": task_id, "status": "queued"})


@login_required
def chat_poll(request, task_id: str):
    """
    Retourne l'état courant de la tâche.
    Statuts possibles : "processing" | "done" | "error" | "not_found"
    """
    if not task_id or len(task_id) > 64:
        return JsonResponse({"status": "not_found"}, status=404)

    result = get_task_result(task_id)

    if result is None:
        return JsonResponse({"status": "not_found"})

    return JsonResponse(result)


# ── Helpers ────────────────────────────────────────────────────────────────────
def _sanitize_history(raw_history) -> list[dict]:
    """
    Valide et nettoie l'historique reçu du client.
    Protège contre les injections et les historiques trop volumineux.
    """
    if not isinstance(raw_history, list):
        return []

    sanitized = []
    for item in raw_history[-MAX_STORED_HISTORY:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role", "")
        text = item.get("text", "")
        if role not in ("user", "bot", "model"):
            continue
        if not isinstance(text, str):
            continue
        text = text.strip()[:MAX_HISTORY_MSG_LENGTH]
        if not text:
            continue
        sanitized.append({"role": role, "text": text})

    return sanitized