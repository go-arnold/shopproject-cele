"""
Accès au catalogue produits depuis la base de données.
Deux niveaux de détail : résumé (contexte système) et détaillé (réponse ciblée).
"""

from django.db.models import Q




def get_compact_catalog(limit: int = 20) -> str:
    """Catalogue ultra-compact pour les messages généraux. Moins de tokens = Gemini plus rapide."""
    try:
        from shop.models import Product

        products = Product.objects.select_related("category_fk").order_by(
            "-date_added"
        )[:limit]
        if not products:
            return "Catalogue temporairement indisponible."
        return "\n".join(_format_one_liner(p) for p in products)
    except Exception as e:
        return f"Catalogue indisponible. ({e})"


def quick_search(terms: list[str], limit: int = 5) -> str:
    """Recherche DB rapide par mots-clés Python, sans appel Gemini supplémentaire."""
    try:
        from shop.models import Product

        if not terms:
            return get_compact_catalog(limit=15)

        q = Q()
        for term in terms:
            q |= Q(name__icontains=term)
            q |= Q(category_fk__name__icontains=term)
            q |= Q(category_legacy__icontains=term)

        qs = (
            Product.objects.filter(q)
            .select_related("category_fk")
            .prefetch_related("features")
            .distinct()
            .order_by("-date_added")[:limit]
        )

        if not qs.exists():
            q2 = Q()
            for term in terms:
                q2 |= Q(description__icontains=term)
                q2 |= Q(features__name__icontains=term)
            qs = (
                Product.objects.filter(q2)
                .select_related("category_fk")
                .prefetch_related("features")
                .distinct()
                .order_by("-date_added")[:limit]
            )

        if not qs.exists():
            return "Aucun produit trouvé.\n" + get_compact_catalog(10)

        return "\n\n".join(_format_single_product_full(p) for p in qs)

    except Exception as e:
        return f"Erreur recherche. ({e})"


def _format_one_liner(p) -> str:
    """Format ultra-compact : 1 ligne par produit."""
    price = (
        f"{p.price_solde} FC (-{p.solde_percent}%)"
        if p.price_solde
        else f"{p.price} FC"
    )
    return f"• {p.name} [{p.category}] {price}"




def get_full_catalog(limit: int = 60) -> str:
    """
    Retourne un résumé compact du catalogue pour injecter dans le contexte système.
    Format: une ligne par produit pour minimiser les tokens.
    """
    try:
        from shop.models import Product

        products = (
            Product.objects.select_related("category_fk")
            .prefetch_related("features")
            .order_by("-date_added")[:limit]
        )

        if not products:
            return "Catalogue temporairement indisponible."

        lines = []
        for p in products:
            lines.append(_format_single_product_summary(p))

        return "\n".join(lines)

    except Exception as e:
        return f"Catalogue temporairement indisponible. ({e})"


def search_products(
    terms: list[str],
    category_hint: str | None = None,
    limit: int = 6,
) -> str:
    """
    Recherche ciblée dans la DB avec les termes extraits par l'IA.
    Retourne un format détaillé pour que Gemini puisse répondre précisément.
    """
    try:
        from shop.models import Product

        if not terms:
            return get_full_catalog(limit=limit)

        # Construction de la requête OR sur tous les champs textuels
        q = Q()
        for term in terms:
            q |= Q(name__icontains=term)
            q |= Q(description__icontains=term)
            q |= Q(category_fk__name__icontains=term)
            q |= Q(category_legacy__icontains=term)
            q |= Q(features__name__icontains=term)

        qs = (
            Product.objects.filter(q)
            .select_related("category_fk")
            .prefetch_related("features")
            .distinct()
            .order_by("-date_added")[:limit]
        )

        # Fallback : essai sur catégorie seule si aucun résultat
        if not qs.exists() and category_hint:
            qs = (
                Product.objects.filter(
                    Q(category_fk__name__icontains=category_hint)
                    | Q(category_legacy__icontains=category_hint)
                )
                .select_related("category_fk")
                .prefetch_related("features")
                .order_by("-date_added")[:limit]
            )

        if not qs.exists():
            return "Aucun produit trouvé correspondant à cette recherche."

        lines = []
        for p in qs:
            lines.append(_format_single_product_full(p))

        return "\n\n".join(lines)

    except Exception as e:
        return f"Erreur lors de la recherche produits. ({e})"


def get_product_by_id(product_id: int) -> str:
    """Retourne le détail complet d'un produit par son ID."""
    try:
        from shop.models import Product

        p = (
            Product.objects.select_related("category_fk")
            .prefetch_related("features")
            .get(pk=product_id)
        )
        return _format_single_product_full(p)
    except Exception:
        return "Produit introuvable."


# ── Helpers de formatage ───────────────────────────────────────────────────────


def _format_single_product_summary(p) -> str:
    """Format compact : une ligne pour le contexte système."""
    if p.price_solde:
        price_info = (
            f"Promo {p.price_solde} FC (au lieu de {p.price} FC, -{p.solde_percent}%)"
        )
    else:
        price_info = f"{p.price} FC"

    badge = f" [{p.current_badge}]" if p.current_badge else ""
    rating = ""
    if p.average_rating:
        rating = f" ★{p.average_rating}/5 ({p.reviews_count} avis)"
    elif p.rating:
        rating = f" ★{p.rating}/5"

    return f"- {p.name} | {p.category} | {price_info}{badge}{rating}"


def _format_single_product_full(p) -> str:
    """Format détaillé : pour une réponse ciblée sur un produit."""
    lines = [f"📦 **{p.name}**"]
    lines.append(f"  Catégorie : {p.category}")

    if p.price_solde:
        lines.append(
            f"  Prix : ~~{p.price} FC~~ → **{p.price_solde} FC** (-{p.solde_percent}% 🔥)"
        )
    else:
        lines.append(f"  Prix : **{p.price} FC**")

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
