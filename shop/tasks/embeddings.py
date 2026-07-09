"""
Celery tasks for product embedding maintenance.
Triggered by shop/signals.py whenever a Product is created, updated, or deleted.
"""

import logging
from celery import shared_task
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


@shared_task(
    name="shop.tasks.upsert_product_embedding",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    time_limit=30,
)
def upsert_product_embedding_task(product_id: int) -> None:
    """Re-embed a single product after create/update."""
    from shop.models import Product
    from shop.services.embedding_service import upsert_product_embedding

    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        logger.warning(f"[EmbeddingTask] Product {product_id} no longer exists")
        return

    async_to_sync(upsert_product_embedding)(product)


@shared_task(
    name="shop.tasks.delete_product_embedding",
    ignore_result=True,
    time_limit=15,
)
def delete_product_embedding_task(product_id: int) -> None:
    """Remove a product's embedding after deletion."""
    from shop.services.embedding_service import delete_product_embedding

    try:
        delete_product_embedding(product_id)
    except Exception as exc:
        logger.error(
            f"[EmbeddingTask] Failed to delete embedding for product {product_id}: {exc}",
            exc_info=True,
        )
