from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Permet d'accéder à une valeur de dictionnaire avec une clé variable dans les templates."""
    return dictionary.get(key, 0) if dictionary else 0
