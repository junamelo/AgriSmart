import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monprojet.settings')
django.setup()

from monapp.models import TypeCulture
from django.db import IntegrityError

print("Test de la contrainte d'unicité sur le champ 'nom' de TypeCulture...")

try:
    # Essayer de créer un doublon de "Maïs"
    TypeCulture.objects.create(nom='Maïs', description='Test doublon')
    print("❌ ERREUR: Le doublon a été créé!")
except IntegrityError as e:
    print("✅ SUCCESS: La contrainte d'unicité fonctionne correctement!")
    print(f"   Détail de l'erreur: {e}")

# Afficher les cultures existantes
print("\nCultures existantes dans la base:")
for culture in TypeCulture.objects.all():
    print(f"  - {culture.nom}")
