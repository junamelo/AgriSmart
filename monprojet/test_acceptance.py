#!/usr/bin/env python
"""
Simulation de l'acceptation d'une demande par un expert
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monprojet.settings')
django.setup()

from monapp.models import DemandeExpert, Expert
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

def simulate_expert_accept_request(expert_id, demande_id):
    """Simuler l'acceptation d'une demande par un expert"""
    print(f"🧪 Simulation d'acceptation - Expert ID: {expert_id}, Demande ID: {demande_id}")
    print("=" * 60)
    
    try:
        expert = Expert.objects.get(id=expert_id)
        print(f"👨‍💼 Expert: {expert.nom_complet}")
        
        # Récupérer la demande (peut être avec ou sans expert assigné)
        demande = get_object_or_404(DemandeExpert, id=demande_id, statut='en_attente')
        print(f"📋 Demande: {demande.sujet}")
        print(f"📊 Statut initial: {demande.statut}")
        print(f"👤 Expert assigné: {demande.expert or 'Aucun'}")
        print()
        
        # Logique corrigée
        # Cas 1: Demande sans expert assigné (demande générale)
        if demande.expert is None:
            print("🔀 Cas 1: Demande générale (sans expert assigné)")
            demande.expert = expert
            demande.statut = 'acceptee'
            demande.save()
            result = {'success': True, 'message': 'Demande acceptée avec succès.'}
            
        # Cas 2: Demande déjà assignée à cet expert (contact direct)
        elif demande.expert == expert:
            print("🎯 Cas 2: Demande assignée directement à cet expert")
            demande.statut = 'acceptee'
            demande.save()
            result = {'success': True, 'message': 'Demande acceptée avec succès.'}
            
        # Cas 3: Demande assignée à un autre expert
        else:
            print("❌ Cas 3: Demande assignée à un autre expert")
            result = {'success': False, 'error': 'Cette demande est déjà assignée à un autre expert.'}
        
        print(f"✅ Résultat: {result}")
        print(f"📊 Statut final: {demande.statut}")
        print(f"👤 Expert final: {demande.expert}")
        
        return result
        
    except Expert.DoesNotExist:
        result = {'success': False, 'error': 'Expert non trouvé.'}
        print(f"❌ Erreur: {result}")
        return result
    except Exception as e:
        result = {'success': False, 'error': f'Erreur: {str(e)}'}
        print(f"💥 Exception: {result}")
        return result

def main():
    print("🚀 Test de simulation d'acceptation de demandes")
    print("=" * 60)
    
    # Récupérer un expert et une demande en attente
    expert = Expert.objects.first()
    if not expert:
        print("❌ Aucun expert trouvé")
        return
    
    # Chercher une demande en attente pour cet expert
    demande_assignee = DemandeExpert.objects.filter(
        expert=expert, 
        statut='en_attente'
    ).first()
    
    if demande_assignee:
        print(f"📋 Test avec demande assignée directement...")
        simulate_expert_accept_request(expert.id, demande_assignee.id)
        print()
    
    # Chercher une demande générale
    demande_generale = DemandeExpert.objects.filter(
        expert__isnull=True,
        statut='en_attente'
    ).first()
    
    if demande_generale:
        print(f"📋 Test avec demande générale...")
        simulate_expert_accept_request(expert.id, demande_generale.id)
        print()
    
    print("🎯 Tests terminés !")

if __name__ == "__main__":
    main()
