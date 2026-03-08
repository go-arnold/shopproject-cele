from django.shortcuts import render, get_object_or_404
from shop.models import Product
from shop.models import FavoriteProduct
from shop.models import Category
import random
from django.contrib.auth import get_user_model

User = get_user_model()


def productVue(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.user.is_authenticated:
        product.is_favorite = FavoriteProduct.objects.filter(
            utilisateur=request.user, produit=product
        ).exists()
    else:
        product.is_favorite = False

    rat = (
        product.average_rating
        if hasattr(product, "average_rating") and product.average_rating is not None
        else (product.rating or "0")
    )

    rating = float(str(rat).replace(",", "."))

    full = int(rating)
    half = 1 if rating - full >= 0.5 else 0
    empty = 5 - full - half

    features = [f.name for f in product.features.all()]

    product_data = {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "price_primary": product.price_primary,
        "category": product.category,
        "image": product.image.url if product.image else "",
        "badge": product.current_badge,
        "current_badge": product.current_badge,
        "features": features,
        "rating": rat,
        "reviews": product.reviews_count
        if hasattr(product, "reviews_count")
        else (product.reviews or 0),
        "date_added": product.date_added,
        "long_description": product.long_description,
        "chara_entretien_list": product.chara_entretien_list,
        "price_solde": product.price_solde,
        "solde_percent": product.solde_percent,
        "image_one": product.image_one.url if product.image_one else "",
        "image_two": product.image_two.url if product.image_two else "",
        "image_three": product.image_three.url if product.image_three else "",
        "stars": {
            "full": range(full),
            "half": range(half),
            "empty": range(empty),
        },
    }

    categories = Category.objects.all()

    testimonies_qs = product.testimonies.select_related("utilisateur").order_by(
        "-date_created"
    )
    for t in testimonies_qs:
        full = int(t.rating)
        half = 1 if (t.rating - full) >= 0.5 else 0
        empty = 5 - full - half

        t.stars = {
            "full": range(full),
            "half": range(half),
            "empty": range(empty),
        }

    similar_qs = Product.objects.filter(category_fk=product.category_fk).exclude(
        pk=product.pk
    )
    similar_available_count = similar_qs.count()
    similar_products = []
    similar_products_count = 0
    similar_pks = list(similar_qs.values_list("pk", flat=True))
    sampled_pks = []
    if similar_pks:
        sample_count = min(6, len(similar_pks))
        sampled_pks = random.sample(similar_pks, sample_count)
        similar_products = list(Product.objects.filter(pk__in=sampled_pks))

    if len(similar_products) < 6:
        needed = 6 - len(similar_products)
        other_qs = Product.objects.exclude(pk=product.pk)
        if sampled_pks:
            other_qs = other_qs.exclude(pk__in=sampled_pks)
        other_pks = list(other_qs.values_list("pk", flat=True))
        if other_pks:
            add_count = min(needed, len(other_pks))
            sampled_other = random.sample(other_pks, add_count)
            additional = list(Product.objects.filter(pk__in=sampled_other))
            similar_products.extend(additional)

    similar_products_count = len(similar_products)

    return render(
        request,
        "shop/product.html",
        {
            "product": product,
            "product_data": product_data,
            "categories": categories,
            "testimonies": testimonies_qs,
            "similar_products": similar_products,
            "similar_products_count": similar_products_count,
            "similar_available_count": similar_available_count,
        },
    )
