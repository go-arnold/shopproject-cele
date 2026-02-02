from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib import messages
from shop.models import (
    Product,
    Vente,
)
from utils.decorators import admin_required


@admin_required
def ajouter_vente(request):
    if request.method == "POST":
        try:
            produit_id = request.POST.get("produit_id")
            date_achat = request.POST.get("date_achat")
            price_final = request.POST.get("price_final") or None
            method = request.POST.get("method", "Cash")

            produit = Product.objects.get(id=produit_id)

            vente = Vente.objects.create(
                utilisateur=request.user,
                produit=produit,
                date_achat=date_achat,
                price_final=price_final,
                method=method,
            )

            messages.success(
                request, f'Vente du produit "{produit.name}" enregistrée avec succès.'
            )
            return redirect("gestion:dashboard")

        except Product.DoesNotExist:
            messages.error(request, "Produit introuvable.")
        except Exception as e:
            messages.error(request, f"Erreur : {str(e)}")

    context = {
        "methods": Vente.METHODS_CHOICES,
        "produits": Product.objects.all(),
    }
    return render(request, "gestion/ajouter_vente.html", context)
