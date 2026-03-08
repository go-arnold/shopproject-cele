from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from accounts.models import Profile
from shop.models import Order

User = get_user_model()


@login_required
def updateInfo(request):
    # num_invited = User.objects.filter(profile__invited_by = request.user).count()
    # num_invited = Profile.objects.filter(invited_by = request.user).count()

    num_invited = request.user.revendeur.count()

    if request.method == "POST":
        form_type = request.POST.get("form_type")
        try:
            user = request.user
            profile = user.profile
            if form_type == "personal_info":
                user.first_name = request.POST.get("first_name", "").strip()
                user.last_name = request.POST.get("last_name", "").strip()
                user.profile.phone_number = request.POST.get("phone", "").strip()
                code_revendeur = request.POST.get("revendeur_code", "").strip()
                try:
                    revendeur = User.objects.get(profile__code_revendeur=code_revendeur)
                    user.invited_by = revendeur
                except User.DoesNotExist:
                    messages.error(
                        request,
                        "Aucun revendeur trouvé avec le code que vous avez entré",
                    )
                    return redirect("profile")

                if "profile_image" in request.FILES:
                    profile.image = request.FILES["profile_image"]

                user.save()
                profile.save()

                messages.success(request, "Informations mises à jour.")
                return redirect("profile")

            if form_type == "addresses":
                profile.def_address = request.POST.get("delivery_address_line1", "")
                profile.def_quarter_town = request.POST.get(
                    "delivery_address_line2", ""
                )
                profile.def_country = request.POST.get("delivery_address_country", "")

                if request.POST.get("same_as_delivery"):
                    profile.deliv_address = profile.def_address
                    profile.deliv_quarter_town = profile.def_quarter_town
                    profile.deliv_country = profile.def_country
                else:
                    profile.deliv_address = request.POST.get(
                        "billing_address_line1", ""
                    )
                    profile.deliv_quarter_town = request.POST.get(
                        "billing_address_line2", ""
                    )
                    profile.deliv_country = request.POST.get(
                        "billing_address_country", ""
                    )

                profile.save()

                messages.success(request, "Adresses mises à jour.")
                return redirect("profile")

        except Exception as e:
            messages.error(request, str(e))
            return redirect("profile")

    return render(request, "shop/profile.html", {"num_invited": num_invited})


@login_required
def order_history(request):
    status_filter = request.GET.get('status')
    
    orders_queryset = Order.objects.select_related(
        "user", "assigned_revendeur"
    ).prefetch_related(
        "items__product", "conversations"
    ).order_by("-created_at")

    if status_filter and status_filter != 'all':
        orders_queryset = orders_queryset.filter(status__iexact=status_filter)

    orders = orders_queryset[:25]

    context = {
        "orders": orders,
        "current_status": status_filter or 'all'
    }
    return render(request, "shop/order_history.html", context)