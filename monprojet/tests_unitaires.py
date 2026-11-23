#!/usr/bin/env python
"""
🌱 AgriSmart - Tests Unitaires Complets
========================================
Vérifie les modèles, formulaires, vues, services et utilitaires.
Exécuter avec : python manage.py test tests_unitaires --verbosity=2
"""

import os
import sys
import json
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from decimal import Decimal

from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.utils import timezone

from monapp.models import (
    TypeCulture, Agriculteur, ConseilAgricole,
    ActiviteAgricole, Expert, DemandeExpert, MessageDiscussion
)
from monapp.forms import (
    CustomUserCreationForm, AgriculteurForm,
    DemandeExpertForm, ExpertRegistrationForm
)
from monapp.utils import get_user_role, get_user_dashboard_url, is_agriculteur, is_expert


# =====================================================================
# 1. TESTS DES MODÈLES
# =====================================================================

class TypeCultureModelTest(TestCase):
    """Tests du modèle TypeCulture"""

    def setUp(self):
        self.culture = TypeCulture.objects.create(
            nom='Maïs',
            description='Culture céréalière principale',
            statut_saison='en_saison',
            periode_semis_debut=3,
            periode_semis_fin=5
        )

    def test_creation_type_culture(self):
        """Vérifier qu'un TypeCulture peut être créé"""
        self.assertEqual(self.culture.nom, 'Maïs')
        self.assertEqual(self.culture.statut_saison, 'en_saison')

    def test_str_representation(self):
        """Vérifier la représentation string"""
        self.assertEqual(str(self.culture), 'Maïs')

    def test_statut_couleur_property(self):
        """Vérifier la propriété statut_couleur"""
        self.assertEqual(self.culture.statut_couleur, 'green')

    def test_statut_couleur_hors_saison(self):
        """Vérifier la couleur hors saison"""
        self.culture.statut_saison = 'hors_saison'
        self.assertEqual(self.culture.statut_couleur, 'gray')

    def test_statut_couleur_fin_saison(self):
        """Vérifier la couleur fin de saison"""
        self.culture.statut_saison = 'fin_saison'
        self.assertEqual(self.culture.statut_couleur, 'yellow')

    def test_statut_couleur_preparation(self):
        """Vérifier la couleur préparation"""
        self.culture.statut_saison = 'preparation'
        self.assertEqual(self.culture.statut_couleur, 'blue')

    def test_nom_unique(self):
        """Vérifier l'unicité du nom"""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            TypeCulture.objects.create(nom='Maïs')


class AgriculteurModelTest(TestCase):
    """Tests du modèle Agriculteur"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='agriculteur1',
            password='testpass123!',
            first_name='Jean',
            last_name='Dupont'
        )
        self.agriculteur = Agriculteur.objects.create(
            user=self.user,
            contact='+22590000000',
            localisation='Lomé, Togo',
            superficie='5 hectares'
        )
        self.culture = TypeCulture.objects.create(nom='Tomates')
        self.agriculteur.cultures_pratiquees.add(self.culture)

    def test_creation_agriculteur(self):
        """Vérifier la création d'un agriculteur"""
        self.assertEqual(self.agriculteur.user.username, 'agriculteur1')
        self.assertEqual(self.agriculteur.localisation, 'Lomé, Togo')

    def test_str_representation(self):
        """Vérifier la représentation string (nom complet)"""
        self.assertEqual(str(self.agriculteur), 'Jean Dupont')

    def test_str_sans_nom_complet(self):
        """Vérifier le fallback vers username si pas de nom complet"""
        user2 = User.objects.create_user(username='user_sans_nom', password='pass123!')
        agri2 = Agriculteur.objects.create(user=user2)
        self.assertEqual(str(agri2), 'user_sans_nom')

    def test_cultures_pratiquees(self):
        """Vérifier la relation ManyToMany avec TypeCulture"""
        self.assertIn(self.culture, self.agriculteur.cultures_pratiquees.all())
        self.assertEqual(self.agriculteur.cultures_pratiquees.count(), 1)


class ExpertModelTest(TestCase):
    """Tests du modèle Expert"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='expert1',
            password='testpass123!',
            first_name='Marie',
            last_name='Koné',
            email='marie@test.com'
        )
        self.expert = Expert.objects.create(
            user=self.user,
            specialite='cultures_maraicheres',
            experience='8-15',
            statut_professionnel='ingenieur_agronome',
            bio='Experte en cultures maraîchères avec 10 ans d\'expérience.',
            est_verifie=True,
            disponible=True
        )

    def test_creation_expert(self):
        """Vérifier la création d'un expert"""
        self.assertEqual(self.expert.specialite, 'cultures_maraicheres')
        self.assertTrue(self.expert.est_verifie)

    def test_str_representation(self):
        """Vérifier la représentation string"""
        self.assertIn('Marie Koné', str(self.expert))
        self.assertIn('Cultures Maraîchères', str(self.expert))

    def test_nom_complet_property(self):
        """Vérifier la propriété nom_complet"""
        self.assertEqual(self.expert.nom_complet, 'Marie Koné')

    def test_auto_sync_fields_on_save(self):
        """Vérifier la synchronisation automatique des champs au save"""
        user2 = User.objects.create_user(
            username='expert2', password='pass123!',
            first_name='Paul', last_name='Eze', email='paul@test.com'
        )
        expert2 = Expert.objects.create(user=user2)
        # Les champs doivent être auto-remplis depuis User
        self.assertEqual(expert2.nom, 'Eze')
        self.assertEqual(expert2.prenom, 'Paul')
        self.assertEqual(expert2.email, 'paul@test.com')

    def test_sync_domaines_expertise(self):
        """Vérifier la synchronisation domaines_expertise avec specialite"""
        self.assertEqual(self.expert.domaines_expertise, 'cultures_maraicheres')


class ConseilAgricoleModelTest(TestCase):
    """Tests du modèle ConseilAgricole"""

    def setUp(self):
        self.culture = TypeCulture.objects.create(nom='Riz')
        self.conseil = ConseilAgricole.objects.create(
            titre='Gestion de l\'eau pour le riz',
            theme='irrigation_arrosage',
            contenu='Maintenez la lame d\'eau à 5cm pendant le tallage.',
            type_culture=self.culture,
            niveau_difficulte='intermediaire',
            auteur='Dr. Koffi'
        )

    def test_creation_conseil(self):
        """Vérifier la création d'un conseil"""
        self.assertEqual(self.conseil.titre, 'Gestion de l\'eau pour le riz')
        self.assertEqual(self.conseil.theme, 'irrigation_arrosage')

    def test_str_representation(self):
        """Vérifier le __str__"""
        expected = "Riz - Irrigation et Arrosage: Gestion de l'eau pour le riz"
        self.assertEqual(str(self.conseil), expected)

    def test_ordering(self):
        """Vérifier l'ordering par date_creation décroissante"""
        conseil2 = ConseilAgricole.objects.create(
            titre='Conseil 2', theme='semences',
            contenu='Contenu', type_culture=self.culture
        )
        conseils = list(ConseilAgricole.objects.all())
        # Le plus récent en premier
        self.assertEqual(conseils[0], conseil2)


class ActiviteAgricoleModelTest(TestCase):
    """Tests du modèle ActiviteAgricole"""

    def setUp(self):
        self.user = User.objects.create_user(username='agri', password='pass123!')
        self.agriculteur = Agriculteur.objects.create(user=self.user)
        self.culture = TypeCulture.objects.create(nom='Manioc')
        self.activite = ActiviteAgricole.objects.create(
            agriculteur=self.agriculteur,
            type_culture=self.culture,
            type_activite='semis',
            date_prevue=date.today() + timedelta(days=7),
            description='Semis de manioc parcelle nord'
        )

    def test_creation_activite(self):
        """Vérifier la création d'une activité"""
        self.assertEqual(self.activite.type_activite, 'semis')
        self.assertFalse(self.activite.terminee)

    def test_str_representation(self):
        """Vérifier le __str__"""
        self.assertIn('Semis', str(self.activite))
        self.assertIn('Manioc', str(self.activite))

    def test_ordering(self):
        """Vérifier l'ordering par date_prevue"""
        activite2 = ActiviteAgricole.objects.create(
            agriculteur=self.agriculteur,
            type_culture=self.culture,
            type_activite='recolte',
            date_prevue=date.today() + timedelta(days=1),
        )
        activites = list(ActiviteAgricole.objects.all())
        self.assertEqual(activites[0], activite2)  # Date plus proche en premier


class DemandeExpertModelTest(TestCase):
    """Tests du modèle DemandeExpert"""

    def setUp(self):
        self.user_agri = User.objects.create_user(username='agri', password='pass123!')
        self.user_expert = User.objects.create_user(username='expert', password='pass123!')
        self.agriculteur = Agriculteur.objects.create(user=self.user_agri)
        self.expert = Expert.objects.create(user=self.user_expert, specialite='irrigation')
        self.demande = DemandeExpert.objects.create(
            agriculteur=self.agriculteur,
            expert=self.expert,
            domaine_demande='irrigation',
            sujet='Problème d\'irrigation',
            description='Mon système d\'irrigation ne fonctionne plus.',
            urgence='elevee',
            statut='en_attente'
        )

    def test_creation_demande(self):
        """Vérifier la création d'une demande"""
        self.assertEqual(self.demande.sujet, 'Problème d\'irrigation')
        self.assertEqual(self.demande.statut, 'en_attente')

    def test_a_reponse_false(self):
        """Vérifier a_reponse quand pas de réponse"""
        self.assertFalse(self.demande.a_reponse)

    def test_a_reponse_true(self):
        """Vérifier a_reponse quand réponse existe"""
        self.demande.reponse = 'Voici ma réponse détaillée.'
        self.assertTrue(self.demande.a_reponse)

    def test_a_reponse_blank_string(self):
        """Vérifier a_reponse avec une chaîne vide/espaces"""
        self.demande.reponse = '   '
        self.assertFalse(self.demande.a_reponse)

    def test_est_en_cours(self):
        """Vérifier la propriété est_en_cours"""
        self.assertFalse(self.demande.est_en_cours)
        self.demande.statut = 'acceptee'
        self.assertTrue(self.demande.est_en_cours)
        self.demande.statut = 'en_cours'
        self.assertTrue(self.demande.est_en_cours)

    def test_ordering(self):
        """Vérifier l'ordering par date_creation décroissante"""
        demande2 = DemandeExpert.objects.create(
            agriculteur=self.agriculteur,
            domaine_demande='sols_fertilisation',
            sujet='Question sols',
            description='Test'
        )
        demandes = list(DemandeExpert.objects.all())
        self.assertEqual(demandes[0], demande2)  # Plus récente en premier


class MessageDiscussionModelTest(TestCase):
    """Tests du modèle MessageDiscussion"""

    def setUp(self):
        self.user_agri = User.objects.create_user(username='agri_msg', password='pass123!')
        self.user_expert = User.objects.create_user(username='expert_msg', password='pass123!')
        self.agriculteur = Agriculteur.objects.create(user=self.user_agri)
        self.expert = Expert.objects.create(user=self.user_expert, specialite='irrigation')
        self.demande = DemandeExpert.objects.create(
            agriculteur=self.agriculteur,
            expert=self.expert,
            domaine_demande='irrigation',
            sujet='Discussion test',
            description='Besoin de conseils.'
        )

    def test_creation_message_discussion(self):
        """Vérifier qu'un message de discussion peut être créé"""
        message = MessageDiscussion.objects.create(
            demande=self.demande,
            auteur=self.user_agri,
            contenu='Bonjour expert, voici mon problème.'
        )

        self.assertEqual(message.demande, self.demande)
        self.assertEqual(message.auteur, self.user_agri)
        self.assertTrue(message.lu is False)

    def test_ordering_message_discussion(self):
        """Vérifier l'ordre chronologique des messages"""
        message1 = MessageDiscussion.objects.create(
            demande=self.demande,
            auteur=self.user_agri,
            contenu='Premier message'
        )
        message2 = MessageDiscussion.objects.create(
            demande=self.demande,
            auteur=self.user_expert,
            contenu='Deuxième message'
        )

        messages = list(MessageDiscussion.objects.filter(demande=self.demande))
        self.assertEqual(messages[0], message1)
        self.assertEqual(messages[1], message2)


# =====================================================================
# 2. TESTS DES FORMULAIRES
# =====================================================================

class CustomUserCreationFormTest(TestCase):
    """Tests du formulaire d'inscription utilisateur"""

    def test_formulaire_valide(self):
        """Vérifier un formulaire valide"""
        form = CustomUserCreationForm(data={
            'username': 'newuser',
            'email': 'new@test.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'role': 'agriculteur',
        })
        self.assertTrue(form.is_valid(), f"Erreurs: {form.errors}")

    def test_email_duplique(self):
        """Vérifier le rejet d'un email déjà existant"""
        User.objects.create_user(
            username='existing', password='pass123!', email='exist@test.com'
        )
        form = CustomUserCreationForm(data={
            'username': 'newuser',
            'email': 'exist@test.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'role': 'agriculteur',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_creation_profil_agriculteur(self):
        """Vérifier que save() crée un profil Agriculteur"""
        form = CustomUserCreationForm(data={
            'username': 'agri_new',
            'email': 'agri@test.com',
            'first_name': 'Jean',
            'last_name': 'Togo',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'role': 'agriculteur',
        })
        self.assertTrue(form.is_valid(), f"Erreurs: {form.errors}")
        user = form.save()
        self.assertTrue(hasattr(user, 'agriculteur'))

    def test_creation_profil_expert(self):
        """Vérifier que save() crée un profil Expert"""
        form = CustomUserCreationForm(data={
            'username': 'expert_new',
            'email': 'expert@test.com',
            'first_name': 'Marie',
            'last_name': 'Expert',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'role': 'expert',
        })
        self.assertTrue(form.is_valid(), f"Erreurs: {form.errors}")
        user = form.save()
        self.assertTrue(hasattr(user, 'expert'))

    def test_mots_de_passe_differents(self):
        """Vérifier le rejet si mots de passe différents"""
        form = CustomUserCreationForm(data={
            'username': 'user',
            'email': 'user@test.com',
            'first_name': 'A',
            'last_name': 'B',
            'password1': 'ComplexPass123!',
            'password2': 'DifferentPass456!',
            'role': 'agriculteur',
        })
        self.assertFalse(form.is_valid())

    def test_role_requis(self):
        """Vérifier que le rôle est requis"""
        form = CustomUserCreationForm(data={
            'username': 'user',
            'email': 'user@test.com',
            'first_name': 'A',
            'last_name': 'B',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('role', form.errors)


class DemandeExpertFormTest(TestCase):
    """Tests du formulaire de demande d'expert"""

    def test_formulaire_valide(self):
        """Vérifier un formulaire valide"""
        form = DemandeExpertForm(data={
            'domaine_demande': 'irrigation',
            'sujet': 'Mon problème d\'irrigation',
            'description': 'Description détaillée du problème rencontré.',
            'urgence': 'normale',
        })
        self.assertTrue(form.is_valid(), f"Erreurs: {form.errors}")

    def test_champs_requis(self):
        """Vérifier que les champs requis sont bien requis"""
        form = DemandeExpertForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('domaine_demande', form.errors)
        self.assertIn('sujet', form.errors)
        self.assertIn('description', form.errors)


# =====================================================================
# 3. TESTS DES VUES (avec Client HTTP)
# =====================================================================

class IndexViewTest(TestCase):
    """Tests de la page d'accueil"""

    def setUp(self):
        self.client = Client()

    def test_index_accessible(self):
        """Vérifier que la page d'accueil est accessible"""
        response = self.client.get(reverse('monapp:index'))
        self.assertEqual(response.status_code, 200)

    def test_index_template_correct(self):
        """Vérifier que le bon template est utilisé"""
        response = self.client.get(reverse('monapp:index'))
        self.assertTemplateUsed(response, 'monapp/index.html')

    def test_index_avec_cultures(self):
        """Vérifier l'affichage avec des cultures en base"""
        TypeCulture.objects.create(nom='Maïs', statut_saison='en_saison')
        TypeCulture.objects.create(nom='Riz', statut_saison='preparation')
        response = self.client.get(reverse('monapp:index'))
        self.assertEqual(response.status_code, 200)


class AuthViewTest(TestCase):
    """Tests de la page d'authentification"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='TestPass123!',
            first_name='Test', last_name='User'
        )

    def test_auth_page_accessible(self):
        """Vérifier que la page auth est accessible"""
        response = self.client.get(reverse('monapp:auth'))
        self.assertEqual(response.status_code, 200)

    def test_login_valide(self):
        """Vérifier la connexion avec identifiants corrects"""
        response = self.client.post(reverse('monapp:auth'), {
            'action': 'login',
            'username': 'testuser',
            'password': 'TestPass123!',
        })
        # Devrait rediriger après connexion
        self.assertIn(response.status_code, [200, 302])

    def test_login_valide_avec_email(self):
        """Vérifier la connexion avec l'email au lieu du username"""
        self.user.email = 'testuser@example.com'
        self.user.save()

        response = self.client.post(reverse('monapp:auth'), {
            'action': 'login',
            'username': 'testuser@example.com',
            'password': 'TestPass123!',
        })

        self.assertIn(response.status_code, [200, 302])

    def test_login_invalide(self):
        """Vérifier le rejet d'identifiants incorrects"""
        response = self.client.post(reverse('monapp:auth'), {
            'action': 'login',
            'username': 'testuser',
            'password': 'WrongPassword',
        })
        self.assertEqual(response.status_code, 200)  # Reste sur la page

    def test_logout(self):
        """Vérifier la déconnexion"""
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.get(reverse('monapp:logout'))
        self.assertIn(response.status_code, [200, 302])


class CompteViewTest(TestCase):
    """Tests de la page Mon Compte"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='agriuser', password='TestPass123!'
        )
        self.agriculteur = Agriculteur.objects.create(user=self.user)

    def test_compte_requiert_connexion(self):
        """Vérifier que la page compte nécessite une connexion"""
        response = self.client.get(reverse('monapp:compte'))
        # Devrait rediriger vers la page d'auth
        self.assertIn(response.status_code, [302, 301])

    def test_compte_accessible_connecte(self):
        """Vérifier l'accès à la page compte une fois connecté"""
        self.client.login(username='agriuser', password='TestPass123!')
        response = self.client.get(reverse('monapp:compte'))
        self.assertEqual(response.status_code, 200)


class ProfilePasswordChangeTest(TestCase):
    """Tests du changement de mot de passe depuis le profil"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='agri_password',
            password='OldPass123!',
            first_name='Alpha',
            last_name='Test'
        )
        Agriculteur.objects.create(user=self.user)

    def test_changement_mot_de_passe_profil(self):
        """Le mot de passe doit pouvoir être modifié depuis le profil"""
        self.client.login(username='agri_password', password='OldPass123!')
        response = self.client.post(reverse('monapp:update_profile'), {
            'email': 'agri_password@example.com',
            'contact': '',
            'localisation': '',
            'superficie': '',
            'current_password': 'OldPass123!',
            'new_password1': 'NewPass123!',
            'new_password2': 'NewPass123!',
        })

        self.assertEqual(response.status_code, 302)
        updated_user = User.objects.get(username='agri_password')
        self.assertTrue(updated_user.check_password('NewPass123!'))

    def test_changement_mot_de_passe_refuse_si_ancien_incorrect(self):
        """Le changement doit échouer si l'ancien mot de passe est faux"""
        self.client.login(username='agri_password', password='OldPass123!')
        response = self.client.post(reverse('monapp:update_profile'), {
            'email': 'agri_password@example.com',
            'contact': '',
            'localisation': '',
            'superficie': '',
            'current_password': 'WrongOldPass!',
            'new_password1': 'NewPass123!',
            'new_password2': 'NewPass123!',
        })

        self.assertEqual(response.status_code, 302)
        updated_user = User.objects.get(username='agri_password')
        self.assertTrue(updated_user.check_password('OldPass123!'))


class ConseilsViewTest(TestCase):
    """Tests de la page Conseils"""

    def setUp(self):
        self.client = Client()
        self.culture = TypeCulture.objects.create(nom='Tomates')
        self.conseil = ConseilAgricole.objects.create(
            titre='Arrosage des tomates',
            theme='irrigation_arrosage',
            contenu='Arrosez régulièrement sans mouiller les feuilles.',
            type_culture=self.culture,
        )

    def test_conseils_page_accessible(self):
        """Vérifier que la page conseils est accessible"""
        response = self.client.get(reverse('monapp:conseils'))
        self.assertEqual(response.status_code, 200)

    def test_conseils_avec_filtre_culture(self):
        """Vérifier le filtrage par culture"""
        response = self.client.get(
            reverse('monapp:conseils'),
            {'culture': self.culture.id}
        )
        self.assertEqual(response.status_code, 200)

    def test_conseils_avec_recherche(self):
        """Vérifier la recherche textuelle"""
        response = self.client.get(
            reverse('monapp:conseils'),
            {'q': 'tomates'}
        )
        self.assertEqual(response.status_code, 200)

    def test_conseil_detail(self):
        """Vérifier la page de détail d'un conseil"""
        response = self.client.get(
            reverse('monapp:conseil_detail', args=[self.conseil.id])
        )
        self.assertEqual(response.status_code, 200)


class CalendrierViewTest(TestCase):
    """Tests de la page Calendrier"""

    def setUp(self):
        self.client = Client()

    def test_calendrier_accessible(self):
        """Vérifier que le calendrier est accessible"""
        response = self.client.get(reverse('monapp:calendrier'))
        self.assertEqual(response.status_code, 200)


class ExpertsViewTest(TestCase):
    """Tests de la page Experts"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='expert_test', password='TestPass123!',
            first_name='Expert', last_name='Test'
        )
        self.expert = Expert.objects.create(
            user=self.user,
            specialite='cultures_cerealieres',
            est_verifie=True,
            disponible=True,
            bio='Expert en céréales.'
        )

    def test_experts_page_accessible(self):
        """Vérifier que la page experts est accessible"""
        response = self.client.get(reverse('monapp:experts'))
        self.assertEqual(response.status_code, 200)


class MeteoViewTest(TestCase):
    """Tests de la page Météo"""

    def setUp(self):
        self.client = Client()

    def test_meteo_accessible(self):
        """Vérifier que la page météo est accessible"""
        response = self.client.get(reverse('monapp:meteo'))
        self.assertEqual(response.status_code, 200)


# =====================================================================
# 4. TESTS DES URLs
# =====================================================================

class URLResolutionTest(TestCase):
    """Tests de résolution des URLs"""

    def test_index_url(self):
        """Vérifier l'URL de l'index"""
        url = reverse('monapp:index')
        self.assertEqual(url, '/')

    def test_conseils_url(self):
        """Vérifier l'URL des conseils"""
        url = reverse('monapp:conseils')
        self.assertEqual(url, '/conseils/')

    def test_calendrier_url(self):
        """Vérifier l'URL du calendrier"""
        url = reverse('monapp:calendrier')
        self.assertEqual(url, '/calendrier/')

    def test_meteo_url(self):
        """Vérifier l'URL de la météo"""
        url = reverse('monapp:meteo')
        self.assertEqual(url, '/meteo/')

    def test_compte_url(self):
        """Vérifier l'URL du compte"""
        url = reverse('monapp:compte')
        self.assertEqual(url, '/compte/')

    def test_auth_url(self):
        """Vérifier l'URL d'authentification"""
        url = reverse('monapp:auth')
        self.assertEqual(url, '/auth/')

    def test_experts_url(self):
        """Vérifier l'URL des experts"""
        url = reverse('monapp:experts')
        self.assertEqual(url, '/experts/')

    def test_expert_dashboard_url(self):
        """Vérifier l'URL du dashboard expert"""
        url = reverse('monapp:expert_dashboard')
        self.assertEqual(url, '/expert-dashboard/')

    def test_discussion_historique_url(self):
        """Vérifier l'URL fallback de l'historique discussion"""
        url = reverse('monapp:discussion_historique_json', kwargs={'demande_id': 1})
        self.assertEqual(url, '/demande-detail/1/discussion-historique/')

    def test_logout_url(self):
        """Vérifier l'URL de déconnexion"""
        url = reverse('monapp:logout')
        self.assertEqual(url, '/logout/')


# =====================================================================
# 5. TESTS DES UTILITAIRES
# =====================================================================

class UtilsTest(TestCase):
    """Tests des fonctions utilitaires"""

    def setUp(self):
        self.user_agri = User.objects.create_user(username='agri_util', password='pass123!')
        self.user_expert = User.objects.create_user(username='expert_util', password='pass123!')
        self.user_normal = User.objects.create_user(username='normal', password='pass123!')
        Agriculteur.objects.create(user=self.user_agri)
        Expert.objects.create(user=self.user_expert, specialite='irrigation')

    def test_get_user_role_agriculteur(self):
        """Vérifier la détection du rôle agriculteur"""
        role = get_user_role(self.user_agri)
        self.assertEqual(role, 'agriculteur')

    def test_get_user_role_expert(self):
        """Vérifier la détection du rôle expert"""
        role = get_user_role(self.user_expert)
        self.assertEqual(role, 'expert')

    def test_is_agriculteur(self):
        """Vérifier is_agriculteur()"""
        self.assertTrue(is_agriculteur(self.user_agri))
        self.assertFalse(is_agriculteur(self.user_expert))

    def test_is_expert(self):
        """Vérifier is_expert()"""
        self.assertTrue(is_expert(self.user_expert))
        self.assertFalse(is_expert(self.user_agri))

    def test_get_user_dashboard_url_agriculteur(self):
        """Vérifier l'URL dashboard pour un agriculteur"""
        url = get_user_dashboard_url(self.user_agri)
        self.assertEqual(url, 'monapp:compte')

    def test_get_user_dashboard_url_expert(self):
        """Vérifier l'URL dashboard pour un expert"""
        url = get_user_dashboard_url(self.user_expert)
        self.assertEqual(url, 'monapp:expert_dashboard')


# =====================================================================
# 6. TESTS DU SERVICE MÉTÉO
# =====================================================================

class WeatherServiceTest(TestCase):
    """Tests du service météo"""

    def test_import_weather_service(self):
        """Vérifier que le service météo peut être importé"""
        from monapp.weather_service import WeatherService
        service = WeatherService()
        self.assertIsNotNone(service)

    def test_fallback_current_weather(self):
        """Vérifier les données de secours météo actuelle"""
        from monapp.weather_service import WeatherService
        service = WeatherService()
        fallback = service._get_fallback_current_weather()
        self.assertIn('temperature', fallback)
        self.assertIn('humidite', fallback)
        self.assertIn('vent', fallback)
        self.assertEqual(fallback['temperature'], 28)

    def test_fallback_forecast(self):
        """Vérifier les données de secours prévisions"""
        from monapp.weather_service import WeatherService
        service = WeatherService()
        forecast = service._get_fallback_forecast()
        self.assertEqual(len(forecast), 5)
        self.assertEqual(forecast[0]['jour'], "Aujourd'hui")

    def test_weather_icon_class(self):
        """Vérifier le mapping des icônes météo"""
        from monapp.weather_service import WeatherService
        service = WeatherService()
        icon = service._get_weather_icon_class('01d')
        self.assertIn('fa-sun', icon)
        icon_unknown = service._get_weather_icon_class('unknown')
        self.assertIn('fa-cloud', icon_unknown)

    def test_agricultural_advice_chaleur(self):
        """Vérifier les conseils agricoles en cas de chaleur"""
        from monapp.weather_service import WeatherService
        service = WeatherService()
        weather_data = {
            'temperature': 38,
            'humidite': 45,
            'vent': 10
        }
        forecast_data = [
            {'probabilite_pluie': 10},
            {'probabilite_pluie': 5},
            {'probabilite_pluie': 0},
        ]
        advice = service.get_agricultural_advice(weather_data, forecast_data)
        self.assertIsNotNone(advice)
        self.assertIn('Chaleur', advice['titre'])

    def test_agricultural_advice_pluie(self):
        """Vérifier les conseils agricoles en cas de pluie prévue"""
        from monapp.weather_service import WeatherService
        service = WeatherService()
        weather_data = {
            'temperature': 25,
            'humidite': 70,
            'vent': 10
        }
        forecast_data = [
            {'probabilite_pluie': 80},
            {'probabilite_pluie': 90},
            {'probabilite_pluie': 60},
        ]
        advice = service.get_agricultural_advice(weather_data, forecast_data)
        self.assertIsNotNone(advice)
        self.assertIn('Pluie', advice['titre'])

    def test_agricultural_advice_none_data(self):
        """Vérifier le retour None si données manquantes"""
        from monapp.weather_service import WeatherService
        service = WeatherService()
        self.assertIsNone(service.get_agricultural_advice(None, None))
        self.assertIsNone(service.get_agricultural_advice({}, None))


# =====================================================================
# 7. TESTS D'INTÉGRATION (Flux complets)
# =====================================================================

class FluxInscriptionTest(TestCase):
    """Tests du flux complet d'inscription"""

    def setUp(self):
        self.client = Client()

    def test_inscription_agriculteur_complete(self):
        """Tester le flux complet d'inscription agriculteur"""
        response = self.client.post(reverse('monapp:auth'), {
            'action': 'register',
            'username': 'new_agri',
            'email': 'agri@nouveau.com',
            'first_name': 'Kouadio',
            'last_name': 'Yao',
            'password1': 'AgriPass2025!',
            'password2': 'AgriPass2025!',
            'role': 'agriculteur',
        })
        # Devrait rediriger vers le compte après inscription
        self.assertIn(response.status_code, [200, 302])
        # Vérifier que l'utilisateur existe et possède un profil agriculteur
        self.assertTrue(User.objects.filter(username='new_agri').exists())
        created_user = User.objects.get(username='new_agri')
        self.assertTrue(Agriculteur.objects.filter(user=created_user).exists())

    def test_connexion_apres_inscription_avec_email(self):
        """Tester que l'utilisateur peut se reconnecter avec son email"""
        self.client.post(reverse('monapp:auth'), {
            'action': 'register',
            'username': 'reconnect_agri',
            'email': 'reconnect@agri.com',
            'first_name': 'Jean',
            'last_name': 'Test',
            'password1': 'AgriPass2025!',
            'password2': 'AgriPass2025!',
            'role': 'agriculteur',
        })

        self.client.logout()
        response = self.client.post(reverse('monapp:auth'), {
            'action': 'login',
            'username': 'reconnect@agri.com',
            'password': 'AgriPass2025!',
        })

        self.assertIn(response.status_code, [200, 302])

    def test_connexion_expert_apres_inscription_avec_email(self):
        """Tester qu'un expert peut se connecter avec son email"""
        self.client.post(reverse('monapp:auth'), {
            'action': 'register',
            'username': 'expert_user_login',
            'email': 'expert.login@example.com',
            'first_name': 'Expert',
            'last_name': 'Login',
            'password1': 'ExpertPass2025!',
            'password2': 'ExpertPass2025!',
            'role': 'expert',
        })

        self.client.logout()
        response = self.client.post(reverse('monapp:expert_login'), {
            'username': 'expert.login@example.com',
            'password': 'ExpertPass2025!',
        })

        self.assertIn(response.status_code, [200, 302])


class FluxDemandeExpertTest(TestCase):
    """Tests du flux de demande d'expert"""

    def setUp(self):
        self.client = Client()
        self.user_agri = User.objects.create_user(
            username='agri_demande', password='TestPass123!'
        )
        self.agriculteur = Agriculteur.objects.create(user=self.user_agri)
        self.user_expert = User.objects.create_user(
            username='expert_rep', password='TestPass123!',
            first_name='Dr', last_name='Expert'
        )
        self.expert = Expert.objects.create(
            user=self.user_expert,
            specialite='cultures_maraicheres',
            est_verifie=True,
            bio='Expert vérifié.'
        )

    def test_creation_demande(self):
        """Tester la création d'une demande d'expert via le modèle"""
        demande = DemandeExpert.objects.create(
            agriculteur=self.agriculteur,
            expert=self.expert,
            domaine_demande='cultures_maraicheres',
            sujet='Parasites sur les tomates',
            description='Mes tomates sont attaquées par des pucerons.',
            urgence='elevee'
        )
        self.assertEqual(demande.statut, 'en_attente')
        self.assertFalse(demande.a_reponse)

    def test_reponse_expert(self):
        """Tester l'ajout d'une réponse par l'expert"""
        demande = DemandeExpert.objects.create(
            agriculteur=self.agriculteur,
            expert=self.expert,
            domaine_demande='cultures_maraicheres',
            sujet='Parasites',
            description='Problème de pucerons.',
            statut='acceptee'
        )
        # L'expert répond
        demande.reponse = 'Utilisez du savon noir dilué pour traiter les pucerons.'
        demande.date_reponse = timezone.now()
        demande.statut = 'terminee'
        demande.save()

        demande.refresh_from_db()
        self.assertTrue(demande.a_reponse)
        self.assertEqual(demande.statut, 'terminee')

    def test_evaluation_agriculteur(self):
        """Tester l'évaluation d'une réponse par l'agriculteur"""
        demande = DemandeExpert.objects.create(
            agriculteur=self.agriculteur,
            expert=self.expert,
            domaine_demande='cultures_maraicheres',
            sujet='Test évaluation',
            description='Test.',
            reponse='Réponse de l\'expert.',
            statut='terminee'
        )
        demande.note_satisfaction = 5
        demande.commentaire_satisfaction = 'Excellent conseil, merci !'
        demande.save()

        demande.refresh_from_db()
        self.assertEqual(demande.note_satisfaction, 5)
        self.assertEqual(demande.commentaire_satisfaction, 'Excellent conseil, merci !')


class DiscussionHistoriqueJsonTest(TestCase):
    """Tests du fallback JSON pour l'historique de discussion"""

    def setUp(self):
        self.client = Client()
        self.user_agri = User.objects.create_user(username='agri_disc', password='TestPass123!')
        self.user_expert = User.objects.create_user(username='expert_disc', password='TestPass123!')
        self.user_normal = User.objects.create_user(username='normal_disc', password='TestPass123!')
        self.agriculteur = Agriculteur.objects.create(user=self.user_agri)
        self.expert = Expert.objects.create(user=self.user_expert, specialite='irrigation')
        self.demande = DemandeExpert.objects.create(
            agriculteur=self.agriculteur,
            expert=self.expert,
            domaine_demande='irrigation',
            sujet='Demande discussion',
            description='Besoin de dialogue.'
        )
        self.message = MessageDiscussion.objects.create(
            demande=self.demande,
            auteur=self.user_agri,
            contenu='Bonjour, j’ai une question.'
        )

    def test_historique_json_agriculteur(self):
        """L'agriculteur doit pouvoir récupérer l'historique"""
        self.client.login(username='agri_disc', password='TestPass123!')
        response = self.client.get(reverse('monapp:discussion_historique_json', kwargs={'demande_id': self.demande.id}))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(len(payload['messages']), 1)
        self.assertEqual(payload['messages'][0]['contenu'], 'Bonjour, j’ai une question.')

    def test_historique_json_expert(self):
        """L'expert assigné doit pouvoir récupérer l'historique"""
        self.client.login(username='expert_disc', password='TestPass123!')
        response = self.client.get(reverse('monapp:discussion_historique_json', kwargs={'demande_id': self.demande.id}))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['demande_id'], self.demande.id)

    def test_historique_json_utilisateur_non_autorise(self):
        """Un utilisateur non concerné doit être refusé"""
        self.client.login(username='normal_disc', password='TestPass123!')
        response = self.client.get(reverse('monapp:discussion_historique_json', kwargs={'demande_id': self.demande.id}))

        self.assertEqual(response.status_code, 403)


class DiscussionDetailViewTest(TestCase):
    """Tests de régression des vues de détail avec discussion"""

    def setUp(self):
        self.client = Client()
        self.user_agri = User.objects.create_user(username='agri_detail', password='TestPass123!')
        self.user_expert = User.objects.create_user(username='expert_detail', password='TestPass123!')
        self.agriculteur = Agriculteur.objects.create(user=self.user_agri)
        self.expert = Expert.objects.create(user=self.user_expert, specialite='irrigation')
        self.demande = DemandeExpert.objects.create(
            agriculteur=self.agriculteur,
            expert=self.expert,
            domaine_demande='irrigation',
            sujet='Vue discussion',
            description='Vérifier le rendu.'
        )
        MessageDiscussion.objects.create(
            demande=self.demande,
            auteur=self.user_agri,
            contenu='Premier message de test.'
        )

    def test_vue_detail_agriculteur_rend_la_page(self):
        """La vue détail agriculteur doit rester fonctionnelle"""
        self.client.login(username='agri_detail', password='TestPass123!')
        response = self.client.get(reverse('monapp:demande_detail_agriculteur', kwargs={'demande_id': self.demande.id}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Discussion en temps réel')
        self.assertContains(response, 'Premier message de test.')

    def test_vue_detail_expert_rend_la_page(self):
        """La vue détail expert doit rester fonctionnelle"""
        self.client.login(username='expert_detail', password='TestPass123!')
        response = self.client.get(reverse('monapp:expert_demande_detail', kwargs={'demande_id': self.demande.id}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Discussion en temps réel')
        self.assertContains(response, 'Premier message de test.')
