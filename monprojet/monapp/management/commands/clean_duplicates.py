from django.core.management.base import BaseCommand
from monapp.models import TypeCulture

class Command(BaseCommand):
    help = 'Nettoie les doublons de cultures'

    def handle(self, *args, **options):
        # Rechercher et supprimer les doublons
        duplicates_found = 0
        
        # Grouper les cultures par nom normalisé
        cultures = TypeCulture.objects.all()
        seen_names = {}
        
        for culture in cultures:
            # Normaliser le nom (supprimer accents, espaces, etc.)
            normalized_name = culture.nom.lower().strip()
            
            if normalized_name in seen_names:
                self.stdout.write(
                    self.style.WARNING(f'Doublon trouvé: {culture.nom} (gardé: {seen_names[normalized_name].nom})')
                )
                culture.delete()
                duplicates_found += 1
            else:
                seen_names[normalized_name] = culture
        
        if duplicates_found == 0:
            self.stdout.write(self.style.SUCCESS('Aucun doublon trouvé.'))
        else:
            self.stdout.write(
                self.style.SUCCESS(f'{duplicates_found} doublon(s) supprimé(s) avec succès.')
            )
