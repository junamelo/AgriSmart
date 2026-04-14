#!/usr/bin/env python
"""
Script de test pour vérifier la correction du problème d'acceptation des demandes d'experts
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monprojet.settings')
django.setup()

from monapp.models import DemandeExpert, Expert
from django.contrib.auth.models import User

def test_expert_fix():
    print("🔍 Test de la correction du problème d'acceptation des demandes")
    print("=" * 60)
    
    # 1. État général
    total_demandes = DemandeExpert.objects.count()
    demandes_sans_expert = DemandeExpert.objects.filter(expert__isnull=True).count()
    demandes_avec_expert = DemandeExpert.objects.filter(expert__isnull=False).count()
    
    print(f"📊 État général :")
    print(f"   Total demandes: {total_demandes}")
    print(f"   Sans expert: {demandes_sans_expert}")
    print(f"   Avec expert: {demandes_avec_expert}")
    print()
    
    # 2. Demandes par statut
    print("📋 Demandes par statut :")
    statuts = ['en_attente', 'acceptee', 'en_cours', 'terminee', 'refusee']
    for statut in statuts:
        count = DemandeExpert.objects.filter(statut=statut).count()
        print(f"   {statut}: {count}")
    print()
    
    # 3. Test de cas spécifiques
    expert = Expert.objects.first()
    if expert:
        print(f"🧑‍💼 Expert test: {expert.nom_complet}")
        
        # Demandes assignées à cet expert en attente
        demandes_assignees_attente = DemandeExpert.objects.filter(
            expert=expert, 
            statut='en_attente'
        )
        print(f"   Demandes assignées en attente: {demandes_assignees_attente.count()}")
        
        # Demandes sans expert dans son domaine
        demandes_disponibles = DemandeExpert.objects.filter(
            expert__isnull=True,
            statut='en_attente',
            domaine_demande=expert.domaines_expertise or expert.specialite
        )
        print(f"   Demandes disponibles dans son domaine: {demandes_disponibles.count()}")
        
        # Total nouvelles demandes (logique corrigée)
        from django.db.models import Q
        nouvelles_demandes = DemandeExpert.objects.filter(
            Q(expert__isnull=True, domaine_demande=expert.domaines_expertise or expert.specialite) |
            Q(expert=expert, statut='en_attente'),
            statut='en_attente'
        )
        print(f"   Total nouvelles demandes (logique corrigée): {nouvelles_demandes.count()}")
        print()
        
        # Détail des demandes
        print("📝 Détail des demandes pour cet expert :")
        for i, demande in enumerate(nouvelles_demandes[:5]):
            type_demande = "Assignée directement" if demande.expert else "Demande générale"
            print(f"   {i+1}. {demande.sujet} [{type_demande}] - {demande.get_urgence_display()}")
    
    print("\n✅ Test terminé avec succès !")

if __name__ == "__main__":
    test_expert_fix()
