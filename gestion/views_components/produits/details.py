from django.core.paginator import Paginator
from django.shortcuts import render
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from shop.models import (
    Product,
    Category,
)
from utils.decorators import admin_required
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied


@admin_required
def admin_products(request):
    user = request.user
    rev = Group.objects.get(name="revendeur").user_set.all()
    muk = Group.objects.get(name="mukubwa").user_set.all()
    if user in rev and user not in muk:
        raise PermissionDenied()
    products_list = Product.objects.select_related("category_fk").order_by(
        "-date_added"
    )

    search_query = request.GET.get("search", "")
    if search_query:
        products_list = products_list.filter(name__icontains=search_query)

    category_filter = request.GET.get("category", "")
    if category_filter:
        products_list = products_list.filter(category_fk__id=category_filter)

    paginator = Paginator(products_list, 12)
    page_number = request.GET.get("page")
    products = paginator.get_page(page_number)

    context = {
        "products": products,
        "categories": Category.objects.all(),
        "search_query": search_query,
        "category_filter": category_filter,
    }
    return render(request, "gestion/admin_products.html", context)


@admin_required
def view_product(request, product_id):
    user = request.user
    rev = Group.objects.get(name="revendeur").user_set.all()
    muk = Group.objects.get(name="mukubwa").user_set.all()
    if user in rev and user not in muk:
        raise PermissionDenied()
    product = get_object_or_404(
        Product.objects.select_related("category_fk"), id=product_id
    )
    context = {
        "product": product,
    }
    return render(request, "gestion/view_product.html", context)


@admin_required
def get_product_details(request, product_id):
    user = request.user
    rev = Group.objects.get(name="revendeur").user_set.all()
    muk = Group.objects.get(name="mukubwa").user_set.all()
    if user in rev and user not in muk:
        raise PermissionDenied()
    try:
        produit = Product.objects.get(id=product_id)
        data = {
            "id": produit.id,
            "name": produit.name,
            "price": float(produit.price),
            "price_primary": float(produit.price_primary or 0),
            "category": produit.category_fk.name if produit.category_fk else "",
        }
        return JsonResponse(data)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Produit introuvable"}, status=404)
