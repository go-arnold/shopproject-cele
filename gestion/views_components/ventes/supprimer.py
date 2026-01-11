from django.shortcuts import render
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from shop.models import (
    Vente,
)
from utils.decorators import admin_required


@admin_required
def supprimer_vente(request, vente_id):
    vente = get_object_or_404(Vente, id=vente_id)

    if request.method == "POST":
        vente.delete()
        messages.success(request, "La vente a été supprimée avec succès.")
        return redirect("gestion:liste_ventes")

    return render(request, "gestion/supprimer_vente.html", {"vente": vente})
