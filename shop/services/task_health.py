"""
Task Health Check Service

Provides health monitoring for Redis, Celery workers, and task queue.
Used by health check endpoint and internal status monitoring.

Patterns:
  - Returns detailed status on every check (not cached)
  - TimeoutError means service is unhealthy
  - All functions are synchronous (called from views)
"""

import logging
import time
from typing import Dict, Any, Optional
import redis
from django.core.cache import cache
from celery import current_app as celery_app
from celery.exceptions import Ignore
from django_celery_results.models import TaskResult

logger = logging.getLogger("task_system")


class TaskHealthError(Exception):
    """Raised when health check fails."""
    pass


def check_redis_connection() -> Dict[str, Any]:
    """
    Check if Redis is accessible.
    
    Returns:
        {
            "connected": bool,
            "latency_ms": float (if connected),
            "error": str (if not connected),
            "timestamp": ISO8601 string
        }
    """
    try:
        start = time.time()
        cache.set("_health_check", "alive", 1)
        value = cache.get("_health_check")
        latency_ms = (time.time() - start) * 1000
        
        if value != "alive":
            raise TaskHealthError("Cache set/get mismatch")
        
        logger.info(
            "redis_health_check",
            extra={
                "event": "redis_check",
                "status": "ok",
                "latency_ms": round(latency_ms, 2),
            }
        )
        
        return {
            "connected": True,
            "latency_ms": round(latency_ms, 2),
        }
    except Exception as e:
        error_msg = str(e)
        logger.warning(
            "redis_health_check_failed",
            extra={
                "event": "redis_check",
                "status": "error",
                "error": error_msg,
            }
        )
        return {
            "connected": False,
            "error": error_msg,
        }


def check_celery_worker_alive() -> Dict[str, Any]:
    """
    Check if Celery workers are alive and accepting tasks.
    
    Returns:
        {
            "workers_alive": int,
            "workers": [{"name": str, "status": str}],
            "error": str (if no workers),
            "timestamp": ISO8601 string
        }
    """
    try:
        inspect = celery_app.control.inspect()
        
        if not inspect:
            raise TaskHealthError("Celery inspector not available")
        
        # Get active workers
        stats = inspect.stats()
        if not stats:
            error_msg = "No Celery workers are alive"
            logger.warning(
                "celery_health_check_failed",
                extra={
                    "event": "celery_check",
                    "status": "no_workers",
                }
            )
            return {
                "workers_alive": 0,
                "workers": [],
                "error": error_msg,
            }
        
        workers_list = [
            {
                "name": worker_name,
                "status": "online",
                "pool": stats[worker_name].get("pool", {}).get("max-concurrency", "N/A"),
            }
            for worker_name in stats.keys()
        ]
        
        logger.info(
            "celery_health_check",
            extra={
                "event": "celery_check",
                "status": "ok",
                "workers": len(workers_list),
            }
        )
        
        return {
            "workers_alive": len(workers_list),
            "workers": workers_list,
        }
    except Exception as e:
        error_msg = str(e)
        logger.error(
            "celery_health_check_error",
            extra={
                "event": "celery_check",
                "status": "error",
                "error": error_msg,
            }
        )
        return {
            "workers_alive": 0,
            "workers": [],
            "error": error_msg,
        }


def get_queue_stats() -> Dict[str, Any]:
    """
    Get task queue statistics from database.
    
    Returns:
        {
            "total_tasks": int,
            "pending": int,
            "processing": int,
            "success": int,
            "failure": int,
        }
    """
    try:
        total = TaskResult.objects.count()
        pending = TaskResult.objects.filter(status="PENDING").count()
        processing = TaskResult.objects.filter(status="PROCESSING").count()
        success = TaskResult.objects.filter(status="SUCCESS").count()
        failure = TaskResult.objects.filter(status="FAILURE").count()
        
        logger.debug(
            "queue_stats",
            extra={
                "event": "queue_stats",
                "total": total,
                "pending": pending,
                "processing": processing,
                "success": success,
                "failure": failure,
            }
        )
        
        return {
            "total_tasks": total,
            "pending": pending,
            "processing": processing,
            "success": success,
            "failure": failure,
        }
    except Exception as e:
        logger.error(
            "queue_stats_error",
            extra={
                "event": "queue_stats",
                "error": str(e),
            }
        )
        return {
            "total_tasks": 0,
            "pending": 0,
            "processing": 0,
            "success": 0,
            "failure": 0,
            "error": str(e),
        }


def is_system_healthy() -> bool:
    """
    Quick check: is the system ready to accept tasks?
    
    Returns:
        True if Redis AND Celery workers are healthy
    """
    redis_ok = check_redis_connection().get("connected", False)
    celery_ok = check_celery_worker_alive().get("workers_alive", 0) > 0
    return redis_ok and celery_ok


def get_full_health_status() -> Dict[str, Any]:
    """
    Comprehensive health check for all systems.
    
    Returns:
        {
            "status": "healthy" | "degraded" | "unhealthy",
            "redis": {...},
            "celery": {...},
            "queue": {...},
            "overall_ok": bool,
            "timestamp": ISO8601 string
        }
    """
    import datetime
    
    redis_status = check_redis_connection()
    celery_status = check_celery_worker_alive()
    queue_status = get_queue_stats()
    
    # Determine overall health
    redis_ok = redis_status.get("connected", False)
    celery_ok = celery_status.get("workers_alive", 0) > 0
    
    if redis_ok and celery_ok:
        overall_status = "healthy"
    elif redis_ok or celery_ok:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"
    
    return {
        "status": overall_status,
        "overall_ok": overall_status == "healthy",
        "redis": redis_status,
        "celery": celery_status,
        "queue": queue_status,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
