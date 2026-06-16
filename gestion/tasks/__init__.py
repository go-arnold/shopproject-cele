"""
Gestion App Tasks

Celery tasks for background processing:
  - export_tasks: PDF/Excel export generation
  - bulk_tasks: Bulk database operations (future)
  - analytics_tasks: Data aggregation (future)

Import tasks in this module to ensure Celery autodiscovery finds them.
"""

from .export_tasks import (
    export_ventes_pdf_task,
    export_ventes_excel_task,
    export_dashboard_pdf_task,
)

__all__ = [
    'export_ventes_pdf_task',
    'export_ventes_excel_task',
    'export_dashboard_pdf_task',
]
