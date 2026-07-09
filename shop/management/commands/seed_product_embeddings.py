import logging

from asgiref.sync import async_to_sync
from django.core.management.base import BaseCommand

from shop.models import Product
from shop.services.embedding_service import batch_upsert_product_embeddings

logger = logging.getLogger(__name__)

BATCH_SIZE = 50


class Command(BaseCommand):
    help = (
        "Backfill ProductEmbedding rows for the RAG assistant. "
        "Run once to seed the initial catalog; ongoing changes are "
        "handled automatically by shop/signals.py."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--only-missing",
            action="store_true",
            help="Skip products that already have an embedding.",
        )

    def handle(self, *args, **options):
        queryset = Product.objects.all().prefetch_related("features")
        if options["only_missing"]:
            queryset = queryset.filter(embedding__isnull=True)

        products = list(queryset)
        total = len(products)
        if not total:
            self.stdout.write(self.style.WARNING("No products to embed."))
            return

        self.stdout.write(f"Embedding {total} product(s)...")

        embedded = 0
        for i in range(0, total, BATCH_SIZE):
            batch = products[i : i + BATCH_SIZE]
            embedded += async_to_sync(batch_upsert_product_embeddings)(batch)
            self.stdout.write(f"  {min(i + BATCH_SIZE, total)}/{total}")

        self.stdout.write(self.style.SUCCESS(f"Done. Embedded {embedded} product(s)."))
