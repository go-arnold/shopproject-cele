from allauth.account.adapter import DefaultAccountAdapter
from django.shortcuts import resolve_url
from django.contrib.auth import get_user_model
from accounts.models import Profile

User = get_user_model()


class CustomAccountAdapter(DefaultAccountAdapter):
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
        try:
            profile = Profile.objects.select_related("user").get(
                phone_number=phone
            )
            return profile.user
        except Profile.DoesNotExist:
            return None

    def set_phone(self, user, phone):
        """
        Save the phone number on the user's profile.
        REQUIRED when using ACCOUNT_SIGNUP_FIELDS with phone.
        """
        profile = user.profile
        profile.phone_number = phone
        profile.save(update_fields=["phone_number"])

    def get_phone(self, user):
        """
        Return the phone number for the user.
        """
        return getattr(user.profile, "phone_number", None)
