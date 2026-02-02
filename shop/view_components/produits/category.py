from django.shortcuts import render, get_object_or_404
from shop.models import FavoriteProduct
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Max, Count
from shop.models import Category
import random
from django.contrib.auth import get_user_model

User = get_user_model()


def categoryVue(request, pk):
    """Affiche une catégorie et ses produits.

    Args:
        request: HttpRequest
        pk: primary key (id) de la Category

    Contexte retourné:
    - `category`: instance de Category
    - `products`: QuerySet des produits rattachés
    - `categories`: liste de toutes les catégories (pour navigation)
    """
    category = get_object_or_404(Category, pk=pk)
    products_qs = (
        category.products.select_related("category_fk")
        .prefetch_related("features")
        .all()
        .order_by("-id")
    )

    if request.user.is_authenticated:
        user_favs = set(
            FavoriteProduct.objects.filter(
                utilisateur=request.user, produit__in=products_qs
            ).values_list("produit_id", flat=True)
        )

        for p in products_qs:
            p.is_favorite = p.id in user_favs

    else:
        for p in products_qs:
            p.is_favorite = False

    # Pagination: 12 produits par page
    paginator = Paginator(products_qs, 12)
    page = request.GET.get("page")
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    categories = Category.objects.all()

    # Prix le plus élevé pour cette catégorie
    agg = products_qs.aggregate(max_price=Max("price"))
    most_expensive_price = agg.get("max_price")

    # Catégories similaires: choisir jusqu'à 2 autres catégories
    similar_qs = (
        Category.objects.exclude(pk=category.pk)
        .annotate(prod_count=Count("products"))
        .order_by("-prod_count")
    )[:10]
    similar_qs = list(similar_qs)
    similar_category_one = None
    similar_category_two = None

    if len(similar_qs) >= 2:
        similar_category_one, similar_category_two = random.sample(similar_qs, 2)
    elif len(similar_qs) == 1:
        similar_category_one = similar_qs[0]
    context = {
        "category": category,
        "products": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
        "start_index": page_obj.start_index(),
        "end_index": page_obj.end_index(),
        "total_count": paginator.count,
        "categories": categories,
        "most_expensive_price": most_expensive_price,
        "similar_category_one": similar_category_one,
        "similar_category_two": similar_category_two,
    }
    return render(request, "shop/category.html", context)
