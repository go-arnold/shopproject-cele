"""
Read-only pgvector similarity search over ProductEmbedding.
Side-effect free: takes a precomputed query embedding, returns Products.
"""

from pgvector.django import CosineDistance

from shop.models import Product, ProductEmbedding

# Cosine distance is in [0, 2]; results past this are treated as "not relevant"
# rather than forced into the assistant's context.
DEFAULT_MAX_DISTANCE = 0.6


def semantic_search(
    query_embedding: list[float],
    limit: int = 5,
    max_distance: float = DEFAULT_MAX_DISTANCE,
) -> list[Product]:
    """Return the products whose embedding is closest to query_embedding."""
    matches = (
        ProductEmbedding.objects.select_related("product")
        .prefetch_related("product__features")
        .annotate(distance=CosineDistance("embedding", query_embedding))
        .filter(distance__lte=max_distance)
        .order_by("distance")[:limit]
    )
    return [m.product for m in matches]
