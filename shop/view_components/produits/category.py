from django.shortcuts import render, get_object_or_404
from shop.models import FavoriteProduct
from django.core.paginator import Paginator
from django.db.models import Max, Count, Exists, OuterRef, Value, BooleanField
from shop.models import Category
import random
from django.contrib.auth import get_user_model


User = get_user_model()


def categoryVue(request, pk):
    category = get_object_or_404(Category, pk=pk)

    products_qs = category.products.all().order_by("-id")

    if request.user.is_authenticated:
        is_favorite_subquery = FavoriteProduct.objects.filter(
            utilisateur=request.user, produit=OuterRef("pk")
        )
        products_qs = products_qs.annotate(is_favorite=Exists(is_favorite_subquery))
    else:
        products_qs = products_qs.annotate(
            is_favorite=Value(False, output_field=BooleanField())
        )

    products_qs = products_qs.select_related("category_fk").prefetch_related("features")

    paginator = Paginator(products_qs, 12)
    page = request.GET.get("page")
    page_obj = paginator.get_page(page)

    most_expensive_price = products_qs.aggregate(Max("price"))["price__max"]

    similar_qs = list(
        Category.objects.exclude(pk=category.pk)
        .annotate(prod_count=Count("products"))
        .order_by("-prod_count")[:10]
    )

    similar_category_one, similar_category_two = None, None
    if len(similar_qs) >= 2:
        similar_category_one, similar_category_two = random.sample(similar_qs, 2)
    elif len(similar_qs) == 1:
        similar_category_one = similar_qs[0]

    context = {
        "category": category,
        "products": page_obj,
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
        "start_index": page_obj.start_index(),
        "end_index": page_obj.end_index(),
        "total_count": paginator.count,
        "categories": Category.objects.all(),
        "most_expensive_price": most_expensive_price,
        "similar_category_one": similar_category_one,
        "similar_category_two": similar_category_two,
    }
    return render(request, "shop/category.html", context)
