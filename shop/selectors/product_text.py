"""
Builds the rich, labeled text representation of a Product used as embedding
input for the RAG pipeline.

Every field gets an explicit label ("Prix : ...", "Caractéristiques : ...")
instead of terse concatenation, so the embedding captures what each value
means, not just its raw value.
"""


def build_product_document(product) -> str:
    """Pure text builder. No I/O, no side effects."""
    lines = [
        f"Produit : {product.name}.",
        f"Catégorie : {product.category}.",
    ]

    if product.price_solde:
        lines.append(
            f"Prix : {product.price} USD, actuellement en promotion à "
            f"{product.price_solde} USD (-{product.solde_percent}%)."
        )
    else:
        lines.append(f"Prix : {product.price} USD.")

    if product.description:
        lines.append(f"Description : {product.description}")

    if product.long_description:
        lines.append(f"Détails supplémentaires : {product.long_description}")

    feature_names = [f.name for f in product.features.all()]
    if feature_names:
        lines.append(
            f"Caractéristiques : le produit {product.name} possède les "
            f"caractéristiques suivantes : {', '.join(feature_names)}."
        )

    care_items = product.chara_entretien_list
    if care_items:
        lines.append(f"Entretien : {'; '.join(care_items)}.")

    badge = product.current_badge
    if badge:
        lines.append(f"Statut / badge : {badge}.")

    if product.average_rating:
        lines.append(
            f"Note client : {product.average_rating}/5 sur "
            f"{product.reviews_count} avis."
        )
    else:
        lines.append("Note client : aucune note client pour l'instant.")

    return "\n".join(lines)


def build_product_metadata(product) -> dict:
    """Snapshot of key fields, stored alongside the embedding for display/filtering."""
    return {
        "product_id": product.pk,
        "name": product.name,
        "category": product.category,
        "price": float(product.price) if product.price is not None else None,
        "price_solde": float(product.price_solde) if product.price_solde else None,
        "badge": product.current_badge,
        "rating": product.average_rating,
        "reviews_count": product.reviews_count,
    }
