from django.views.decorators.csrf import csrf_exempt
import json
import logging
from django.http import JsonResponse
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied

from gestion.tasks.export_tasks import export_dashboard_pdf_task

logger = logging.getLogger("task_system")


@csrf_exempt
def dashboard_pdf(request):
    """
    Export dashboard to PDF.
    
    NEW (async): Returns task_id immediately (dispatch <100ms)
    Client polls GET /api/tasks/{task_id}/ to download when ready
    
    Request:
        POST /export/dashboard/pdf/
        Body: {
            "images": ["https://...", "https://..."]
        }
    
    Response:
        {
            "task_id": str,
            "status": "queued",
            "poll_url": "/api/tasks/{task_id}/",
            "message": "Your PDF export has been queued..."
        }
    """
    user = request.user
    rev = Group.objects.get(name="revendeur").user_set.all()
    muk = Group.objects.get(name="mukubwa").user_set.all()
    
    if user in rev and user not in muk:
        raise PermissionDenied()
    
    if request.method != "POST":
        return JsonResponse(
            {"error": "Method not allowed. Use POST."},
            status=405
        )
    
    try:
        data = json.loads(request.body)
        images = data.get("images", [])
        
        # Dispatch to Celery task
        images_json = json.dumps(images)
        task = export_dashboard_pdf_task.apply_async(
            args=[user.id],
            kwargs={"images_json": images_json}
        )
        
        logger.info(
            "export_dashboard_pdf_dispatched",
            extra={
                "event": "export_dispatch",
                "export_type": "dashboard_pdf",
                "task_id": task.id,
                "user_id": user.id,
                "image_count": len(images),
            }
        )
        
        return JsonResponse({
            "task_id": task.id,
            "status": "queued",
            "poll_url": f"/api/tasks/{task.id}/",
            "message": "Your dashboard PDF export has been queued. Poll the URL to check status.",
        }, status=202)
    
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON in request body"},
            status=400
        )
    except Exception as e:
        logger.error(
            "export_dashboard_pdf_dispatch_failed",
            extra={
                "event": "export_dispatch_error",
                "export_type": "dashboard_pdf",
                "user_id": user.id,
                "error": str(e),
            }
        )
        return JsonResponse(
            {"error": "Failed to queue export", "details": str(e)},
            status=500
        )
