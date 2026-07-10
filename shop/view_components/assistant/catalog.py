"""
Product formatting for assistant prompt context.

Retrieval itself is now handled by pgvector semantic search
(shop/selectors/product_search.py) — this module only renders the
Product objects it returns into the rich text the model reads.
"""


def format_product_full(p) -> str:
    """Detailed one-product block for the assistant's prompt context."""
    lines = [f"📦 **{p.name}**"]
    lines.append(f"  Catégorie : {p.category}")

    if p.price_solde:
        lines.append(
            f"  Prix : ~~${p.price}~~ → **${p.price_solde}** (-{p.solde_percent}% 🔥)"
        )
    else:
        lines.append(f"  Prix : **${p.price}**")

    if p.description:
        lines.append(f"  Description : {p.description}")

    if p.long_description:
        lines.append(f"  Détails : {p.long_description}")

    features = list(p.features.all()[:8])
    if features:
        feat_str = " | ".join([f.name for f in features])
        lines.append(f"  Caractéristiques : {feat_str}")

    if p.average_rating:
        lines.append(f"  Note : ★{p.average_rating}/5 ({p.reviews_count} avis clients)")
    elif p.rating:
        lines.append(f"  Note : ★{p.rating}/5")

    if p.current_badge:
        lines.append(f"  Badge : {p.current_badge}")

    return "\n".join(lines)
