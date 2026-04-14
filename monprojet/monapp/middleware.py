from django.shortcuts import redirect
from django.urls import reverse
from django.core.exceptions import ImproperlyConfigured
from django.urls.exceptions import NoReverseMatch

class AuthRedirectMiddleware:
    """Middleware pour rediriger les utilisateurs non connectés vers la page d'authentification"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Pages nécessitant une authentification
        try:
            protected_paths = [
                reverse('monapp:compte'),
                reverse('monapp:add_activite'),
                reverse('monapp:edit_activite'),
                reverse('monapp:delete_activite'),
            ]
            
            # Si l'utilisateur n'est pas connecté et essaie d'accéder à une page protégée
            if not request.user.is_authenticated and request.path in protected_paths:
                return redirect(f"{reverse('monapp:auth')}?next={request.path}")
        except (NoReverseMatch, ImproperlyConfigured):
            # En cas d'erreur avec les URLs (pendant le démarrage), on ignore
            pass
        
        response = self.get_response(request)
        return response