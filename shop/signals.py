"""
Narrowly-scoped framework hooks only: dispatch background embedding tasks
on Product changes. No business logic here — that lives in
shop/services/embedding_service.py, run via shop/tasks/embeddings.py.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from shop.models import Product


@receiver(post_save, sender=Product)
def on_product_saved(sender, instance, **kwargs):
    from shop.tasks.embeddings import upsert_product_embedding_task

    upsert_product_embedding_task.delay(instance.pk)


@receiver(post_delete, sender=Product)
def on_product_deleted(sender, instance, **kwargs):
    from shop.tasks.embeddings import delete_product_embedding_task

    delete_product_embedding_task.delay(instance.pk)
