from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.db.models import Sum
from django.contrib import messages
from shop.models import (
    Vente,
    Notification,
    Order,
    Conversation,
    Message,
)
from utils.decorators import admin_required
from datetime import timedelta
from django.db.models import F, DecimalField
from django.utils.timezone import now
from django.db.models.functions import Coalesce
from django.core.exceptions import ObjectDoesNotExist


@admin_required
def dashboard(request):
    today = now().date()
    current_month = today.month
    current_year = today.year
    notifications = Notification.objects.filter(user=request.user).order_by(
        "-created_at"
    )
    notif_count = notifications.count()

    ventes = Vente.objects.select_related("produit", "produit__category_fk")

    ventes_mois_courant = ventes.filter(
        date_achat__month=current_month, date_achat__year=current_year
    )
    ventes_mois_precedent = ventes.filter(
        date_achat__month=(current_month - 1 if current_month > 1 else 12),
        date_achat__year=(current_year if current_month > 1 else current_year - 1),
    )

    def calculate_revenue_and_profit(ventes):
        revenue = (
            ventes.aggregate(total_revenue=Sum("price_final"))["total_revenue"] or 0
        )
        profit = (
            ventes.aggregate(
                total_profit=Sum(
                    F("price_final") - F("produit__price_primary"),
                    output_field=DecimalField(),
                )
            )["total_profit"]
            or 0
        )
        return revenue, profit

    revenu_courant, profit_actuel = calculate_revenue_and_profit(ventes_mois_courant)
    revenu_precedent, profit_precedent = calculate_revenue_and_profit(
        ventes_mois_precedent
    )

    croissance_pourcentage = 0
    if profit_precedent > 0:
        croissance_pourcentage = (
            (profit_actuel - profit_precedent) / profit_precedent
        ) * 100

    ventes_aujourdhui = ventes.filter(date_achat__date=today)
    ventes_hier = ventes.filter(date_achat__date=today - timedelta(days=1))
    revenu_jour = ventes_aujourdhui.aggregate(total=Sum("price_final"))["total"] or 0
    revenu_hier = ventes_hier.aggregate(total=Sum("price_final"))["total"] or 0
    revenu_journalier_pourcentage = 0
    if revenu_hier > 0:
        revenu_journalier_pourcentage = (
            (revenu_jour - revenu_hier) / revenu_hier
        ) * 100

    habits_categories = [
        "Habits/Homme",
        "Habits/Femme",
        "Habits/Enfants",
        "Habits/Souliers",
        "Habits/Neutre",
    ]
    habits_mois_courant = ventes_mois_courant.filter(
        produit__category_fk__name__in=habits_categories
    )
    habits_mois_precedent = ventes_mois_precedent.filter(
        produit__category_fk__name__in=habits_categories
    )
    revenu_habits_courant, _ = calculate_revenue_and_profit(habits_mois_courant)
    revenu_habits_precedent, _ = calculate_revenue_and_profit(habits_mois_precedent)

    habits_pourcentage = 0
    if revenu_habits_precedent > 0:
        habits_pourcentage = (
            (revenu_habits_courant - revenu_habits_precedent) / revenu_habits_precedent
        ) * 100

    methodes_stats = (
        ventes.values("method")
        .annotate(total=Coalesce(Sum("price_final"), 0, output_field=DecimalField()))
        .order_by("method")
    )
    methods_labels = [item["method"] for item in methodes_stats]
    methods_data = [float(item["total"]) for item in methodes_stats]

    recent_ventes = ventes.order_by("-date_achat")[:5]

    if request.user.groups.filter(name="mukubwa").exists():
        orders = (
            Order.objects.select_related("user", "assigned_revendeur")
            .prefetch_related("items__product")
            .order_by("-created_at")
        )
    else:
        try:
            orders = (
                Order.objects.filter(assigned_revendeur=request.user)
                .select_related("user")
                .prefetch_related("items__product")
                .order_by("-created_at")
            )
        except ObjectDoesNotExist:
            messages.error(
                request,
                "Aucune commande trouvée pour l'utilisateur spécifié ou les données n'existent pas.",
            )
            orders = []
        except Exception as e:
            messages.error(request, f"Une erreur inattendue est survenue : {str(e)}")
            orders = []
    qs = Conversation.objects.filter(participants=request.user).order_by("-created_at")
    paginator_sms = Paginator(qs, 5)
    paginator_notif = Paginator(notifications, 5)
    paginator_order = Paginator(orders, 10)

    page_sms = request.GET.get("page_sms")
    page_notif = request.GET.get("page_notif")
    page_order = request.GET.get("page_order")

    try:
        page_obj_sms = paginator_sms.page(page_sms)
    except PageNotAnInteger:
        page_obj_sms = paginator_sms.page(1)
    except EmptyPage:
        page_obj_sms = paginator_sms.page(paginator_sms.num_pages)

    try:
        page_obj_order = paginator_order.page(page_order)
    except PageNotAnInteger:
        page_obj_order = paginator_order.page(1)
    except EmptyPage:
        page_obj_order = paginator_order.page(paginator_order.num_pages)

    try:
        page_obj_notif = paginator_notif.page(page_notif)
    except PageNotAnInteger:
        page_obj_notif = paginator_notif.page(1)
    except EmptyPage:
        page_obj_notif = paginator_notif.page(paginator_notif.num_pages)

    conversations_info = []

    for conv in page_obj_sms.object_list:
        last_msg = (
            Message.objects.filter(conversation=conv).order_by("-timestamp").first()
        )

        last_content = last_msg.content if last_msg else ""

        last_sender = last_msg.sender if last_msg else None
        last_timestamp = last_msg.timestamp if last_msg else None

        others = conv.participants.exclude(id=request.user.id)
        other = others.first() if others.exists() else None

        conversations_info.append(
            {
                "conversation": conv,
                "other": other,
                "last_content": last_content,
                "last_sender": last_sender,
                "last_timestamp": last_timestamp,
            }
        )

    context = {
        "croissance_potentielle": round(profit_actuel, 2),
        "croissance_pourcentage": round(croissance_pourcentage, 2),
        "revenu_mensuel": round(revenu_courant, 2),
        "revenu_mensuel_pourcentage": round(
            ((revenu_courant - revenu_precedent) / revenu_precedent) * 100
            if revenu_precedent > 0
            else 0,
            2,
        ),
        "revenu_quotidien": round(revenu_jour, 2),
        "revenu_quotidien_pourcentage": round(revenu_journalier_pourcentage, 2),
        "revenu_habits": round(revenu_habits_courant, 2),
        "revenu_habits_pourcentage": round(habits_pourcentage, 2),
        "total_ventes": ventes.count(),
        "recent_ventes": recent_ventes,
        "methods_labels": methods_labels,
        "methods_data": methods_data,
        "notif_count": notif_count,
        "page_obj_notif": page_obj_notif,
        "page_obj_order": page_obj_order,
        "page_obj_sms": page_obj_sms,
        "conversations_info": conversations_info,
        "paginator_sms": paginator_sms,
        "page_sms": page_sms,
        "is_paginated_sms": page_obj_sms.has_other_pages(),
        "paginator_notif": paginator_notif,
        "page_notif": page_notif,
        "is_paginated_notif": page_obj_notif.has_other_pages(),
        "paginator_order": paginator_order,
        "page_order": page_order,
        "is_paginated_order": page_obj_order.has_other_pages(),
    }
    return render(request, "gestion/dash.html", context)
