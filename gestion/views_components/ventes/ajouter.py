from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib import messages
from shop.models import (
    Product,
    Vente,
    Order,
)
from utils.decorators import admin_required

from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.db.models import Q


User = get_user_model()


User = get_user_model()


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


@admin_required
def bulk_enregistrer_vente(request):
    if request.method == "POST":
        try:
            order_id = request.POST.get("order_id")
            method = request.POST.get("method", "Cash")
            date_achat = request.POST.get("date_achat")
            vendu_a = request.POST.get("vendu_a", "")

            order = Order.objects.prefetch_related("items__product").get(id=order_id)

            ventes_creees = 0
            for item in order.items.all():
                price_final_key = f"price_final_{item.id}"
                price_final = request.POST.get(price_final_key) or item.unit_price

                for _ in range(item.quantity):
                    Vente.objects.create(
                        utilisateur=request.user,
                        produit=item.product,
                        date_achat=date_achat,
                        price_final=price_final,
                        method=method,
                        vendu_a=vendu_a,
                    )
                    ventes_creees += 1

            order.status = "terminé"
            order.save()

            messages.success(
                request,
                f"{ventes_creees} vente(s) enregistrée(s) avec succès pour la commande #{order.id}.",
            )
            return redirect("gestion:dashboard")

        except Order.DoesNotExist:
            messages.error(request, "Commande introuvable.")
        except Exception as e:
            messages.error(request, f"Erreur : {str(e)}")

    context = {
        "methods": Vente.METHODS_CHOICES,
    }
    return render(request, "gestion/ajouter_commande.html", context)


@admin_required
def search_orders_by_user(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"orders": []})

    users = User.objects.filter(
        Q(username__icontains=query)
        | Q(first_name__icontains=query)
        | Q(last_name__icontains=query)
        | Q(email__icontains=query)
    )

    orders_data = []
    for user in users:
        user_orders = (
            Order.objects.filter(user=user)
            .prefetch_related("items__product")
            .order_by("-created_at")[:10]
        )
        for order in user_orders:
            items = []
            for item in order.items.all():
                items.append(
                    {
                        "id": item.id,
                        "product_name": item.product.name if item.product else "—",
                        "quantity": item.quantity,
                        "unit_price": str(item.unit_price),
                    }
                )
            orders_data.append(
                {
                    "id": order.id,
                    "user_display": user.get_full_name() or user.username,
                    "user_email": user.email,
                    "total_price": str(order.total_price),
                    "status": order.get_status_display(),
                    "created_at": order.created_at.strftime("%d/%m/%Y à %H:%M"),
                    "items": items,
                }
            )

    return JsonResponse({"orders": orders_data})
