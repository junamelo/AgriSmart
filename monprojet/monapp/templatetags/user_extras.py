from django import template
from ..utils import get_user_role, is_agriculteur, is_expert

register = template.Library()

@register.filter
def user_role(user):
    """Retourne le rôle de l'utilisateur"""
    return get_user_role(user)

@register.filter
def is_user_agriculteur(user):
    """Vérifie si l'utilisateur est un agriculteur"""
    return is_agriculteur(user)

@register.filter
def is_user_expert(user):
    """Vérifie si l'utilisateur est un expert"""
    return is_expert(user)
