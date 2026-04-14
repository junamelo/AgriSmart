#!/usr/bin/env python
"""
Script pour tester l'ajout d'une réponse d'expert
"""
import os
import django
import sys

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monprojet.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from monapp.models import Expert, DemandeExpert

def ajouter_reponse_test():
    print("🧪 Test d'ajout de réponse d'expert")
    print("=" * 50)
    
    # Trouver une demande acceptée
    demande = DemandeExpert.objects.filter(statut='acceptee').first()
    
    if not demande:
        print("❌ Aucune demande acceptée trouvée")
        return
    
    print(f"📝 Ajout de réponse à la demande ID: {demande.id}")
    print(f"Sujet: {demande.sujet}")
    print(f"Expert: {demande.expert.nom_complet}")
    
    # Ajouter une réponse
    nom_agriculteur = demande.agriculteur.user.first_name or demande.agriculteur.user.username or 'Cher agriculteur'
    
    reponse_text = f"""Bonjour {nom_agriculteur},

Merci pour votre question concernant "{demande.sujet}".

Après analyse de votre description, voici mes recommandations :

🔍 **Diagnostic** :
D'après les éléments que vous avez fournis, il s'agit d'un problème que nous rencontrons fréquemment dans le domaine de {demande.get_domaine_demande_display().lower()}.

💡 **Solutions recommandées** :

1. **Action immédiate** : 
   - Surveillez attentivement l'évolution quotidienne
   - Prenez des photos pour documenter l'évolution
   - Évitez toute intervention hasardeuse

2. **Stratégie à moyen terme** :
   - Mise en place d'un suivi préventif
   - Ajustement des pratiques actuelles
   - Formation aux bonnes pratiques

3. **Suivi recommandé** :
   - Observation hebdomadaire
   - Tenir un registre détaillé
   - Me contacter en cas d'aggravation

📞 **Contact** :
N'hésitez pas à me recontacter si vous avez besoin de précisions ou si la situation évolue.

Cordialement,
{demande.expert.nom_complet}
Expert en {demande.get_domaine_demande_display()}
AgriSmart - Plateforme d'Appui Conseil

---
Réponse générée le {timezone.now().strftime('%d/%m/%Y à %H:%M')}"""
    
    # Appliquer la réponse
    demande.reponse = reponse_text
    demande.date_reponse = timezone.now()
    demande.statut = 'terminee'  # Marquer comme terminée
    demande.save()
    
    print("✅ Réponse ajoutée avec succès !")
    print(f"📅 Date de réponse: {demande.date_reponse}")
    print(f"📊 Nouveau statut: {demande.get_statut_display()}")
    print(f"📝 Longueur de la réponse: {len(reponse_text)} caractères")
    
    # Vérification
    demande.refresh_from_db()
    print(f"\n🔍 Vérification:")
    print(f"   Réponse présente: {'✅' if demande.a_reponse else '❌'}")
    print(f"   Date réponse: {demande.date_reponse}")
    print(f"   Statut: {demande.get_statut_display()}")
    
    return demande

if __name__ == '__main__':
    demande_repondue = ajouter_reponse_test()
    if demande_repondue:
        print(f"\n🎯 Test réussi ! Demande ID {demande_repondue.id} a maintenant une réponse.")
