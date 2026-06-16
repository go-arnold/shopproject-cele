"""
Health Check Endpoint

GET /api/health/ - Full system health status (Redis, Celery, Queue)
GET /api/health/redis/ - Redis connectivity only
GET /api/health/celery/ - Celery workers only
GET /api/health/queue/ - Task queue statistics

Used by:
  - Load balancers (checking if service is alive)
  - Monitoring systems (Prometheus, DataDog)
  - Admin dashboard (checking system status)
  - Client-side (checking before dispatching tasks)

Returns HTTP 200 if healthy, 503 if unhealthy.
"""

import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from shop.services.task_health import (
    check_redis_connection,
    check_celery_worker_alive,
    get_queue_stats,
    get_full_health_status,
    is_system_healthy,
)
import logging

logger = logging.getLogger("task_system")


@require_http_methods(["GET"])
def health_check_full(request):
    """
    Full system health check.
    
    Returns 200 if healthy, 503 if unhealthy.
    """
    status = get_full_health_status()
    http_status = 200 if status["overall_ok"] else 503
    
    logger.info(
        "health_check_full",
        extra={
            "event": "health_check",
            "scope": "full",
            "status": status["status"],
            "http_status": http_status,
        }
    )
    
    return JsonResponse(status, status=http_status)


@require_http_methods(["GET"])
def health_check_redis(request):
    """Check Redis connectivity only."""
    status = check_redis_connection()
    http_status = 200 if status.get("connected", False) else 503
    
    return JsonResponse(status, status=http_status)


@require_http_methods(["GET"])
def health_check_celery(request):
    """Check Celery workers only."""
    status = check_celery_worker_alive()
    http_status = 200 if status.get("workers_alive", 0) > 0 else 503
    
    return JsonResponse(status, status=http_status)


@require_http_methods(["GET"])
def health_check_queue(request):
    """Check task queue statistics."""
    status = get_queue_stats()
    
    return JsonResponse(status, status=200)


@require_http_methods(["GET"])
def task_status(request, task_id):
    """
    Get status of a specific task.
    
    GET /api/tasks/{task_id}/
    
    Returns:
        {
            "task_id": str,
            "status": "PENDING" | "PROCESSING" | "SUCCESS" | "FAILURE" | "RETRY",
            "result": {...} (if SUCCESS),
            "error": str (if FAILURE),
            "progress": {
                "current": int,
                "total": int,
                "percentage": float (0-100)
            }
        }
    """
    from django_celery_results.models import TaskResult
    
    try:
        task_result = TaskResult.objects.get(task_id=task_id)
    except TaskResult.DoesNotExist:
        return JsonResponse(
            {"error": "Task not found", "task_id": task_id},
            status=404
        )
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
    }
    
    if task_result.result:
        try:
            result = json.loads(task_result.result) if isinstance(task_result.result, str) else task_result.result
            response["result"] = result
        except (json.JSONDecodeError, TypeError):
            response["result"] = task_result.result
    
    if task_result.traceback:
        response["error"] = task_result.traceback
    
    # Log task status checks
    logger.debug(
        "task_status_check",
        extra={
            "event": "task_status",
            "task_id": task_id,
            "status": task_result.status,
        }
    )
    
    http_status = 200
    if task_result.status == "FAILURE":
        http_status = 400
    
    return JsonResponse(response, status=http_status)


@require_http_methods(["POST"])
def task_retry(request, task_id):
    """
    Retry a failed task.
    
    POST /api/tasks/{task_id}/retry/
    
    Only works if original task is in FAILURE state.
    Requires authentication.
    """
    if not request.user.is_authenticated:
        raise PermissionDenied("Authentication required")
    
    from django_celery_results.models import TaskResult
    from gestion.tasks.export_tasks import retry_failed_task
    
    try:
        task_result = TaskResult.objects.get(task_id=task_id)
    except TaskResult.DoesNotExist:
        return JsonResponse(
            {"error": "Task not found", "task_id": task_id},
            status=404
        )
    
    if task_result.status != "FAILURE":
        return JsonResponse(
            {"error": f"Cannot retry task in {task_result.status} state"},
            status=400
        )
    
    # Dispatch retry
    try:
        new_task_id = retry_failed_task(task_result)
        
        logger.info(
            "task_retry_requested",
            extra={
                "event": "task_retry",
                "original_task_id": task_id,
                "new_task_id": new_task_id,
                "user_id": request.user.id,
            }
        )
        
        return JsonResponse({
            "status": "retrying",
            "original_task_id": task_id,
            "new_task_id": new_task_id,
        }, status=202)
    except Exception as e:
        logger.error(
            "task_retry_failed",
            extra={
                "event": "task_retry",
                "task_id": task_id,
                "error": str(e),
            }
        )
        return JsonResponse(
            {"error": str(e)},
            status=500
        )
