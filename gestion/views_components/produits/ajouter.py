from django.shortcuts import render
from django.contrib.auth.models import Group
from django.shortcuts import redirect
from django.contrib import messages
from shop.models import (
    Product,
    Feature,
    Category,
)
from utils.decorators import admin_required
from django.core.exceptions import PermissionDenied


@admin_required
def add_product(request):
    user = request.user
    rev = Group.objects.get(name="revendeur").user_set.all()
    muk = Group.objects.get(name="mukubwa").user_set.all()
    if user in rev and user not in muk:
        raise PermissionDenied()
    if request.method == "POST":
        try:
            category_id = request.POST.get("category")
            category = Category.objects.filter(id=category_id).first()

            product = Product(
                name=request.POST.get("name"),
                description=request.POST.get("description"),
                long_description=request.POST.get("long_description"),
                chara_entretien=request.POST.get("chara_entretien"),
                delivery_policy_phase1=request.POST.get("delivery_policy_phase1"),
                delivery_policy_phase2=request.POST.get("delivery_policy_phase2"),
                price=request.POST.get("price"),
                price_primary=request.POST.get("price_primary") or None,
                price_solde=request.POST.get("price_solde") or None,
                category_fk=category,
                date_wish=request.POST.get("date_wish"),
            )

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

            features = request.POST.getlist("features[]")
            for feature_name in features:
                if feature_name.strip():
                    Feature.objects.create(product=product, name=feature_name.strip())

            messages.success(
                request, f'Le produit "{product.name}" a été ajouté avec succès.'
            )
            return redirect("gestion:admin_products")

        except Exception as e:
            messages.error(request, f"Erreur lors de l'ajout du produit : {str(e)}")

    context = {
        "categories": Category.objects.all(),
    }
    return render(request, "gestion/add_product.html", context)
