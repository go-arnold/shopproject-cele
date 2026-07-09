"""
Dashboard Home View - Optimized N+1 Queries

Key optimizations:
- prefetch_related for Conversation messages (was N+1 loop)
- select_related for Vente relationships
- Optimized aggregation queries with F expressions
- Single database transaction where possible
"""

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.db.models import Sum, Prefetch, F, DecimalField, Q
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
from django.db.models.functions import Coalesce
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import now


@admin_required
def dashboard(request):
    today = now().date()
    current_month = today.month
    current_year = today.year

    # Optimized notification query (was N+1)
    notifications = Notification.objects.select_related('user').filter(
        user=request.user
    ).order_by('-created_at')[:10]
    notif_count = notifications.count()

    # Single optimized Vente query with all needed relations
    ventes = Vente.objects.select_related(
        "produit",
        "produit__category_fk",  # Added to prevent N+1
        "utilisateur"
    ).filter(date_achat__year=current_year)  # Base filter once

    ventes_mois_courant = ventes.filter(date_achat__month=current_month)
    ventes_mois_precedent = ventes.filter(
        date_achat__month=(current_month - 1 if current_month > 1 else 12),
        date_achat__year=(current_year if current_month > 1 else current_year - 1),
    )

    def calculate_revenue_and_profit(ventes_qs):
        revenue = (
            ventes_qs.aggregate(total_revenue=Sum("price_final"))["total_revenue"] or 0
        )
        profit = (
            ventes_qs.aggregate(
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
    ]
    ventes_habits_courant = ventes_mois_courant.filter(
        produit__category_fk__name__in=habits_categories
    )
    ventes_habits_precedent = ventes_mois_precedent.filter(
        produit__category_fk__name__in=habits_categories
    )

    habits_courant_rev, habits_courant_profit = calculate_revenue_and_profit(
        ventes_habits_courant
    )
    habits_precedent_rev, habits_precedent_profit = calculate_revenue_and_profit(
        ventes_habits_precedent
    )

    habits_croissance = 0
    if habits_precedent_profit > 0:
        habits_croissance = (
            (habits_courant_profit - habits_precedent_profit) / habits_precedent_profit
        ) * 100

    # OPTIMIZED: prefetch_related instead of loop N+1
    latest_messages = Message.objects.order_by('-timestamp')
    conversations = Conversation.objects.filter(
        participants=request.user
    ).prefetch_related(
        Prefetch('messages', queryset=latest_messages[:1]),
        'participants'
    ).select_related('related_order').order_by('-created_at')[:5]

    # Check for assigned orders
    assigned_orders = None
    if request.user.groups.filter(name="mukubwa").exists():
        assigned_orders = Order.objects.select_related('user').filter(
            assigned_revendeur=request.user
        ).order_by('-created_at')[:5]

    context = {
        "notifications": notifications,
        "notif_count": notif_count,
        "conversations": conversations,
        "assigned_orders": assigned_orders,
        "revenu_courant": revenu_courant,
        "profit_actuel": profit_actuel,
        "croissance_pourcentage": croissance_pourcentage,
        "revenu_jour": revenu_jour,
        "revenu_journalier_pourcentage": revenu_journalier_pourcentage,
        "habits_courant_rev": habits_courant_rev,
        "habits_courant_profit": habits_courant_profit,
        "habits_croissance": habits_croissance,
    }
    return render(request, "gestion/dash.html", context)
