from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.core.exceptions import PermissionDenied


def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            login_url = reverse("account_login")
            return redirect(f"{login_url}?next={request.path}")

        if not user.groups.filter(name__in=["revendeur", "mukubwa"]).exists():
            messages.error(request, "Accès réservé aux revendeurs et mukubwas.")
            # return redirect('account_login')
            raise PermissionDenied(
                "Vous n'avez pas l'autorisation d'accéder à cette page."
            )

        return view_func(request, *args, **kwargs)

    return _wrapped_view
