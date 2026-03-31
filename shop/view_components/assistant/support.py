"""
Gestion des plaintes clients.
Génère et envoie un email HTML aux membres du groupe "mukubwa".
"""

import json
import re
import logging
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from google.genai import types

from .constants import SUPPORT_EMAIL_PROMPT, MODEL_NAME
from .intent import get_gemini_client

logger = logging.getLogger(__name__)

COMPLAINT_LABELS = {
    "livraison":          "Problème de livraison",
    "produit_defectueux": "Produit défectueux / non conforme",
    "commande":           "Problème de commande",
    "paiement":           "Problème de paiement",
    "plateforme":         "Problème sur la plateforme",
    "autre":              "Autre problème",
}

PRIORITY_COLORS = {
    "haute":   "#dc2626",
    "normale": "#d97706",
    "basse":   "#16a34a",
}


def send_support_alert(
    complaint_type: str,
    client_message: str,
    complaint_summary: str | None,
    user,
) -> bool:
    """
    Génère un email HTML via Gemini et l'envoie aux membres du groupe "mukubwa".
    Retourne True si l'envoi a réussi.
    """
    try:
        mukubwa_emails = _get_mukubwa_emails()
        if not mukubwa_emails:
            logger.warning("[Support] Aucun membre dans le groupe 'mukubwa'.")
            return False

        email_data = _generate_email_content(
            complaint_type=complaint_type,
            client_message=client_message,
            complaint_summary=complaint_summary or "Non spécifié",
            user=user,
        )

        return _send_email(email_data, mukubwa_emails, user)

    except Exception as e:
        logger.error(f"[Support] Erreur send_support_alert: {e}")
        return False


def _generate_email_content(
    complaint_type: str,
    client_message: str,
    complaint_summary: str,
    user,
) -> dict:
    """Appelle Gemini pour générer un email HTML structuré."""
    try:
        prompt = SUPPORT_EMAIL_PROMPT.format(
            complaint_type=COMPLAINT_LABELS.get(complaint_type, complaint_type),
            client_message=client_message[:500],
            complaint_summary=complaint_summary,
        )

        client = get_gemini_client()
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[{"role": "user", "parts": [{"text": prompt}]}],
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=800,
            ),
        )

        raw = getattr(response, "text", "") or ""
        cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group())

    except Exception as e:
        logger.warning(f"[Support] Gemini email generation failed: {e}")

    return _fallback_email_template(complaint_type, client_message, complaint_summary, user)


def _fallback_email_template(complaint_type, client_message, summary, user) -> dict:
    """Template HTML de secours si Gemini échoue."""
    label = COMPLAINT_LABELS.get(complaint_type, complaint_type)
    username = getattr(user, "username", "Client anonyme")
    email_addr = getattr(user, "email", "N/A")

    priority = "haute" if complaint_type in ("livraison", "produit_defectueux") else "normale"
    color = PRIORITY_COLORS.get(priority, "#d97706")

    body_html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden">
      <div style="background:#640c5f;padding:20px;color:white">
        <h2 style="margin:0">🔔 Alerte Support — Celebobo Business</h2>
      </div>
      <div style="padding:24px">
        <p style="margin-bottom:8px">
          <strong>Type de problème :</strong>
          <span style="background:{color};color:white;padding:2px 10px;border-radius:12px;font-size:13px">{label}</span>
        </p>
        <p><strong>Priorité :</strong> {priority.capitalize()}</p>
        <p><strong>Client :</strong> {username} ({email_addr})</p>
        <hr style="border:none;border-top:1px solid #e5e7eb;margin:16px 0">
        <p><strong>Résumé :</strong><br>{summary}</p>
        <hr style="border:none;border-top:1px solid #e5e7eb;margin:16px 0">
        <p><strong>Message original du client :</strong></p>
        <blockquote style="border-left:4px solid #640c5f;padding:12px 16px;background:#f9f9f9;color:#374151;border-radius:0 4px 4px 0">
          {client_message}
        </blockquote>
        <hr style="border:none;border-top:1px solid #e5e7eb;margin:16px 0">
        <p style="color:#6b7280;font-size:13px">
          Message automatique généré par l'assistant Celebobo Business.
        </p>
      </div>
    </div>
    """

    return {
        "subject": f"[{priority.upper()}] Plainte client — {label}",
        "body_html": body_html,
        "priority": priority,
    }


def _get_mukubwa_emails() -> list[str]:
    """Retourne les emails des utilisateurs actifs du groupe 'mukubwa'."""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return list(
            User.objects.filter(
                groups__name="mukubwa",
                is_active=True,
            ).values_list("email", flat=True)
            .exclude(email="")
        )
    except Exception as e:
        logger.error(f"[Support] Erreur récupération emails mukubwa: {e}")
        return []


def _send_email(email_data: dict, recipients: list[str], user) -> bool:
    """Envoie l'email HTML aux destinataires."""
    try:
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@celebobo.com")
        subject = email_data.get("subject", "Alerte support Celebobo")
        body_html = email_data.get("body_html", "")
        body_text = re.sub(r"<[^>]+>", "", body_html)  # version plain text

        msg = EmailMultiAlternatives(
            subject=subject,
            body=body_text,
            from_email=from_email,
            to=recipients,
        )
        msg.attach_alternative(body_html, "text/html")
        msg.send(fail_silently=False)

        logger.info(f"[Support] Email envoyé à {len(recipients)} membre(s) mukubwa.")
        return True

    except Exception as e:
        logger.error(f"[Support] Erreur envoi email: {e}")
        return False