from django.http import JsonResponse
import logging
from django.contrib.auth.models import Group
from shop.models import Vente
from utils.decorators import admin_required
from django.core.exceptions import PermissionDenied

from gestion.tasks.export_tasks import export_ventes_excel_task

logger = logging.getLogger("task_system")


@admin_required
def export_ventes_excel(request):
    """
    Export ventes to Excel.
    
    NEW (async): Returns task_id immediately (dispatch <100ms)
    Client polls GET /api/tasks/{task_id}/ to download when ready
    
    Response:
        {
            "task_id": str,
            "status": "queued",
            "poll_url": "/api/tasks/{task_id}/",
            "message": "Your export has been queued..."
        }
    """
    user = request.user
    rev = Group.objects.get(name="revendeur").user_set.all()
    muk = Group.objects.get(name="mukubwa").user_set.all()
    
    if user in rev and user not in muk:
        raise PermissionDenied()
    
    try:
        # Dispatch to Celery task (non-blocking)
        task = export_ventes_excel_task.apply_async(
            args=[user.id],
            kwargs={"filters_dict": None}
        )
        
        logger.info(
            "export_ventes_excel_dispatched",
            extra={
                "event": "export_dispatch",
                "export_type": "excel",
                "task_id": task.id,
                "user_id": user.id,
            }
        )
        
        return JsonResponse({
            "task_id": task.id,
            "status": "queued",
            "poll_url": f"/api/tasks/{task.id}/",
            "message": "Your Excel export has been queued. Poll the URL to check status.",
        }, status=202)
    
    except Exception as e:
        logger.error(
            "export_ventes_excel_dispatch_failed",
            extra={
                "event": "export_dispatch_error",
                "export_type": "excel",
                "user_id": user.id,
                "error": str(e),
            }
        )
        return JsonResponse(
            {"error": "Failed to queue export", "details": str(e)},
            status=500
        )
