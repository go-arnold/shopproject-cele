"""
Shop App Tasks

Celery tasks for background processing:
  - image_tasks: Image processing (future)
  - ai_tasks: AI processing (already integrated in services)

Import tasks in this module to ensure Celery autodiscovery finds them.
"""

from .embeddings import upsert_product_embedding_task, delete_product_embedding_task

__all__ = ["upsert_product_embedding_task", "delete_product_embedding_task"]
