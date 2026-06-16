import tempfile
from weasyprint import HTML
import logging
import json

from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import Group
from django.templatetags.static import static
from django.core.exceptions import PermissionDenied
from django.db.models import F

from shop.models import Vente
from utils.decorators import admin_required
from gestion.tasks.export_tasks import export_ventes_pdf_task

logger = logging.getLogger("task_system")


@admin_required
def export_ventes_pdf(request):
    """
    Export ventes to PDF.
    
    NEW (async): Returns task_id immediately (dispatch <100ms)
    Client polls GET /api/tasks/{task_id}/ to download when ready
    
    Response:
        {
            "task_id": str,
            "status": "queued",
            "poll_url": "/api/tasks/{task_id}/",
            "message": "Your export has been queued. You can check status at poll_url"
        }
    """
    user = request.user
    
    rev = Group.objects.get(name="revendeur").user_set.all()
    muk = Group.objects.get(name="mukubwa").user_set.all()
    
    if user in rev and user not in muk:
        raise PermissionDenied()
    
    try:
        # Dispatch to Celery task (non-blocking)
        task = export_ventes_pdf_task.apply_async(
            args=[user.id],
            kwargs={"filters_dict": None}
        )
        
        logger.info(
            "export_ventes_pdf_dispatched",
            extra={
                "event": "export_dispatch",
                "export_type": "pdf",
                "task_id": task.id,
                "user_id": user.id,
            }
        )
        
        return JsonResponse({
            "task_id": task.id,
            "status": "queued",
            "poll_url": f"/api/tasks/{task.id}/",
            "message": "Your PDF export has been queued. Poll the URL to check status.",
        }, status=202)
    
    except Exception as e:
        logger.error(
            "export_ventes_pdf_dispatch_failed",
            extra={
                "event": "export_dispatch_error",
                "export_type": "pdf",
                "user_id": user.id,
                "error": str(e),
            }
        )
        return JsonResponse(
            {"error": "Failed to queue export", "details": str(e)},
            status=500
        )
