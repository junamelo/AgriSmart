from django.core.management.base import BaseCommand
from monapp.models import TypeCulture, ConseilAgricole

class Command(BaseCommand):
    help = 'Peuple la base de données avec des données d\'exemple pour les conseils agricoles'

    def handle(self, *args, **options):
        self.stdout.write('Création des types de cultures...')
        
        # Créer ou récupérer les cultures
        mais, created = TypeCulture.objects.get_or_create(
            nom='Maïs',
            defaults={
                'description': 'Céréale de base, culture principale en Afrique',
                'statut_saison': 'en_saison',
                'periode_semis_debut': 4,
                'periode_semis_fin': 6
            }
        )
        
        haricot, created = TypeCulture.objects.get_or_create(
            nom='Haricot',
            defaults={
                'description': 'Légumineuse riche en protéines',
                'statut_saison': 'en_saison',
                'periode_semis_debut': 3,
                'periode_semis_fin': 5
            }
        )
        
        manioc, created = TypeCulture.objects.get_or_create(
            nom='Manioc',
            defaults={
                'description': 'Tubercule de base, résistant à la sécheresse',
                'statut_saison': 'preparation',
                'periode_semis_debut': 2,
                'periode_semis_fin': 4
            }
        )
        
        tomate, created = TypeCulture.objects.get_or_create(
            nom='Tomate',
            defaults={
                'description': 'Fruit légume très cultivé',
                'statut_saison': 'en_saison',
                'periode_semis_debut': 3,
                'periode_semis_fin': 7
            }
        )
        
        self.stdout.write('Création des conseils agricoles...')
        
        # Conseils pour le Maïs - Irrigation et Arrosage
        conseils_mais_irrigation = [
            {
                'titre': 'Fréquence d\'arrosage optimal pour le maïs',
                'contenu': '''Le maïs a besoin d'un arrosage régulier, surtout pendant la floraison. 
                
Voici les recommandations :
• Arrosez 2-3 fois par semaine
• Quantité : 25-30mm d'eau à chaque arrosage
• Évitez l'arrosage des feuilles pour prévenir les maladies fongiques
• Arrosez de préférence le matin ou en fin d'après-midi
• Augmentez la fréquence pendant la formation des épis''',
                'theme': 'irrigation_arrosage',
                'niveau_difficulte': 'debutant',
                'auteur': 'Dr. Kouame Jean'
            },
            {
                'titre': 'Irrigation goutte-à-goutte pour le maïs',
                'contenu': '''L'irrigation goutte-à-goutte est la méthode la plus efficace pour le maïs.

Avantages :
• Économise 30-40% d'eau par rapport à l'arrosage traditionnel
• Réduit les maladies foliaires
• Permet une fertilisation précise (fertigation)
• Maintient l'humidité constante du sol

Installation :
• Installez les goutteurs à 30cm de la base de chaque plant
• Débit recommandé : 2-4 litres/heure par goutteur
• Programmez 2-3 sessions par jour de 20-30 minutes''',
                'theme': 'irrigation_arrosage',
                'niveau_difficulte': 'intermediaire',
                'auteur': 'Ing. Agr. Fatou Diallo'
            },
            {
                'titre': 'Gestion de l\'eau pendant la sécheresse',
                'contenu': '''En période de sécheresse, optimisez l'utilisation de l'eau pour votre maïs.

Stratégies :
• Paillez autour des plants pour conserver l'humidité
• Arrosez tôt le matin (5h-7h) pour réduire l'évaporation
• Creusez des cuvettes autour des plants pour retenir l'eau
• Utilisez l'eau de pluie récupérée
• Réduisez la densité de plantation si nécessaire

Signes de stress hydrique :
• Feuilles qui s'enroulent
• Croissance ralentie
• Jaunissement prématuré''',
                'theme': 'irrigation_arrosage',
                'niveau_difficulte': 'avance',
                'auteur': 'Prof. Amadou Traore'
            }
        ]
        
        # Conseils pour le Maïs - Maladies et Parasites
        conseils_mais_maladies = [
            {
                'titre': 'Prévention de la chenille légionnaire',
                'contenu': '''La chenille légionnaire est un ravageur majeur du maïs en Afrique.

Prévention :
• Inspectez vos champs 2 fois par semaine
• Éliminez les mauvaises herbes qui servent d'abri
• Plantez des cultures-pièges comme le sorgho en bordure
• Favorisez les prédateurs naturels (oiseaux, araignées)

Traitement biologique :
• Utilisez Bacillus thuringiensis (Bt)
• Pulvérisez tôt le matin ou tard le soir
• Répétez le traitement après 7 jours si nécessaire''',
                'theme': 'maladies_parasites',
                'niveau_difficulte': 'intermediaire',
                'auteur': 'Dr. Assia Kone'
            },
            {
                'titre': 'Lutte contre la rouille du maïs',
                'contenu': '''La rouille du maïs se manifeste par des pustules orangées sur les feuilles.

Prévention :
• Choisissez des variétés résistantes
• Respectez l'espacement entre les plants
• Évitez l'excès d'azote
• Éliminez les résidus de culture infectés

Traitement :
• Appliquez un fongicide à base de cuivre
• Pulvérisez en prévention si l'humidité est élevée
• Traitez dès l'apparition des premiers symptômes''',
                'theme': 'maladies_parasites',
                'niveau_difficulte': 'debutant',
                'auteur': 'Ing. Agr. Mohamed Sylla'
            }
        ]
        
        # Conseils pour le Haricot - Maladies et Parasites
        conseils_haricot_maladies = [
            {
                'titre': 'Prévention de la rouille du haricot',
                'contenu': '''La rouille du haricot est une maladie fongique courante.

Symptômes :
• Pustules rouge-orangé sous les feuilles
• Jaunissement et chute des feuilles
• Réduction du rendement

Prévention :
• Évitez l'arrosage des feuilles
• Assurez une bonne circulation d'air entre les plants
• Espacez correctement vos plants (20-30 cm)
• Éliminez les feuilles malades

Traitement préventif :
• Pulvérisez une solution de bicarbonate de soude (1 cuillère/litre)
• Appliquez un fongicide à base de cuivre tous les 15 jours''',
                'theme': 'maladies_parasites',
                'niveau_difficulte': 'debutant',
                'auteur': 'Dr. Mariama Toure'
            },
            {
                'titre': 'Lutte contre les pucerons du haricot',
                'contenu': '''Les pucerons attaquent souvent les jeunes pousses de haricot.

Identification :
• Petits insectes verts ou noirs sous les feuilles
• Feuilles collantes (miellat)
• Déformation des feuilles et tiges

Lutte biologique :
• Pulvérisez de l'eau savonneuse (savon noir)
• Introduisez des coccinelles (prédateurs naturels)
• Plantez de la menthe ou du basilic en association

Traitement d'urgence :
• Utilisez un insecticide à base de pyrèthre
• Pulvérisez en fin de journée
• Répétez après 7 jours si nécessaire''',
                'theme': 'maladies_parasites',
                'niveau_difficulte': 'intermediaire',
                'auteur': 'Ing. Agr. Ibrahim Diarra'
            }
        ]
        
        # Conseils pour le Manioc - Techniques de Culture
        conseils_manioc_techniques = [
            {
                'titre': 'Plantation du manioc : bonnes pratiques',
                'contenu': '''Le manioc se plante par boutures pour garantir la qualité.

Préparation des boutures :
• Utilisez des tiges de 20-25 cm
• Choisissez des tiges saines, sans maladies
• Laissez sécher les boutures 2-3 jours avant plantation

Plantation :
• Creusez des trous de 10-15 cm de profondeur
• Inclinez les boutures à 45° avec 2/3 enterrés
• Espacez les plants de 1m x 1m minimum
• Plantez au début de la saison des pluies

Entretien :
• Désherbez régulièrement les 3 premiers mois
• Buttez légèrement autour des plants
• Pas besoin d'arrosage après installation''',
                'theme': 'techniques_culture',
                'niveau_difficulte': 'debutant',
                'auteur': 'Agr. Fatoumata Coulibaly'
            },
            {
                'titre': 'Récolte et conservation du manioc',
                'contenu': '''Le manioc se récolte 8-24 mois après plantation selon la variété.

Signes de maturité :
• Jaunissement des feuilles inférieures
• Épaississement visible des racines
• Test : déterrez une racine pour vérifier la taille

Récolte :
• Récoltez par temps sec
• Coupez les tiges à 20 cm du sol
• Déterrez délicatement avec une houe
• Évitez de blesser les tubercules

Conservation :
• Consommez dans les 2-3 jours (frais)
• Ou transformez en farine, attiéké
• Stockage : dans un endroit frais et aéré
• Évitez l'exposition au soleil''',
                'theme': 'recolte_stockage',
                'niveau_difficulte': 'intermediaire',
                'auteur': 'Prof. Yao N\'guessan'
            }
        ]
        
        # Conseils pour la Tomate - Fertilisation
        conseils_tomate_fertilisation = [
            {
                'titre': 'Programme de fertilisation de la tomate',
                'contenu': '''La tomate est une culture exigeante en nutriments.

Fumure de fond (avant plantation) :
• 20-30 tonnes/ha de fumier bien décomposé
• NPK 10-10-20 : 400-500 kg/ha
• Enfouissez 2 semaines avant plantation

Fertilisation d'entretien :
• 15 jours après plantation : NPK 15-15-15 (200 kg/ha)
• À la floraison : NPK 0-20-30 (150 kg/ha)
• Formation des fruits : NPK 15-5-30 (200 kg/ha)

Fertilisation foliaire :
• Pulvérisez tous les 15 jours
• Solution d'urée à 0,5%
• Ajoutez du bore et du calcium
• Appliquez le matin ou le soir''',
                'theme': 'fertilisation',
                'niveau_difficulte': 'intermediaire',
                'auteur': 'Dr. Adjoua Aya'
            }
        ]
        
        # Conseils généraux - Choix des semences
        conseils_semences = [
            {
                'titre': 'Critères de choix des semences de maïs',
                'contenu': '''Le choix des semences détermine 50% du succès de votre culture.

Critères de sélection :
• Adaptation au climat local
• Résistance aux maladies courantes
• Cycle de production adapté à vos objectifs
• Rendement potentiel
• Qualité nutritionnelle

Variétés recommandées pour la Côte d'Ivoire :
• Précoces (90 jours) : TZPB-SR, DMR-ESR-Y
• Intermédiaires (110 jours) : SAMMAZ-15, SAMMAZ-16
• Tardives (120+ jours) : OBATANPA, QB

Vérification de la qualité :
• Taux de germination > 85%
• Pureté variétale > 98%
• Humidité < 14%
• Absence de parasites''',
                'theme': 'semences',
                'niveau_difficulte': 'intermediaire',
                'auteur': 'Ing. Semencier Koffi Yao'
            }
        ]
        
        # Créer tous les conseils
        tous_les_conseils = []
        
        # Conseils pour le Maïs
        for conseil_data in conseils_mais_irrigation + conseils_mais_maladies:
            conseil_data['type_culture'] = mais
            tous_les_conseils.append(conseil_data)
        
        # Conseils pour le Haricot
        for conseil_data in conseils_haricot_maladies:
            conseil_data['type_culture'] = haricot
            tous_les_conseils.append(conseil_data)
        
        # Conseils pour le Manioc
        for conseil_data in conseils_manioc_techniques:
            conseil_data['type_culture'] = manioc
            tous_les_conseils.append(conseil_data)
        
        # Conseils pour la Tomate
        for conseil_data in conseils_tomate_fertilisation:
            conseil_data['type_culture'] = tomate
            tous_les_conseils.append(conseil_data)
        
        # Conseils pour les semences (Maïs)
        for conseil_data in conseils_semences:
            conseil_data['type_culture'] = mais
            tous_les_conseils.append(conseil_data)
        
        # Créer les conseils en base
        conseils_crees = 0
        for conseil_data in tous_les_conseils:
            conseil, created = ConseilAgricole.objects.get_or_create(
                titre=conseil_data['titre'],
                type_culture=conseil_data['type_culture'],
                defaults=conseil_data
            )
            if created:
                conseils_crees += 1
                self.stdout.write(f'  ✓ Créé: {conseil.titre}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Terminé ! {conseils_crees} nouveaux conseils créés.'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Total des conseils en base : {ConseilAgricole.objects.count()}'
            )
        )
