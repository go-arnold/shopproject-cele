from django.shortcuts import render
from shop.models import Product
from shop.models import FavoriteProduct
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from shop.models import Category
from django.db.models import Exists, OuterRef, Value, BooleanField
from django.contrib.auth import get_user_model

User = get_user_model()


def allProducts(request):
    is_favorite_subquery = FavoriteProduct.objects.filter(
        utilisateur=request.user if request.user.is_authenticated else None,
        produit=OuterRef("pk"),
    )

    products_qs = (
        Product.objects.select_related("category_fk")
        .prefetch_related("features")
        .annotate(
            is_favorite=Exists(is_favorite_subquery)
            if request.user.is_authenticated
            else Value(False)
        )
        .order_by("name")
    )

    paginator = Paginator(products_qs, 12)
    page = request.GET.get("page")
    page_obj = paginator.get_page(page)
    context = {
        "products": page_obj,
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
        "total_count": paginator.count,
        "categories": Category.objects.all(),
    }
    return render(request, "shop/allProducts.html", context)
