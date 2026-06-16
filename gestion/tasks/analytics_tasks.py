"""
Celery tasks for product analytics reporting and email notifications.

Tasks:
- send_product_analytics_email: Weekly report of top-asked products
"""

import os
import logging
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(
    name="gestion.tasks.send_product_analytics_email",
    autoretry_for={"max_retries": 3, "exc": Exception},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    time_limit=30,
    soft_time_limit=25,
)
def send_product_analytics_email():
    """
    Send weekly email with top-asked products and analytics.
    
    Configuration (via environment variables):
    - PRODUCT_ANALYTICS_TOP_N: Number of top products to report (default: 15)
    - PRODUCT_ANALYTICS_EMAIL_RECIPIENTS: Comma-separated email list
    - PRODUCT_ANALYTICS_SEND_DAY: Day to send (default: "monday")
    - PRODUCT_ANALYTICS_SEND_TIME: Time to send (default: "09:00")
    
    Scheduled via django-celery-beat (PeriodicTask model).
    """
    try:
        from shop.models import ProductQuestion
        
        # Get configuration from environment
        top_n = int(os.getenv("PRODUCT_ANALYTICS_TOP_N", "15"))
        recipients = os.getenv("PRODUCT_ANALYTICS_EMAIL_RECIPIENTS", "").split(",")
        recipients = [e.strip() for e in recipients if e.strip()]
        
        if not recipients:
            logger.warning("[Analytics] No email recipients configured. Skipping email.")
            return {"status": "skipped", "reason": "no_recipients"}
        
        logger.info(f"[Analytics] Generating product analytics report (top {top_n})")
        
        # Generate analytics report
        report = ProductQuestion.objects.get_analytics_report(n=top_n, days=30)
        
        logger.debug(f"[Analytics] Report generated: {len(report['top_products'])} products")
        
        # Prepare email data
        context = {
            "report": report,
            "site_name": os.getenv("SITE_NAME", "Celebobo"),
            "report_title": f"Top {top_n} Asked Products - Weekly Report",
            "generated_date": report["generated_at"],
        }
        
        # Render HTML template
        html_message = render_to_string(
            "emails/product_analytics.html",
            context
        )
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=f"[Celebobo Analytics] Top {top_n} Asked Products",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(
            f"[Analytics] Email sent successfully to {len(recipients)} recipients. "
            f"Top product: {report['top_products'][0]['product_name'] if report['top_products'] else 'N/A'}"
        )
        
        return {
            "status": "success",
            "recipients": len(recipients),
            "top_products_count": len(report["top_products"]),
            "total_questions": report["total_questions"],
        }
    
    except Exception as e:
        logger.error(f"[Analytics] Failed to send analytics email: {e}", exc_info=True)
        raise


@shared_task(
    name="gestion.tasks.cleanup_old_analytics",
    autoretry_for={"max_retries": 2},
    retry_backoff=True,
    time_limit=60,
    soft_time_limit=50,
)
def cleanup_old_analytics(days_to_keep=90):
    """
    Clean up old product question records (older than N days).
    
    Scheduled monthly to keep the database lean.
    
    Args:
        days_to_keep: Number of days of data to keep (default: 90)
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        from shop.models import ProductQuestion
        
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        deleted_count, _ = ProductQuestion.objects.filter(
            created_at__lt=cutoff_date
        ).delete()
        
        logger.info(
            f"[Analytics] Cleaned up {deleted_count} old product questions "
            f"(older than {days_to_keep} days)"
        )
        
        return {
            "status": "success",
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
        }
    
    except Exception as e:
        logger.error(f"[Analytics] Failed to cleanup old analytics: {e}", exc_info=True)
        raise
