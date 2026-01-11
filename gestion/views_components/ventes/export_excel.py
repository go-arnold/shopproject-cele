from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.db.models.functions import TruncMonth, TruncDay
import json
from django.shortcuts import render
from django.db.models import Count, Sum
import tempfile
from weasyprint import HTML
from django.template.loader import render_to_string
from django.http import HttpResponse
import openpyxl
from django.utils import timezone
from django.contrib.auth.models import Group
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from shop.models import (
    Product,
    Feature,
    Category,
    Vente,
    Notification,
    Order,
    Conversation,
    Message,
)
from utils.decorators import admin_required
from django.http import JsonResponse
from datetime import timedelta, datetime
from django.db.models import F, DecimalField
from django.utils.timezone import now
from django.db.models.functions import Coalesce
from django.templatetags.static import static
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied


@admin_required
def export_ventes_excel(request):
    utilisateur = request.user
    user = request.user
    rev = Group.objects.get(name="revendeur").user_set.all()
    muk = Group.objects.get(name="mukubwa").user_set.all()
    if user in rev and user not in muk:
        raise PermissionDenied()
    if utilisateur.groups.filter(name="mukubwa").exists():
        ventes = Vente.objects.select_related("produit", "utilisateur")
    else:
        ventes = Vente.objects.filter(utilisateur=utilisateur).select_related(
            "produit", "utilisateur"
        )

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ventes"

    ws.append(["Produit", "Utilisateur", "Prix", "Méthode", "Date"])

    for v in ventes:
        ws.append(
            [
                v.produit_nom,
                v.utilisateur.username,
                float(v.price_final or v.produit_prix),
                v.method,
                v.date_achat.strftime("%Y-%m-%d %H:%M"),
            ]
        )

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="ventes.xlsx"'
    wb.save(response)

    return response
