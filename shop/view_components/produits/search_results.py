from django.shortcuts import render
from shop.models import Product
from shop.models import FavoriteProduct
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.contrib.auth import get_user_model

User = get_user_model()


def results(request):
    query = request.GET.get("q", "").strip()

    # Preselect all products
    products = Product.objects.all()

    if request.user.is_authenticated:
        favorite_ids = set(
            FavoriteProduct.objects.filter(utilisateur=request.user).values_list(
                "produit_id", flat=True
            )
        )
    else:
        favorite_ids = set()

    # Handle search query
    if query:
        keywords = query.split()
        q_object = Q()

        for word in keywords:
            q_object &= (
                Q(name__icontains=word)
                | Q(description__icontains=word)
                | Q(long_description__icontains=word)
                | Q(category_legacy__icontains=word)
                | Q(category_fk__name__icontains=word)
            )

        products = products.filter(q_object).distinct()

    # Pagination
    paginator = Paginator(products, 12)
    page_num = request.GET.get("page")

    try:
        page_obj = paginator.page(page_num)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    for p in page_obj:
        p.is_favorite = p.id in favorite_ids

    return render(
        request,
        "shop/results.html",
        {
            "query": query,
            "products": page_obj,
            "page_obj": page_obj,
            "paginator": paginator,
            "is_paginated": page_obj.has_other_pages(),
            "start_index": page_obj.start_index(),
            "end_index": page_obj.end_index(),
            "total_count": paginator.count,
        },
    )
