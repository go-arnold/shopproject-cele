from django.shortcuts import render
from django.contrib.auth import get_user_model
from utils.decorators import admin_required
from django.contrib.auth.models import Group
from django.core.paginator import Paginator


User = get_user_model()


@admin_required
def inscriptions_par_revendeur(request):
    try:
        revendeur_group = Group.objects.get(name="revendeur")
        revs = revendeur_group.user_set.all().order_by("date_joined")
    except Group.DoesNotExist:
        revs = []

    paginator = Paginator(revs, 20)
    page_number = request.GET.get("page")
    revendeurs = paginator.get_page(page_number)

    context = {"revendeurs": revendeurs}

    return render(request, "gestion/invites.html", context)
