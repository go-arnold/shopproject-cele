from django.db.models.functions import TruncMonth, TruncDay
import json
from django.shortcuts import render
from django.db.models import Count, Sum
from django.utils import timezone
from django.contrib.auth.models import Group
from django.shortcuts import redirect
from shop.models import (
    Vente,
)
from utils.decorators import admin_required
from datetime import timedelta
from django.core.exceptions import PermissionDenied


@admin_required
def dashboard_ventes(request):
    user = request.user
    rev = Group.objects.get(name="revendeur").user_set.all()
    muk = Group.objects.get(name="mukubwa").user_set.all()
    if user in rev and user not in muk:
        raise PermissionDenied()
    utilisateur = request.user
    today = timezone.now()
    if utilisateur.groups.filter(name="revendeur").exists():
        return redirect("gestion:dashboard")

    if utilisateur.groups.filter(name="mukubwa").exists():
        ventes = Vente.objects.all().select_related("produit", "utilisateur")
    else:
        ventes = Vente.objects.filter(utilisateur=utilisateur).select_related(
            "produit", "utilisateur"
        )

    last_week = today - timedelta(days=7)
    last_year = today - timedelta(days=365)

    ventes_7j = (
        ventes.filter(date_achat__gte=last_week)
        .annotate(day=TruncDay("date_achat"))
        .values("day")
        .annotate(total=Count("id"))
        .order_by("day")
    )

    ventes_7j = [
        {"day": item["day"].strftime("%Y-%m-%d"), "total": item["total"]}
        for item in ventes_7j
    ]

    ca_mensuel = (
        ventes.filter(date_achat__gte=last_year)
        .annotate(month=TruncMonth("date_achat"))
        .values("month")
        .annotate(total=Sum("price_final"))
        .order_by("month")
    )

    ca_mensuel = [
        {
            "month": item["month"].strftime("%Y-%m"),
            "total": float(item["total"]) if item["total"] else 0,
        }
        for item in ca_mensuel
    ]

    methode_repartition = (
        ventes.values("method").annotate(total=Count("id")).order_by("-total")
    )

    methode_repartition = [
        {"method": row["method"], "total": row["total"]} for row in methode_repartition
    ]

    top_produits = (
        ventes.values("produit__name")
        .annotate(total=Count("id"))
        .order_by("-total")[:10]
    )

    top_produits = [
        {"produit": row["produit__name"], "total": row["total"]} for row in top_produits
    ]

    ventes_par_revendeur = (
        ventes.values("utilisateur__username")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    ventes_par_revendeur = [
        {"revendeur": row["utilisateur__username"], "total": row["total"]}
        for row in ventes_par_revendeur
    ]

    ca_par_revendeur = (
        ventes.values("utilisateur__username")
        .annotate(ca_total=Sum("price_final"))
        .order_by("-ca_total")
    )

    ca_par_revendeur = [
        {
            "revendeur": row["utilisateur__username"],
            "total": float(row["ca_total"]) if row["ca_total"] else 0.0,
        }
        for row in ca_par_revendeur
    ]

    habits_categories = [
        "Habits/Homme",
        "Habits/Femme",
        "Habits/Enfants",
        "Habits/Souliers",
        "Habits/Neutre",
    ]

    ventes_habillement = (
        ventes.filter(produit__category_fk__name__in=habits_categories)
        .filter(date_achat__gte=last_week)
        .annotate(day=TruncDay("date_achat"))
        .values("day")
        .annotate(total=Sum("price_final"))
        .order_by("day")
    )

    ventes_habillement = [
        {"day": item["day"].strftime("%Y-%m-%d"), "total": float(item["total"])}
        for item in ventes_habillement
    ]

    context = {
        "ventes_7j": json.dumps(ventes_7j),
        "ca_mensuel": json.dumps(ca_mensuel),
        "methode_repartition": json.dumps(methode_repartition),
        "top_produits": json.dumps(top_produits),
        "ventes_par_revendeur": json.dumps(ventes_par_revendeur),
        "ca_par_revendeur": json.dumps(ca_par_revendeur),
        "ventes_habillement": json.dumps(ventes_habillement),
    }

    return render(request, "gestion/graphs.html", context)
