#!/usr/bin/env python
"""
Script de test pour vérifier le système de communication expert-agriculteur
"""
import os
import django
import sys

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monprojet.settings')
django.setup()

from django.contrib.auth.models import User
from monapp.models import Expert, DemandeExpert

def test_response_system():
    print("🔍 Test du système de réponses expert-agriculteur")
    print("=" * 60)
    
    # Vérifier les demandes existantes
    demandes = DemandeExpert.objects.all()
    print(f"📊 Nombre total de demandes: {demandes.count()}")
    
    # Vérifier les demandes avec réponses
    demandes_avec_reponse = DemandeExpert.objects.exclude(reponse='').exclude(reponse__isnull=True)
    print(f"💬 Demandes avec réponse: {demandes_avec_reponse.count()}")
    
    # Vérifier les demandes avec évaluation
    demandes_evaluees = DemandeExpert.objects.filter(note_satisfaction__isnull=False)
    print(f"⭐ Demandes évaluées: {demandes_evaluees.count()}")
    
    print("\n📋 Détail des demandes:")
    print("-" * 40)
    
    for demande in demandes.order_by('-date_creation')[:5]:
        print(f"\nID: {demande.id}")
        print(f"Sujet: {demande.sujet}")
        print(f"Statut: {demande.statut}")
        print(f"Expert: {demande.expert.nom_complet if demande.expert else 'Non assigné'}")
        print(f"Réponse: {'✅ Oui' if demande.reponse and demande.reponse.strip() else '❌ Non'}")
        if demande.reponse:
            print(f"Date réponse: {demande.date_reponse}")
        print(f"Évaluation: {'✅ ' + str(demande.note_satisfaction) + '/5' if demande.note_satisfaction else '❌ Non'}")
        if demande.note_satisfaction and demande.commentaire_satisfaction:
            print(f"Commentaire: {demande.commentaire_satisfaction[:50]}...")
    
    # Test de création d'une réponse
    print(f"\n🧪 Test de création d'une réponse")
    print("-" * 40)
    
    # Trouver une demande acceptée sans réponse
    demande_test = DemandeExpert.objects.filter(
        statut='acceptee',
        reponse=''
    ).first()
    
    if not demande_test:
        demande_test = DemandeExpert.objects.filter(
            statut='acceptee'
        ).first()
    
    if demande_test:
        print(f"📝 Test sur la demande ID: {demande_test.id}")
        
        # Simuler une réponse d'expert
        response_text = """Bonjour,

Merci pour votre question concernant {sujet}.

Voici mes recommandations :

1. **Analyse de la situation** : D'après votre description, il semble que vous rencontriez un problème classique dans votre domaine.

2. **Solutions recommandées** :
   - Solution immédiate : [Action à court terme]
   - Solution à moyen terme : [Stratégie préventive]
   - Suivi recommandé : [Monitoring continu]

3. **Conseils pratiques** :
   - Surveillez l'évolution quotidiennement
   - Tenez un registre des observations
   - N'hésitez pas à me recontacter si nécessaire

Cordialement,
Expert AgriSmart""".format(sujet=demande_test.sujet)
        
        print(f"✅ Réponse simulée préparée ({len(response_text)} caractères)")
        
        # Optionnel : appliquer la réponse (décommentez pour tester)
        # demande_test.reponse = response_text
        # demande_test.statut = 'terminee'
        # from django.utils import timezone
        # demande_test.date_reponse = timezone.now()
        # demande_test.save()
        # print("✅ Réponse appliquée avec succès")
        
    else:
        print("❌ Aucune demande acceptée sans réponse trouvée")
    
    # Vérifier la structure de la base de données
    print(f"\n🏗️ Vérification de la structure")
    print("-" * 40)
    
    # Vérifier les nouveaux champs
    sample_demande = DemandeExpert.objects.first()
    if sample_demande:
        fields_to_check = ['date_reponse', 'note_satisfaction', 'commentaire_satisfaction']
        for field in fields_to_check:
            if hasattr(sample_demande, field):
                print(f"✅ Champ '{field}' présent")
            else:
                print(f"❌ Champ '{field}' manquant")
    
    # Statistiques finales
    print(f"\n📈 Statistiques du système")
    print("-" * 40)
    print(f"👥 Experts actifs: {Expert.objects.count()}")
    print(f"👨‍🌾 Utilisateurs: {User.objects.count()}")
    print(f"📝 Demandes totales: {demandes.count()}")
    print(f"✅ Taux de réponse: {(demandes_avec_reponse.count() / demandes.count() * 100):.1f}%" if demandes.count() > 0 else "N/A")
    print(f"⭐ Taux d'évaluation: {(demandes_evaluees.count() / demandes.count() * 100):.1f}%" if demandes.count() > 0 else "N/A")
    
    print(f"\n🎯 Test terminé avec succès !")

if __name__ == '__main__':
    test_response_system()
