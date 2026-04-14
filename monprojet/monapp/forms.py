from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from .models import Agriculteur, TypeCulture, DemandeExpert, Expert

class CustomUserCreationForm(UserCreationForm):
    ROLE_CHOICES = [
        ('agriculteur', 'Agriculteur'),
        ('expert', 'Expert Agricole'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        required=True,
        widget=forms.RadioSelect(attrs={
            'class': 'role-radio'
        }),
        label="Je souhaite m'inscrire en tant que :"
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-green-300 rounded-md',
            'placeholder': 'votre.email@exemple.com'
        })
    )
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-green-300 rounded-md',
            'placeholder': 'Votre prénom'
        })
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-green-300 rounded-md',
            'placeholder': 'Votre nom'
        })
    )
    
    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2", "role")
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-green-300 rounded-md',
                'placeholder': 'Nom d\'utilisateur'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-green-300 rounded-md'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-green-300 rounded-md'
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée.")
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            # Créer le profil correspondant selon le rôle
            role = self.cleaned_data.get('role')
            if role == 'agriculteur':
                Agriculteur.objects.create(user=user)
            elif role == 'expert':
                Expert.objects.create(
                    user=user,
                    nom=user.last_name,
                    prenom=user.first_name,
                    email=user.email
                )
        return user

class AgriculteurForm(forms.ModelForm):
    phone_validator = RegexValidator(
        regex=r'^\+?225?\d{8,10}$',
        message="Format: +225XXXXXXXX ou 225XXXXXXXX"
    )
    
    contact = forms.CharField(
        validators=[phone_validator],
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '+225 XX XX XX XX XX',
            'class': 'w-full px-3 py-2 border border-green-300 rounded-md'
        })
    )
    
    cultures_pratiquees = forms.ModelMultipleChoiceField(
        queryset=TypeCulture.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = Agriculteur
        fields = ['contact', 'localisation', 'superficie', 'photo', 'cultures_pratiquees']
        widgets = {
            'localisation': forms.TextInput(attrs={
                'placeholder': 'Ex: Abidjan, Côte d\'Ivoire',
                'class': 'w-full px-3 py-2 border border-green-300 rounded-md'
            }),
            'superficie': forms.TextInput(attrs={
                'placeholder': 'Ex: 2.5 hectares',
                'class': 'w-full px-3 py-2 border border-green-300 rounded-md'
            }),
            'photo': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'w-full px-3 py-2 border border-green-300 rounded-md bg-white'
            }),
        }
    
    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo:
            if photo.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError("La photo ne peut pas dépasser 5MB.")
            if not photo.content_type.startswith('image/'):
                raise forms.ValidationError("Veuillez uploader une image valide.")
        return photo


class DemandeExpertForm(forms.ModelForm):
    class Meta:
        model = DemandeExpert
        fields = ['domaine_demande', 'sujet', 'description', 'urgence']
        widgets = {
            'domaine_demande': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-green-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500'
            }),
            'sujet': forms.TextInput(attrs={
                'placeholder': 'Ex: Problème de parasites sur mes tomates',
                'class': 'w-full px-3 py-2 border border-green-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Décrivez en détail votre problème ou votre demande...',
                'rows': 5,
                'class': 'w-full px-3 py-2 border border-green-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500'
            }),
            'urgence': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-green-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500'
            }),
        }
        labels = {
            'domaine_demande': 'Domaine d\'expertise requis',
            'sujet': 'Sujet de votre demande',
            'description': 'Description détaillée',
            'urgence': 'Niveau d\'urgence',
        }
        help_texts = {
            'description': 'Plus votre description sera détaillée, mieux l\'expert pourra vous aider.',
            'urgence': 'Sélectionnez le niveau d\'urgence approprié pour votre situation.',
        }

class ExpertRegistrationForm(forms.ModelForm):
    """Formulaire spécialisé pour l'inscription des experts"""
    
    DOMAINE_CHOICES = [
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
    
    # Champs de base utilisateur
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-purple-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
            'placeholder': 'Votre prénom'
        }),
        label='Prénom'
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-purple-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
            'placeholder': 'Votre nom'
        }),
        label='Nom'
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-purple-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
            'placeholder': 'votre.email@exemple.com'
        }),
        label='Adresse email'
    )
    
    # Champs de mot de passe
    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-purple-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
            'placeholder': 'Mot de passe'
        }),
        label='Mot de passe',
        help_text='Minimum 8 caractères avec lettres et chiffres'
    )
    
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-purple-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
            'placeholder': 'Confirmez le mot de passe'
        }),
        label='Confirmation du mot de passe'
    )
    
    # Champs spécifiques à l'expert
    specialite = forms.ChoiceField(
        choices=DOMAINE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-purple-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
        }),
        label='Domaine de spécialité principal'
    )
    
    experience = forms.ChoiceField(
        choices=EXPERIENCE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-purple-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
        }),
        label='Années d\'expérience'
    )
    
    statut_professionnel = forms.ChoiceField(
        choices=STATUT_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-purple-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
        }),
        label='Statut professionnel'
    )
    
    formation = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-purple-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
            'placeholder': 'Ex: Master en Agronomie, École Supérieure d\'Agriculture'
        }),
        label='Formation principale',
        help_text='Diplôme principal ou formation la plus pertinente'
    )
    
    certifications = forms.CharField(
        max_length=300,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-purple-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
            'placeholder': 'Ex: Certification en Agriculture Biologique, Phytolicence'
        }),
        label='Certifications et agréments',
        help_text='Certifications professionnelles, agréments officiels (optionnel)'
    )
    
    localisation = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-purple-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
            'placeholder': 'Ex: Abidjan, Bouaké, San-Pédro'
        }),
        label='Localisation',
        help_text='Ville ou région où vous exercez principalement'
    )
    
    bio = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-purple-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
            'rows': 4,
            'placeholder': 'Présentez-vous en quelques mots : votre parcours, votre expertise, vos domaines de prédilection...'
        }),
        label='Présentation professionnelle',
        help_text='Décrivez votre parcours et votre expertise (maximum 500 caractères)',
        max_length=500,
        required=True
    )
    
    contact = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-purple-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
            'placeholder': '+225 XX XX XX XX XX'
        }),
        label='Téléphone',
        help_text='Numéro de téléphone professionnel (optionnel)'
    )
    
    disponibilite = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-purple-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
            'placeholder': 'Ex: Disponible du lundi au vendredi, consultations le weekend'
        }),
        label='Disponibilité',
        help_text='Précisez vos créneaux de disponibilité (optionnel)'
    )
    
    class Meta:
        model = Expert
        fields = ['specialite', 'experience', 'bio', 'contact', 'localisation']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée.")
        return email
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1 and len(password1) < 8:
            raise forms.ValidationError("Le mot de passe doit contenir au moins 8 caractères.")
        if password1 and password1.isdigit():
            raise forms.ValidationError("Le mot de passe ne peut pas être entièrement numérique.")
        if password1 and password1.isalpha():
            raise forms.ValidationError("Le mot de passe doit contenir au moins un chiffre.")
        return password1
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return password2
    
    def clean_bio(self):
        bio = self.cleaned_data.get('bio')
        if bio and len(bio) < 50:
            raise forms.ValidationError("La présentation doit contenir au moins 50 caractères.")
        return bio