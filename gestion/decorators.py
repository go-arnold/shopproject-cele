from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

def admin_required(view_func):
    """
    Décorateur pour restreindre l'accès aux utilisateurs du groupe 'revendeur' ou 'mukubwa'.
    Redirige vers login si non connecté, sinon vers une page d'accès refusé.
    """
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:            
            login_url = reverse('account_login')  
            return redirect(f"{login_url}?next={request.path}")

        if not user.groups.filter(name__in=['revendeur', 'mukubwa']).exists():
            messages.error(request, "Accès réservé aux revendeurs et mukubwas.")
            return redirect('account_login')  # ou je vais ajouter une page d'accès refusé 403 plus tard
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view
