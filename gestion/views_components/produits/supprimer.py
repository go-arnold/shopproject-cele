from django.shortcuts import render
from django.contrib.auth.models import Group
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from shop.models import (
    Product,
)
from utils.decorators import admin_required
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied


@admin_required
def delete_product(request, product_id):
    user = request.user
    rev = Group.objects.get(name="revendeur").user_set.all()
    muk = Group.objects.get(name="mukubwa").user_set.all()
    if user in rev and user not in muk:
        raise PermissionDenied()
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        product_name = product.name
        product.delete()
        messages.success(
            request, f'Le produit "{product_name}" a été supprimé avec succès.'
        )

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        return redirect("gestion:admin_products")

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(
            request, "gestion/delete_product_partial.html", {"product": product}
        )

    return render(request, "gestion/delete_product.html", {"product": product})
