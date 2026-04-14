from django.core.management.base import BaseCommand
from monapp.models import TypeCulture

class Command(BaseCommand):
    help = 'Crée les types de cultures de base'
    
    def handle(self, *args, **options):
        cultures = [
            {'nom': 'Manioc', 'description': 'Culture de tubercule, aliment de base'},
            {'nom': 'Igname', 'description': 'Culture de tubercule'},
            {'nom': 'Maïs', 'description': 'Culture céréalière importante'},
            {'nom': 'Mil', 'description': 'Céréale résistante à la sécheresse'},
            {'nom': 'Riz', 'description': 'Céréale cultivée en zone humide'},
            {'nom': 'Haricot', 'description': 'Légumineuse riche en protéines'},
        ]
        
        created_count = 0
        for culture_data in cultures:
            culture, created = TypeCulture.objects.get_or_create(
                nom=culture_data['nom'],
                defaults=culture_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Culture "{culture.nom}" créée avec succès')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Culture "{culture.nom}" existe déjà')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'{created_count} nouvelles cultures créées')
        )
