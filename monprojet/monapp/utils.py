from django.core.cache import cache
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
import hashlib

def get_user_role(user):
    """Détermine le rôle d'un utilisateur"""
    if not user.is_authenticated:
        return None
    
    from .models import Agriculteur, Expert

    try:
        user.agriculteur
        return 'agriculteur'
    except Agriculteur.DoesNotExist:
        pass

    try:
        user.expert
        return 'expert'
    except Expert.DoesNotExist:
        pass
    
    return None

def get_user_dashboard_url(user):
    """Retourne l'URL du tableau de bord approprié selon le rôle"""
    role = get_user_role(user)
    
    if role == 'agriculteur':
        return 'monapp:compte'
    elif role == 'expert':
        return 'monapp:expert_dashboard'
    else:
        return 'monapp:index'

def is_agriculteur(user):
    """Vérifie si l'utilisateur est un agriculteur"""
    return get_user_role(user) == 'agriculteur'

def is_expert(user):
    """Vérifie si l'utilisateur est un expert"""
    return get_user_role(user) == 'expert'

class LoginAttemptLimiter:
    """Limitateur de tentatives de connexion"""
    
    def __init__(self, max_attempts=5, lockout_duration=15):
        self.max_attempts = max_attempts
        self.lockout_duration = lockout_duration  # minutes
    
    def get_cache_key(self, identifier):
        """Génère une clé de cache pour l'identifiant"""
        hash_id = hashlib.md5(identifier.encode()).hexdigest()
        return f"login_attempts_{hash_id}"
    
    def is_locked(self, identifier):
        """Vérifie si l'identifiant est verrouillé"""
        cache_key = self.get_cache_key(identifier)
        attempts_data = cache.get(cache_key, {'count': 0, 'locked_until': None})
        
        if attempts_data.get('locked_until'):
            if timezone.now() < attempts_data['locked_until']:
                return True
            else:
                # Le verrouillage a expiré, réinitialiser
                cache.delete(cache_key)
                return False
        return False
    
    def record_failed_attempt(self, identifier):
        """Enregistre une tentative échouée"""
        cache_key = self.get_cache_key(identifier)
        attempts_data = cache.get(cache_key, {'count': 0, 'locked_until': None})
        
        attempts_data['count'] += 1
        
        if attempts_data['count'] >= self.max_attempts:
            attempts_data['locked_until'] = timezone.now() + timedelta(minutes=self.lockout_duration)
            # Cache pour la durée du verrouillage
            cache.set(cache_key, attempts_data, timeout=self.lockout_duration * 60)
        else:
            # Cache pour 1 heure
            cache.set(cache_key, attempts_data, timeout=3600)
    
    def record_successful_attempt(self, identifier):
        """Réinitialise le compteur après une connexion réussie"""
        cache_key = self.get_cache_key(identifier)
        cache.delete(cache_key)
    
    def get_remaining_attempts(self, identifier):
        """Retourne le nombre de tentatives restantes"""
        cache_key = self.get_cache_key(identifier)
        attempts_data = cache.get(cache_key, {'count': 0})
        return max(0, self.max_attempts - attempts_data['count'])

def get_client_ip(request):
    """Récupère l'adresse IP du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def validate_file_upload(file, max_size_mb=5, allowed_types=None):
    """Valide un fichier uploadé"""
    if allowed_types is None:
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    
    errors = []
    
    if file.size > max_size_mb * 1024 * 1024:
        errors.append(f"Le fichier ne peut pas dépasser {max_size_mb}MB.")
    
    if file.content_type not in allowed_types:
        errors.append("Type de fichier non autorisé. Utilisez JPEG, PNG, GIF ou WebP.")
    
    return errors

def sanitize_input(input_string):
    """Nettoie une chaîne d'entrée"""
    if not input_string:
        return ""
    
    # Supprimer les espaces en début/fin
    cleaned = input_string.strip()
    
    # Remplacer les caractères de contrôle
    cleaned = ''.join(char for char in cleaned if ord(char) >= 32 or char in '\t\n\r')
    
    return cleaned
