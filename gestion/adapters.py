from allauth.account.adapter import DefaultAccountAdapter
from django.shortcuts import resolve_url

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
