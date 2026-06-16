"""
Export Tasks - Async PDF/Excel generation

Migrate heavy CPU operations (PDF, Excel) to Celery workers.
This allows exports to happen in background without blocking user requests.

Task Results:
  - Stored in database (django-celery-results)
  - Download URLs stored in Redis with 1-hour TTL
  - Client polls GET /api/tasks/{task_id}/ for status and download link

Retry Logic:
  - Auto-retry 3 times with exponential backoff
  - Failed tasks marked as FAILURE in database
  - User can manual retry via POST /api/tasks/{task_id}/retry/

Performance:
  - Export dispatch: <100ms (returns task_id immediately)
  - PDF generation: 2-5 seconds (in background)
  - Result polling: <50ms (just Redis lookup)

Logging:
  - Structured JSON logs with export time, file size, error details
  - Cost tracking not applicable (local operation, no API calls)
"""

import tempfile
import logging
import json
from io import BytesIO
from datetime import timedelta

from celery import shared_task, Task
from celery.exceptions import SoftTimeLimitExceeded
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.template.loader import render_to_string
from django.db.models import F
from django.contrib.auth.models import Group, User
from weasyprint import HTML, CSS
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.drawing.image import Image as XLImage
import os

from shop.models import Vente
from shop.services.ai_logger import ai_logger

logger = logging.getLogger("task_system")


class ExportTask(Task):
    """Base task class with error handling and retry logic."""
    
    autoretry_for = (SoftTimeLimitExceeded,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes max between retries
    retry_jitter = True
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails after all retries."""
        logger.error(
            "export_task_failed",
            extra={
                "event": "export_failure",
                "task_id": task_id,
                "task_name": self.name,
                "error": str(exc),
                "retries": self.request.retries,
            }
        )
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        logger.warning(
            "export_task_retry",
            extra={
                "event": "export_retry",
                "task_id": task_id,
                "task_name": self.name,
                "error": str(exc),
                "retry_count": self.request.retries,
            }
        )
    
    def on_success(self, result, task_id, args, kwargs):
        """Called when task succeeds."""
        logger.info(
            "export_task_success",
            extra={
                "event": "export_success",
                "task_id": task_id,
                "task_name": self.name,
                "result": result,
            }
        )


@shared_task(bind=True, base=ExportTask, time_limit=600, soft_time_limit=550)
def export_ventes_pdf_task(self, user_id: int, filters_dict: dict = None) -> dict:
    """
    Export sales (ventes) to PDF.
    
    Args:
        user_id: Django user ID
        filters_dict: Optional filters (e.g., {"date_range": "2024-01"})
    
    Returns:
        {
            "file_url": str,  # Download URL
            "file_size_kb": float,
            "export_time_ms": float,
            "filename": str,
        }
    """
    task_start = __import__('time').time()
    
    try:
        # 1. Get user and check permissions
        user = User.objects.get(id=user_id)
        
        # 2. Query ventes with optimizations
        ventes_qs = (
            Vente.objects.select_related("produit", "utilisateur")
            .annotate(
                produit_nom_flat=F("produit__name"),
                produit_prix_flat=F("produit__price"),
                utilisateur_username_flat=F("utilisateur__username"),
            )
            .only(
                "date_achat",
                "method",
                "price_final",
                "produit__name",
                "produit__price",
                "utilisateur__username",
            )
            .order_by("-date_achat")
        )
        
        # Apply permission filter
        if not user.groups.filter(name="mukubwa").exists():
            ventes_qs = ventes_qs.filter(utilisateur=user)
        
        # Apply optional filters
        if filters_dict and filters_dict.get("date_range"):
            # Example: "2024-01" format
            date_range = filters_dict["date_range"]
            ventes_qs = ventes_qs.filter(
                date_achat__startswith=date_range
            )
        
        ventes = list(ventes_qs[:1000])  # Limit to 1000 records
        
        # 3. Render HTML template
        html_string = render_to_string(
            "gestion/export_ventes_pdf.html",
            {"ventes": ventes, "user": user}
        )
        
        # 4. Generate PDF using WeasyPrint
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            HTML(string=html_string).write_pdf(tmp.name)
            with open(tmp.name, 'rb') as f:
                pdf_content = f.read()
            os.unlink(tmp.name)
        
        # 5. Upload to Cloudinary (via default_storage)
        filename = f"exports/ventes_{user_id}_{self.request.id}.pdf"
        file_obj = ContentFile(pdf_content, name=filename)
        file_url = default_storage.save(filename, file_obj)
        
        # 6. Store download URL in Redis with 1-hour TTL
        cache_key = f"export_url_{self.request.id}"
        cache.set(cache_key, file_url, timeout=3600)
        
        export_time_ms = (__import__('time').time() - task_start) * 1000
        file_size_kb = len(pdf_content) / 1024
        
        logger.info(
            "export_ventes_pdf_completed",
            extra={
                "event": "export_ventes_pdf",
                "status": "success",
                "task_id": self.request.id,
                "user_id": user_id,
                "export_time_ms": round(export_time_ms, 2),
                "file_size_kb": round(file_size_kb, 2),
                "record_count": len(ventes),
            }
        )
        
        return {
            "file_url": file_url,
            "file_size_kb": round(file_size_kb, 2),
            "export_time_ms": round(export_time_ms, 2),
            "filename": filename,
        }
    
    except SoftTimeLimitExceeded:
        logger.error(
            "export_ventes_pdf_timeout",
            extra={
                "event": "export_timeout",
                "task_id": self.request.id,
                "user_id": user_id,
            }
        )
        raise
    except Exception as e:
        logger.error(
            "export_ventes_pdf_error",
            extra={
                "event": "export_error",
                "task_id": self.request.id,
                "user_id": user_id,
                "error": str(e),
            },
            exc_info=True
        )
        raise


@shared_task(bind=True, base=ExportTask, time_limit=600, soft_time_limit=550)
def export_ventes_excel_task(self, user_id: int, filters_dict: dict = None) -> dict:
    """
    Export sales (ventes) to Excel.
    
    Args:
        user_id: Django user ID
        filters_dict: Optional filters
    
    Returns:
        {
            "file_url": str,
            "file_size_kb": float,
            "export_time_ms": float,
            "filename": str,
        }
    """
    task_start = __import__('time').time()
    
    try:
        # 1. Get user
        user = User.objects.get(id=user_id)
        
        # 2. Query ventes
        if user.groups.filter(name="mukubwa").exists():
            ventes = Vente.objects.select_related("produit", "utilisateur")
        else:
            ventes = Vente.objects.filter(utilisateur=user).select_related(
                "produit", "utilisateur"
            )
        
        # Apply optional filters
        if filters_dict and filters_dict.get("date_range"):
            date_range = filters_dict["date_range"]
            ventes = ventes.filter(date_achat__startswith=date_range)
        
        ventes = list(ventes[:1000])
        
        # 3. Create Excel workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Ventes"
        
        # 4. Add headers
        headers = ["Date", "Produit", "Prix Produit", "Vendeur", "Méthode", "Prix Final"]
        ws.append(headers)
        
        # Style headers
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill("solid", fgColor="4B0082")
        alignment_center = Alignment(horizontal="center", vertical="center")
        
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = alignment_center
        
        # 5. Add data rows
        for vente in ventes:
            ws.append([
                str(vente.date_achat.date()),
                vente.produit.name,
                vente.produit.price,
                vente.utilisateur.username,
                vente.method,
                vente.price_final,
            ])
        
        # 6. Save to BytesIO
        excel_buffer = BytesIO()
        wb.save(excel_buffer)
        excel_content = excel_buffer.getvalue()
        
        # 7. Upload to Cloudinary
        filename = f"exports/ventes_{user_id}_{self.request.id}.xlsx"
        file_obj = ContentFile(excel_content, name=filename)
        file_url = default_storage.save(filename, file_obj)
        
        # 8. Store URL in Redis
        cache_key = f"export_url_{self.request.id}"
        cache.set(cache_key, file_url, timeout=3600)
        
        export_time_ms = (__import__('time').time() - task_start) * 1000
        file_size_kb = len(excel_content) / 1024
        
        logger.info(
            "export_ventes_excel_completed",
            extra={
                "event": "export_ventes_excel",
                "status": "success",
                "task_id": self.request.id,
                "user_id": user_id,
                "export_time_ms": round(export_time_ms, 2),
                "file_size_kb": round(file_size_kb, 2),
                "record_count": len(ventes),
            }
        )
        
        return {
            "file_url": file_url,
            "file_size_kb": round(file_size_kb, 2),
            "export_time_ms": round(export_time_ms, 2),
            "filename": filename,
        }
    
    except SoftTimeLimitExceeded:
        logger.error(
            "export_ventes_excel_timeout",
            extra={
                "event": "export_timeout",
                "task_id": self.request.id,
                "user_id": user_id,
            }
        )
        raise
    except Exception as e:
        logger.error(
            "export_ventes_excel_error",
            extra={
                "event": "export_error",
                "task_id": self.request.id,
                "user_id": user_id,
                "error": str(e),
            },
            exc_info=True
        )
        raise


@shared_task(bind=True, base=ExportTask, time_limit=300, soft_time_limit=280)
def export_dashboard_pdf_task(self, user_id: int, images_json: str = None) -> dict:
    """
    Export dashboard analytics to PDF.
    
    Args:
        user_id: Django user ID
        images_json: JSON string with chart images
    
    Returns:
        {
            "file_url": str,
            "file_size_kb": float,
            "export_time_ms": float,
        }
    """
    task_start = __import__('time').time()
    
    try:
        user = User.objects.get(id=user_id)
        
        # Parse images
        images = []
        if images_json:
            try:
                images = json.loads(images_json)
            except json.JSONDecodeError:
                images = []
        
        # Build HTML with dashboard content
        html_content = f"""
        <html>
        <head>
           <style>
              @page {{
                   size: A4;
                   margin: 20mm;
              }}
              body {{
                   font-family: Arial, sans-serif;
                   color: #333;
              }}
              h1 {{ text-align: center; color: #4B0082; }}
              .chart {{ page-break-inside: avoid; margin: 20px 0; }}
              img {{ max-width: 100%; height: auto; }}
           </style>
        </head>
        <body>
           <h1>Dashboard Export - {user.username}</h1>
        """
        
        for i, image_url in enumerate(images):
            html_content += f'<div class="chart"><img src="{image_url}" /></div>'
        
        html_content += "</body></html>"
        
        # Generate PDF
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            HTML(string=html_content).write_pdf(tmp.name)
            with open(tmp.name, 'rb') as f:
                pdf_content = f.read()
            os.unlink(tmp.name)
        
        # Upload
        filename = f"exports/dashboard_{user_id}_{self.request.id}.pdf"
        file_obj = ContentFile(pdf_content, name=filename)
        file_url = default_storage.save(filename, file_obj)
        
        # Cache
        cache_key = f"export_url_{self.request.id}"
        cache.set(cache_key, file_url, timeout=3600)
        
        export_time_ms = (__import__('time').time() - task_start) * 1000
        file_size_kb = len(pdf_content) / 1024
        
        logger.info(
            "export_dashboard_pdf_completed",
            extra={
                "event": "export_dashboard_pdf",
                "status": "success",
                "task_id": self.request.id,
                "user_id": user_id,
                "export_time_ms": round(export_time_ms, 2),
                "file_size_kb": round(file_size_kb, 2),
            }
        )
        
        return {
            "file_url": file_url,
            "file_size_kb": round(file_size_kb, 2),
            "export_time_ms": round(export_time_ms, 2),
            "filename": filename,
        }
    
    except Exception as e:
        logger.error(
            "export_dashboard_pdf_error",
            extra={
                "event": "export_error",
                "task_id": self.request.id,
                "user_id": user_id,
                "error": str(e),
            },
            exc_info=True
        )
        raise


def retry_failed_task(task_result):
    """
    Retry a failed task.
    
    Extracts original task arguments and re-dispatches.
    Returns new task ID.
    """
    task_name = task_result.task_name
    
    try:
        # Parse original args
        args = json.loads(task_result.task_args) if task_result.task_args else []
        kwargs = json.loads(task_result.task_kwargs) if task_result.task_kwargs else {}
    except json.JSONDecodeError:
        raise ValueError("Could not parse original task arguments")
    
    # Get task function and retry
    from celery import current_app as celery_app
    
    task_func = celery_app.tasks.get(task_name)
    if not task_func:
        raise ValueError(f"Task {task_name} not found")
    
    new_task = task_func.apply_async(args=args, kwargs=kwargs)
    
    logger.info(
        "retry_failed_task",
        extra={
            "event": "task_retry_manual",
            "original_task_id": task_result.task_id,
            "new_task_id": new_task.id,
            "task_name": task_name,
        }
    )
    
    return new_task.id
