from django.shortcuts import render
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from shop.models import (
    Product,
    Vente,
)
from utils.decorators import admin_required
from django.core.exceptions import PermissionDenied


@admin_required
def modifier_vente(request, vente_id):
    vente = get_object_or_404(Vente, id=vente_id)
    produits = Product.objects.all()
    if not request.user.groups.filter(name="mukubwa").exists():
        raise PermissionDenied()

    if request.method == "POST":
        produit_id = request.POST.get("produit_id")
        price_final = request.POST.get("price_final")
        method = request.POST.get("method")
        date_achat = request.POST.get("date_achat")

        if produit_id:
            vente.produit_id = produit_id
        vente.price_final = price_final or vente.produit.price
        vente.method = method
        vente.date_achat = date_achat
        vente.save()

        messages.success(request, "La vente a été modifiée avec succès.")
        return redirect("gestion:liste_ventes")

    return render(
        request,
        "gestion/modifier_vente.html",
        {
            "vente": vente,
            "produits": produits,
            "methods": Vente.METHODS_CHOICES,
        },
    )
