from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth import get_user_model
from django.shortcuts import resolve_url
from .models import Profile

User = get_user_model()


class MyAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        """
        Redirige après connexion selon le groupe de l'utilisateur.
        """
        user = request.user
        if user.is_authenticated:
            if user.groups.filter(name__in=['revendeur', 'mukubwa']).exists():
                return resolve_url('/cele-admin/')

        return resolve_url('/')

    def get_user_by_phone(self, phone):
        """
        Return (phone, verified) tuple if phone exists, else None.
        """
        try:
            profile = Profile.objects.select_related(
                "user").get(phone_number=phone)
            return profile.phone_number, True
        except Profile.DoesNotExist:
            return None

    def get_phone(self, user):
        if hasattr(user, "profile"):
            return getattr(user.profile, "phone_number", None)
        return None

    def set_phone(self, user, phone):
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.phone_number = phone
        profile.save(update_fields=["phone_number"])
