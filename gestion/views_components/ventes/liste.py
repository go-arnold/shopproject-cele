from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from shop.models import (
    Vente,
)
from utils.decorators import admin_required
from django.utils import timezone
from django.contrib.auth.models import Group
from datetime import timedelta, datetime
from django.core.exceptions import PermissionDenied


@admin_required
def liste_ventes(request):
    utilisateur = request.user
    if utilisateur.groups.filter(name="mukubwa").exists():
        ventes_list = Vente.objects.select_related("produit", "utilisateur").order_by(
            "-date_achat"
        )
    else:
        ventes_list = (
            Vente.objects.filter(utilisateur=utilisateur)
            .select_related("produit", "utilisateur")
            .order_by("-date_achat")
        )

    paginator = Paginator(ventes_list, 7)
    page_number = request.GET.get("page")
    ventes = paginator.get_page(page_number)

    return render(
        request,
        "gestion/liste_ventes.html",
        {
            "ventes": ventes,
        },
    )


@admin_required
def liste_ventes_rev(request):
    utilisateur = request.user

    rev = Group.objects.get(name="revendeur").user_set.all()
    muk = Group.objects.get(name="mukubwa").user_set.all()
    if utilisateur in rev and utilisateur not in muk:
        raise PermissionDenied()

    if utilisateur.groups.filter(name="revendeur").exists():
        return redirect("gestion:dashboard")

    if utilisateur.groups.filter(name="mukubwa").exists():
        ventes_list = Vente.objects.select_related("produit", "utilisateur").order_by(
            "-date_achat"
        )
    else:
        ventes_list = (
            Vente.objects.filter(utilisateur=utilisateur)
            .select_related("produit", "utilisateur")
            .order_by("-date_achat")
        )

    filtre = request.GET.get("filtre")
    date_achat_search = request.GET.get("date_achat")
    date_enregistrement_search = request.GET.get("date_enregistrement")
    maintenant = timezone.now()

    if filtre == "2":
        ventes_list = ventes_list.filter(date_achat__gte=maintenant - timedelta(days=2))
    elif filtre == "7":
        ventes_list = ventes_list.filter(date_achat__gte=maintenant - timedelta(days=7))
    elif filtre == "30":
        ventes_list = ventes_list.filter(
            date_achat__gte=maintenant - timedelta(days=30)
        )
    elif filtre == "90":
        ventes_list = ventes_list.filter(
            date_achat__gte=maintenant - timedelta(days=90)
        )

    if date_achat_search:
        try:
            date_obj = datetime.strptime(date_achat_search, "%Y-%m-%d")
            ventes_list = ventes_list.filter(date_achat__date=date_obj)
        except ValueError:
            pass

    if date_enregistrement_search:
        try:
            date_obj = datetime.strptime(date_enregistrement_search, "%Y-%m-%d")
            ventes_list = ventes_list.filter(date_enregistrement__date=date_obj)
        except ValueError:
            pass

    paginator = Paginator(ventes_list, 7)
    page_number = request.GET.get("page")
    ventes = paginator.get_page(page_number)

    return render(
        request,
        "gestion/liste_ventes_rev.html",
        {
            "ventes": ventes,
            "filtre": filtre,
        },
    )
