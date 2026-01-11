from django.shortcuts import render
from django.contrib.auth.models import Group
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from shop.models import (
    Product,
    Feature,
    Category,
)
from utils.decorators import admin_required
from django.core.exceptions import PermissionDenied


@admin_required
def edit_product(request, product_id):
    user = request.user
    rev = Group.objects.get(name="revendeur").user_set.all()
    muk = Group.objects.get(name="mukubwa").user_set.all()
    if user in rev and user not in muk:
        raise PermissionDenied()
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        try:
            category_id = request.POST.get("category")
            category = Category.objects.filter(id=category_id).first()

            product.name = request.POST.get("name")
            product.badge = request.POST.get("badge")
            product.description = request.POST.get("description")
            product.long_description = request.POST.get("long_description")
            product.chara_entretien = request.POST.get("chara_entretien")
            product.delivery_policy_phase1 = request.POST.get("delivery_policy_phase1")
            product.delivery_policy_phase2 = request.POST.get("delivery_policy_phase2")
            product.price = request.POST.get("price")
            product.price_primary = request.POST.get("price_primary") or None
            product.price_solde = request.POST.get("price_solde") or None
            product.category_fk = category
            product.date_wish = request.POST.get("date_wish")

            if "image" in request.FILES:
                product.image = request.FILES["image"]
            if "image_one" in request.FILES:
                product.image_one = request.FILES["image_one"]
            if "image_two" in request.FILES:
                product.image_two = request.FILES["image_two"]
            if "image_three" in request.FILES:
                product.image_three = request.FILES["image_three"]

            product.full_clean()
            product.save()

            product.features.all().delete()
            features = request.POST.getlist("features[]")
            for feature_name in features:
                if feature_name.strip():
                    Feature.objects.create(product=product, name=feature_name.strip())

            messages.success(
                request, f'Le produit "{product.name}" a été modifié avec succès.'
            )
            return redirect("gestion:admin_products")

        except Exception as e:
            messages.error(request, f"Erreur lors de la modification : {str(e)}")

    context = {
        "product": product,
        "categories": Category.objects.all(),
    }
    return render(request, "gestion/edit_product.html", context)
