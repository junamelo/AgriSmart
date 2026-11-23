from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class TypeCulture(models.Model):
    STATUT_SAISON_CHOICES = [
        ('en_saison', 'En saison'),
        ('fin_saison', 'Fin de saison'),
        ('preparation', 'Préparation'),
        ('hors_saison', 'Hors saison'),
    ]
    
    COULEUR_STATUT = {
        'en_saison': 'green',
        'fin_saison': 'yellow',
        'preparation': 'blue',
        'hors_saison': 'gray',
    }
    
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True, help_text="URL de l'image de la culture")
    statut_saison = models.CharField(max_length=20, choices=STATUT_SAISON_CHOICES, default='en_saison')
    periode_semis_debut = models.IntegerField(help_text="Mois de début (1-12)", null=True, blank=True)
    periode_semis_fin = models.IntegerField(help_text="Mois de fin (1-12)", null=True, blank=True)
    
    def __str__(self):
        return self.nom
    
    @property
    def statut_couleur(self):
        return self.COULEUR_STATUT.get(self.statut_saison, 'gray')


class Agriculteur(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    contact = models.CharField(max_length=15, blank=True)
    localisation = models.CharField(max_length=200, blank=True)
    superficie = models.CharField(max_length=50, blank=True, help_text="Ex: 2.5 hectares")
    photo = models.ImageField(upload_to='profils/', blank=True, null=True)
    cultures_pratiquees = models.ManyToManyField(TypeCulture, blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"


class ConseilAgricole(models.Model):
    THEMES_CHOICES = [
        ('irrigation_arrosage', 'Irrigation et Arrosage'),
        ('maladies_parasites', 'Lutte contre les Maladies et Parasites'),
        ('techniques_culture', 'Techniques de Culture'),
        ('semences', 'Choix des Semences'),
        ('fertilisation', 'Fertilisation'),
        ('recolte_stockage', 'Récolte et Stockage'),
    ]
    
    NIVEAU_DIFFICULTE = [
        ('debutant', 'Débutant'),
        ('intermediaire', 'Intermédiaire'),
        ('avance', 'Avancé'),
    ]
    
    titre = models.CharField(max_length=200)
    theme = models.CharField(max_length=30, choices=THEMES_CHOICES)
    contenu = models.TextField()
    type_culture = models.ForeignKey(TypeCulture, on_delete=models.CASCADE)
    niveau_difficulte = models.CharField(max_length=20, choices=NIVEAU_DIFFICULTE, default='debutant')
    auteur = models.CharField(max_length=100, blank=True, help_text="Auteur du conseil")
    date_creation = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.type_culture.nom} - {self.get_theme_display()}: {self.titre}"
    
    class Meta:
        verbose_name = "Conseil agricole"
        verbose_name_plural = "Conseils agricoles"
        ordering = ['-date_creation']


class ActiviteAgricole(models.Model):
    TYPES_ACTIVITE = [
        ('semis', 'Semis'),
        ('fertilisation', 'Fertilisation'),
        ('traitement', 'Traitement'),
        ('irrigation', 'Irrigation'),
        ('entretien', 'Entretien'),
        ('recolte', 'Récolte'),
    ]
    
    agriculteur = models.ForeignKey(Agriculteur, on_delete=models.CASCADE)
    type_culture = models.ForeignKey(TypeCulture, on_delete=models.CASCADE)
    type_activite = models.CharField(max_length=20, choices=TYPES_ACTIVITE)
    date_prevue = models.DateField()
    description = models.TextField(blank=True)
    terminee = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['date_prevue']
        verbose_name = "Activité agricole"
        verbose_name_plural = "Activités agricoles"
    
    def __str__(self):
        return f"{self.get_type_activite_display()} - {self.type_culture} - {self.date_prevue}"


class Expert(models.Model):
    DOMAINES_CHOICES = [
        ('cultures_cerealieres', 'Cultures Céréalières'),
        ('cultures_maraicheres', 'Cultures Maraîchères'),
        ('cultures_fruitieres', 'Cultures Fruitières'),
        ('elevage', 'Élevage'),
        ('irrigation', 'Irrigation et Gestion de l\'Eau'),
        ('sols_fertilisation', 'Sols et Fertilisation'),
        ('phytosanitaire', 'Protection Phytosanitaire'),
        ('machinisme', 'Machinisme Agricole'),
        ('economie_agricole', 'Économie Agricole'),
        ('agriculture_biologique', 'Agriculture Biologique'),
        ('agroecologie', 'Agroécologie'),
        ('autre', 'Autre Spécialité'),
    ]
    
    EXPERIENCE_CHOICES = [
        ('1-3', '1 à 3 ans'),
        ('4-7', '4 à 7 ans'),
        ('8-15', '8 à 15 ans'),
        ('16-25', '16 à 25 ans'),
        ('25+', 'Plus de 25 ans'),
    ]
    
    STATUT_CHOICES = [
        ('ingenieur_agronome', 'Ingénieur Agronome'),
        ('technicien_agricole', 'Technicien Agricole'),
        ('consultant', 'Consultant Indépendant'),
        ('agriculteur_expert', 'Agriculteur Expérimenté'),
        ('chercheur', 'Chercheur'),
        ('enseignant', 'Enseignant/Formateur'),
        ('veterinaire', 'Vétérinaire'),
        ('autre', 'Autre'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Informations de base (pour compatibilité avec l'existant)
    nom = models.CharField(max_length=100, blank=True)
    prenom = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    
    # Informations professionnelles
    specialite = models.CharField(max_length=50, choices=DOMAINES_CHOICES, default='autre')
    domaines_expertise = models.CharField(max_length=50, choices=DOMAINES_CHOICES, blank=True)  # Pour compatibilité
    experience = models.CharField(max_length=10, choices=EXPERIENCE_CHOICES, default='1-3')
    statut_professionnel = models.CharField(max_length=30, choices=STATUT_CHOICES, default='autre')
    formation = models.CharField(max_length=200, blank=True)
    certifications = models.CharField(max_length=300, blank=True)
    
    # Informations de contact
    contact = models.CharField(max_length=15, blank=True)
    localisation = models.CharField(max_length=100, blank=True)
    
    # Présentation et disponibilité
    bio = models.TextField(max_length=500, blank=True)
    disponibilite = models.CharField(max_length=200, blank=True)
    disponible = models.BooleanField(default=True)
    
    # Statut et validation
    est_verifie = models.BooleanField(default=False)
    note_moyenne = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    nombre_consultations = models.IntegerField(default=0)
    
    # Photo
    photo = models.ImageField(upload_to='experts/', blank=True, null=True)
    
    # Dates
    date_inscription = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    date_verification = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Expert {self.user.get_full_name() or self.user.username} - {self.get_specialite_display()}"
    
    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}".strip() or self.user.get_full_name()
    
    def save(self, *args, **kwargs):
        # Synchroniser avec les données utilisateur
        if not self.nom and self.user.last_name:
            self.nom = self.user.last_name
        if not self.prenom and self.user.first_name:
            self.prenom = self.user.first_name
        if not self.email and self.user.email:
            self.email = self.user.email
        
        # Synchroniser domaines_expertise avec specialite pour compatibilité
        if self.specialite and not self.domaines_expertise:
            self.domaines_expertise = self.specialite
            
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Expert"
        verbose_name_plural = "Experts"


class DemandeExpert(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('acceptee', 'Acceptée'),
        ('en_cours', 'En cours de traitement'),
        ('terminee', 'Terminée'),
        ('refusee', 'Refusée'),
    ]
    
    URGENCE_CHOICES = [
        ('faible', 'Faible'),
        ('normale', 'Normale'),
        ('elevee', 'Élevée'),
        ('critique', 'Critique'),
    ]
    
    agriculteur = models.ForeignKey(Agriculteur, on_delete=models.CASCADE)
    expert = models.ForeignKey(Expert, on_delete=models.SET_NULL, null=True, blank=True)
    domaine_demande = models.CharField(max_length=50, choices=Expert.DOMAINES_CHOICES)
    sujet = models.CharField(max_length=200)
    description = models.TextField()
    urgence = models.CharField(max_length=10, choices=URGENCE_CHOICES, default='normale')
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='en_attente')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    
    # Champs pour les réponses de l'expert
    reponse = models.TextField(blank=True, help_text="Réponse de l'expert à la demande")
    date_reponse = models.DateTimeField(null=True, blank=True, help_text="Date de la réponse de l'expert")
    
    # Évaluation optionnelle de l'agriculteur
    note_satisfaction = models.IntegerField(null=True, blank=True, help_text="Note de 1 à 5")
    commentaire_satisfaction = models.TextField(blank=True, help_text="Commentaire de l'agriculteur")
    
    def __str__(self):
        return f"Demande {self.sujet} - {self.agriculteur}"
    
    @property
    def a_reponse(self):
        """Vérifie si l'expert a répondu à la demande"""
        return bool(self.reponse and self.reponse.strip())
    
    @property  
    def est_en_cours(self):
        """Vérifie si la demande est en cours de traitement"""
        return self.statut in ['acceptee', 'en_cours']
    
    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Demande d'expert"
        verbose_name_plural = "Demandes d'experts"


class MessageDiscussion(models.Model):
    demande = models.ForeignKey(DemandeExpert, on_delete=models.CASCADE, related_name='messages_discussion')
    auteur = models.ForeignKey(User, on_delete=models.CASCADE)
    contenu = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)

    def __str__(self):
        return f"Message de {self.auteur} sur {self.demande}"

    class Meta:
        ordering = ['date_envoi']
        verbose_name = 'Message de discussion'
        verbose_name_plural = 'Messages de discussion'
