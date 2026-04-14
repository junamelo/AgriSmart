from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from monapp.models import Agriculteur

class Command(BaseCommand):
    help = 'Crée des profils agriculteurs manquants pour les utilisateurs existants'

    def handle(self, *args, **options):
        # Récupérer tous les utilisateurs sans profil agriculteur
        users_without_profile = User.objects.filter(agriculteur__isnull=True)
        
        created_count = 0
        
        for user in users_without_profile:
            # Créer le profil agriculteur manquant
            agriculteur = Agriculteur.objects.create(
                user=user,
                contact='',
                localisation='',
                superficie=''
            )
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Profil créé pour l\'utilisateur: {user.username}')
            )
        
        if created_count == 0:
            self.stdout.write(
                self.style.SUCCESS('Tous les utilisateurs ont déjà un profil agriculteur.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'{created_count} profil(s) agriculteur(s) créé(s) avec succès.')
            )
