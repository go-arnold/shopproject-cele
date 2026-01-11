from django.shortcuts import render
from shop.models import Product
from shop.models import FavoriteProduct
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from shop.models import Category
from django.contrib.auth import get_user_model

User = get_user_model()


def allProducts(request):
    """Affiche tous les produits avec la même pagination que `categoryVue`.

    Contexte retourné (noms identiques à `categoryVue` pour compatibilité):
    - `products`: liste de produits pour la page courante
    - `page_obj`, `paginator`, `is_paginated`, `start_index`, `end_index`, `total_count`
    - `categories`: toutes les catégories (utile pour la navigation)
    """
    products_qs = (
        Product.objects.select_related("category_fk").prefetch_related("features").all()
    )  # .order_by("name")

    if request.user.is_authenticated:
        for p in products_qs:
            p.is_favorite = FavoriteProduct.objects.filter(
                utilisateur=request.user, produit=p
            ).exists()
    else:
        for p in products_qs:
            p.is_favorite = False

    paginator = Paginator(products_qs, 12)
    page = request.GET.get("page")
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    categories = Category.objects.all()

    context = {
        "products": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
        "start_index": page_obj.start_index(),
        "end_index": page_obj.end_index(),
        "total_count": paginator.count,
        "categories": categories,
    }
    return render(request, "shop/allProducts.html", context)
