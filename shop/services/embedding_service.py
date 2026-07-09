"""
Embedding generation and storage for the product RAG pipeline.

Single code path shared by:
- shop/tasks/embeddings.py (automatic, triggered by Product create/update/delete)
- shop/management/commands/seed_product_embeddings.py (manual bulk backfill)
"""

import logging
from typing import Iterable

from asgiref.sync import sync_to_async

from shop.services.gemini_async import get_async_gemini_client
from shop.selectors.product_text import build_product_document, build_product_metadata

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768


def _document_and_metadata(product) -> tuple[str, dict]:
    """Sync helper: both builders touch the ORM (FK, related features, rating aggregate)."""
    return build_product_document(product), build_product_metadata(product)


async def upsert_product_embedding(product) -> None:
    """Embed a single product and upsert its ProductEmbedding row."""
    from shop.models import ProductEmbedding

    text, metadata = await sync_to_async(_document_and_metadata)(product)
    client = await get_async_gemini_client()
    vector = await client.embed_content(
        text,
        task_type="RETRIEVAL_DOCUMENT",
        model=EMBEDDING_MODEL,
        output_dimensionality=EMBEDDING_DIMENSIONS,
    )

    await sync_to_async(ProductEmbedding.objects.update_or_create)(
        product=product,
        defaults={
            "embedding": vector,
            "embedded_text": text,
            "metadata": metadata,
            "model_name": EMBEDDING_MODEL,
        },
    )
    logger.info(f"[EmbeddingService] Upserted embedding for product {product.pk}")


def delete_product_embedding(product_id: int) -> None:
    """Remove a product's embedding row (product already deleted)."""
    from shop.models import ProductEmbedding

    deleted, _ = ProductEmbedding.objects.filter(product_id=product_id).delete()
    if deleted:
        logger.info(f"[EmbeddingService] Deleted embedding for product {product_id}")


async def batch_upsert_product_embeddings(products: Iterable) -> int:
    """
    Embed many products in as few Gemini round trips as possible.
    Used by the bulk seeding management command.

    Returns:
        int: number of products embedded
    """
    from shop.models import ProductEmbedding

    products = list(products)
    if not products:
        return 0

    pairs = await sync_to_async(lambda: [_document_and_metadata(p) for p in products])()
    texts = [text for text, _ in pairs]
    client = await get_async_gemini_client()
    vectors = await client.batch_embed_contents(
        texts,
        task_type="RETRIEVAL_DOCUMENT",
        model=EMBEDDING_MODEL,
        output_dimensionality=EMBEDDING_DIMENSIONS,
    )

    def _write():
        for product, (text, metadata), vector in zip(products, pairs, vectors):
            ProductEmbedding.objects.update_or_create(
                product=product,
                defaults={
                    "embedding": vector,
                    "embedded_text": text,
                    "metadata": metadata,
                    "model_name": EMBEDDING_MODEL,
                },
            )

    await sync_to_async(_write)()
    logger.info(f"[EmbeddingService] Batch-upserted {len(products)} product embeddings")
    return len(products)


async def embed_query(text: str) -> list[float]:
    """Embed a user query (asymmetric task_type vs. document embedding)."""
    client = await get_async_gemini_client()
    return await client.embed_content(
        text,
        task_type="RETRIEVAL_QUERY",
        model=EMBEDDING_MODEL,
        output_dimensionality=EMBEDDING_DIMENSIONS,
    )
