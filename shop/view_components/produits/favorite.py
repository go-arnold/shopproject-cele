from django.shortcuts import render, get_object_or_404
from shop.models import Product
from django.http import JsonResponse, HttpResponseBadRequest
from shop.models import FavoriteProduct
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model


User = get_user_model()


@login_required
def add_favorite(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    fav, created = FavoriteProduct.objects.get_or_create(
        utilisateur=request.user, produit=product
    )
    return JsonResponse({"added": True})


@login_required
def remove_favorite(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    FavoriteProduct.objects.filter(utilisateur=request.user, produit=product).delete()
    return JsonResponse({"removed": True})


@login_required
def toggle_favorite(request, product_id):
    """Un seul endpoint : s'il est favori → enlever. Sinon → ajouter."""
    if request.method != "POST":
        return HttpResponseBadRequest("Méthode invalide")

    product = get_object_or_404(Product, id=product_id)

    fav = FavoriteProduct.objects.filter(utilisateur=request.user, produit=product)

    if fav.exists():
        fav.delete()
        return JsonResponse({"favori": False})

    else:
        FavoriteProduct.objects.create(utilisateur=request.user, produit=product)
        return JsonResponse({"favori": True})


@login_required
def favorites_list(request):
    favoris = FavoriteProduct.objects.filter(utilisateur=request.user).select_related(
        "produit"
    )

    products = [fav.produit for fav in favoris]
    for p in products:
        p.is_favorite = FavoriteProduct.objects.filter(
            utilisateur=request.user, produit=p
        ).exists()

    paginator = Paginator(products, 12)
    page = request.GET.get("page")
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        "products": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
        "start_index": page_obj.start_index(),
        "end_index": page_obj.end_index(),
        "total_count": paginator.count,
    }

    return render(request, "shop/favorite.html", context)
