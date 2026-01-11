from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction


@login_required
def updateInfo(request):
    if request.method == "POST":
        form_type = request.POST.get("form_type")

        try:
            user = request.user
            profile = user.profile

            if form_type == "personal_info":
                user.first_name = request.POST.get("first_name", "").strip()
                user.last_name = request.POST.get("last_name", "").strip()
                user.profile.phone_number = request.POST.get(
                    "phone", "").strip()

                if "profile_image" in request.FILES:
                    profile.image = request.FILES["profile_image"]

                user.save()
                profile.save()

                messages.success(request, "Informations mises à jour.")
                return redirect("profile")

            if form_type == "addresses":
                profile.def_address = request.POST.get(
                    "delivery_address_line1", "")
                profile.def_quarter_town = request.POST.get(
                    "delivery_address_line2", "")
                profile.def_country = request.POST.get(
                    "delivery_address_country", "")

                if request.POST.get("same_as_delivery"):
                    profile.deliv_address = profile.def_address
                    profile.deliv_quarter_town = profile.def_quarter_town
                    profile.deliv_country = profile.def_country
                else:
                    profile.deliv_address = request.POST.get(
                        "billing_address_line1", "")
                    profile.deliv_quarter_town = request.POST.get(
                        "billing_address_line2", "")
                    profile.deliv_country = request.POST.get(
                        "billing_address_country", "")

                profile.save()

                messages.success(request, "Adresses mises à jour.")
                return redirect("profile")

        except Exception as e:
            messages.error(request, str(e))
            return redirect("profile")

    return render(request, "shop/profile.html")
