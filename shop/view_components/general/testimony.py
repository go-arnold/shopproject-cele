from django.shortcuts import get_object_or_404, redirect
from shop.models import Product
from django.db import transaction
from shop.models import Testimony
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def add_testimony(request, pk):
    """Reçoit un POST depuis le formulaire produit et crée un `Testimony`.

    - Requiert une session utilisateur (redirige vers login si non connecté).
    - Attend `rating` et `message` dans `request.POST`.
    - Redirige vers la page produit après création.
    """
    product = get_object_or_404(Product, pk=pk)
    if request.method != "POST":
        return redirect("product_detail", pk=product.pk)

    rating = request.POST.get("rating")
    message = request.POST.get("message", "").strip()

    if not message:
        return redirect("product_detail", pk=product.pk)

    try:
        rating_val = int(rating)
    except (TypeError, ValueError):
        rating_val = 5

    rating_val = max(1, min(5, rating_val))
    with transaction.atomic():
        Testimony.objects.filter(product=product, utilisateur=request.user).delete()
        Testimony.objects.create(
            product=product,
            utilisateur=request.user,
            rating=rating_val,
            message=message,
        )

    return redirect("product_detail", pk=product.pk)
