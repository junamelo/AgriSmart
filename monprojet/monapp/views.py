from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from .models import TypeCulture, ActiviteAgricole, ConseilAgricole, Agriculteur, Expert, DemandeExpert, MessageDiscussion  # Assurez-vous d'importer votre modèle
from django.http import JsonResponse
import json
from datetime import datetime
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.shortcuts import redirect
from .forms import CustomUserCreationForm, AgriculteurForm, DemandeExpertForm, ExpertRegistrationForm
from django.utils import timezone
import logging
from .utils import LoginAttemptLimiter, get_client_ip, get_user_dashboard_url

logger = logging.getLogger(__name__)

# Create your views here.


def authenticate_by_username_or_email(request, identifier, password):
    """Authenticate a user by username first, then by email if needed."""
    user = authenticate(request, username=identifier, password=password)
    if user is not None:
        return user

    try:
        matched_user = User.objects.get(email__iexact=identifier)
    except User.DoesNotExist:
        return None

    return authenticate(request, username=matched_user.username, password=password)

@login_required
def compte_view(request):
    # Récupérer ou créer le profil agriculteur
    agriculteur, created = Agriculteur.objects.get_or_create(
        user=request.user,
        defaults={
            'contact': '',
            'localisation': '',
            'superficie': ''
        }
    )
    
    if created:
        messages.info(request, 'Votre profil agriculteur a été créé automatiquement. Complétez vos informations ci-dessous.')
    
    # Conseils personnalisés basés sur les cultures de l'utilisateur
    conseils_personnalises = []
    if agriculteur and agriculteur.cultures_pratiquees.exists():
        # Base de conseils par culture avec saison
        conseils_par_culture = {
            'Maïs': {
                'aout': {
                    'message': 'Période de floraison : surveillez l\'arrosage et appliquez de l\'engrais potassique.',
                    'couleur': 'blue'
                },
                'septembre': {
                    'message': 'Formation des épis : augmentez l\'irrigation et protégez contre les oiseaux.',
                    'couleur': 'green'
                },
                'defaut': {
                    'message': 'Vérifiez régulièrement l\'état des feuilles et traitez les parasites.',
                    'couleur': 'yellow'
                }
            },
            'Manioc': {
                'aout': {
                    'message': 'Période de croissance active : désherbez et buttez les plants.',
                    'couleur': 'green'
                },
                'septembre': {
                    'message': 'Surveillez les attaques de mosaïque et retirez les plants infectés.',
                    'couleur': 'red'
                },
                'defaut': {
                    'message': 'Culture résistante : vérifiez l\'état sanitaire et buttez si nécessaire.',
                    'couleur': 'blue'
                }
            },
            'Tomates': {
                'aout': {
                    'message': 'Période de fructification : taillez les gourmands et traitez contre le mildiou.',
                    'couleur': 'orange'
                },
                'septembre': {
                    'message': 'Récolte continue : cueillez régulièrement et surveillez les maladies.',
                    'couleur': 'green'
                },
                'defaut': {
                    'message': 'Arrosage régulier nécessaire : évitez de mouiller les feuilles.',
                    'couleur': 'blue'
                }
            },
            'Banane': {
                'aout': {
                    'message': 'Période humide favorable : éliminez les rejets en excès.',
                    'couleur': 'green'
                },
                'septembre': {
                    'message': 'Surveillez les charançons et appliquez un traitement préventif.',
                    'couleur': 'red'
                },
                'defaut': {
                    'message': 'Maintenez l\'humidité du sol et taillez les feuilles sèches.',
                    'couleur': 'blue'
                }
            },
            'Riz': {
                'aout': {
                    'message': 'Période de tallage : maintenez le niveau d\'eau et appliquez l\'urée.',
                    'couleur': 'blue'
                },
                'septembre': {
                    'message': 'Formation des panicules : surveillez les oiseaux et les parasites.',
                    'couleur': 'yellow'
                },
                'defaut': {
                    'message': 'Gestion de l\'eau cruciale : maintenez la lame d\'eau appropriée.',
                    'couleur': 'blue'
                }
            },
            'Haricot': {
                'aout': {
                    'message': 'Période de floraison : évitez l\'excès d\'azote et surveillez l\'arrosage.',
                    'couleur': 'yellow'
                },
                'septembre': {
                    'message': 'Formation des gousses : traitez contre les pucerons si nécessaire.',
                    'couleur': 'green'
                },
                'defaut': {
                    'message': 'Culture sensible : évitez l\'humidité excessive et les sols compacts.',
                    'couleur': 'orange'
                }
            }
        }
        
        # Mois actuel pour contextualiser les conseils
        import datetime
        mois_actuel = datetime.datetime.now().strftime('%B').lower()
        mois_mapping = {
            'august': 'aout',
            'september': 'septembre',
            'october': 'octobre',
            'november': 'novembre'
        }
        mois_francais = mois_mapping.get(mois_actuel, 'defaut')
        
        # Génération des conseils pour chaque culture de l'agriculteur
        for culture in agriculteur.cultures_pratiquees.all():
            culture_nom = culture.nom
            if culture_nom in conseils_par_culture:
                conseil_data = conseils_par_culture[culture_nom].get(
                    mois_francais, 
                    conseils_par_culture[culture_nom]['defaut']
                )
                conseils_personnalises.append({
                    'culture': culture_nom,
                    'message': conseil_data['message'],
                    'couleur': conseil_data['couleur']
                })
            else:
                # Conseil générique pour les cultures non répertoriées
                conseils_personnalises.append({
                    'culture': culture_nom,
                    'message': f'Surveillez l\'état sanitaire de vos plants de {culture_nom.lower()} et adaptez l\'irrigation selon les conditions.',
                    'couleur': 'gray'
                })
        
        # Si pas de cultures spécifiques, conseil général
        if not conseils_personnalises:
            conseils_personnalises.append({
                'culture': 'Général',
                'message': 'Ajoutez vos cultures dans votre profil pour recevoir des conseils personnalisés.',
                'couleur': 'blue'
            })
    
    # Prochaines activités récupérées depuis la base de données
    prochaines_activites = []
    if agriculteur:
        from datetime import datetime, date as date_class, timedelta
        today = date_class.today()
        
        # Récupérer les activités futures de l'agriculteur (30 prochains jours maximum)
        try:
            activites_futures = ActiviteAgricole.objects.filter(
                agriculteur=agriculteur,
                date_prevue__gte=today,
                terminee=False  # Seulement les activités non terminées
            ).order_by('date_prevue')[:10]  # Limiter à 10 activités
            
            for activite in activites_futures:
                # Déterminer la priorité basée sur la proximité de la date
                days_until = (activite.date_prevue - today).days
                if days_until <= 3:
                    priorite = 'haute'
                elif days_until <= 7:
                    priorite = 'moyenne'
                else:
                    priorite = 'basse'
                
                # Créer un titre complet pour l'activité
                titre_activite = f"{activite.get_type_activite_display()}"
                if activite.description:
                    titre_activite += f" - {activite.description[:50]}{'...' if len(activite.description) > 50 else ''}"
                
                prochaines_activites.append({
                    'date': activite.date_prevue,
                    'type': titre_activite,
                    'culture': activite.type_culture.nom,
                    'priorite': priorite,
                    'id': activite.id
                })
                
        except Exception as e:
            logger.exception("Erreur lors de la récupération des activités: %s", e)
        
        # Si pas d'activités programmées, proposer des activités suggérées basées sur les cultures
        if not prochaines_activites and agriculteur.cultures_pratiquees.exists():
            # Activités suggérées par culture
            activites_suggerees = {
                'Maïs': [
                    {'type': 'Fertilisation potassique', 'jours': 3},
                    {'type': 'Surveillance des parasites', 'jours': 7},
                ],
                'Manioc': [
                    {'type': 'Désherbage', 'jours': 2},
                    {'type': 'Buttage des plants', 'jours': 10},
                ],
                'Tomates': [
                    {'type': 'Taille des gourmands', 'jours': 1},
                    {'type': 'Traitement préventif mildiou', 'jours': 5},
                ],
                'Banane': [
                    {'type': 'Élimination des rejets', 'jours': 4},
                    {'type': 'Taille des feuilles sèches', 'jours': 8},
                ],
                'Riz': [
                    {'type': 'Contrôle du niveau d\'eau', 'jours': 2},
                    {'type': 'Application d\'engrais', 'jours': 6},
                ],
                'Haricot': [
                    {'type': 'Surveillance des pucerons', 'jours': 3},
                    {'type': 'Vérification de la floraison', 'jours': 9},
                ]
            }
            
            for culture in agriculteur.cultures_pratiquees.all():
                if culture.nom in activites_suggerees:
                    for activite_suggere in activites_suggerees[culture.nom][:1]:  # 1 par culture
                        date_suggestion = today + timedelta(days=activite_suggere['jours'])
                        prochaines_activites.append({
                            'date': date_suggestion,
                            'type': f"{activite_suggere['type']} (suggéré)",
                            'culture': culture.nom,
                            'priorite': 'moyenne',
                            'id': None,  # Pas d'ID car c'est une suggestion
                            'suggested': True
                        })
    
    # Si toujours pas d'activités, afficher un message par défaut
    if not prochaines_activites:
        from datetime import date as date_class, timedelta
        prochaines_activites = [
            {
                'date': date_class.today() + timedelta(days=1),
                'type': 'Planifiez vos premières activités agricoles',
                'culture': 'Général',
                'priorite': 'basse',
                'id': None,
                'suggested': True
            }
        ]
    
    context = {
        'agriculteur': agriculteur,
        'conseils_personnalises': conseils_personnalises,
        'prochaines_activites': prochaines_activites,
        'cultures_disponibles': TypeCulture.objects.exclude(
            id__in=agriculteur.cultures_pratiquees.all() if agriculteur else []
        ) if agriculteur else TypeCulture.objects.all(),
    }
    
    return render(request, 'monapp/compte.html', context)

def index_view(request):
    # Récupération des cultures saisonnières
    cultures_saisonnieres = TypeCulture.objects.all()[:4]  # Limiter à 4 cultures
    
    # Si pas de données en base, on peut créer des données d'exemple
    if not cultures_saisonnieres.exists():
        cultures_saisonnieres = [
            {
                'nom': 'Maïs',
                'description': 'Culture de saison humide, période idéale de plantation.',
                'statut_saison': 'En saison',
                'statut_couleur': 'green',
                'image_url': 'https://images.unsplash.com/photo-1594282416549-65a935d968e9?ixlib=rb-4.0.3&auto=format&fit=crop&w=1470&q=80'
            },
            {
                'nom': 'Manioc',
                'description': 'Culture résistante, adaptée aux sols pauvres.',
                'statut_saison': 'En saison',
                'statut_couleur': 'green',
                'image_url': 'https://images.unsplash.com/photo-1550583721-586fbafc9d1d?ixlib=rb-4.0.3&auto=format&fit=crop&w=1471&q=80'
            },
            {
                'nom': 'Tomates',
                'description': 'Nécessite un bon ensoleillement et un arrosage régulier.',
                'statut_saison': 'Fin de saison',
                'statut_couleur': 'yellow',
                'image_url': 'https://images.unsplash.com/photo-1594282486552-01a2290f8e23?ixlib=rb-4.0.3&auto=format&fit=crop&w=1470&q=80'
            },
            {
                'nom': 'Haricots',
                'description': 'Culture à cycle court, enrichit le sol en azote.',
                'statut_saison': 'Préparation',
                'statut_couleur': 'blue',
                'image_url': 'https://images.unsplash.com/photo-1594282486552-01a2290f8e23?ixlib=rb-4.0.3&auto=format&fit=crop&w=1470&q=80'
            }
        ]
    
    context = {
        'cultures_saisonnieres': cultures_saisonnieres,
    }
    
    return render(request, 'monapp/index.html', context)

@login_required
def calendrier_view(request):
    cultures_utilisateur = []
    culture_selectionnee = None
    activites_utilisateur = []
    
    # Traitement POST pour ajouter/modifier/supprimer des activités
    if request.method == 'POST':
        try:
            agriculteur = request.user.agriculteur
            action = request.POST.get('action', 'add')
            
            if action == 'add':
                # Ajouter une nouvelle activité
                type_culture = TypeCulture.objects.get(id=request.POST['type_culture'])
                ActiviteAgricole.objects.create(
                    agriculteur=agriculteur,
                    type_culture=type_culture,
                    type_activite=request.POST['type_activite'],
                    date_prevue=request.POST['date_prevue'],
                    description=request.POST.get('description', '')
                )
                messages.success(request, 'Activité ajoutée avec succès!')
                
            elif action == 'edit':
                # Modifier une activité existante
                activity_id = request.POST['activity_id']
                activite = ActiviteAgricole.objects.get(
                    id=activity_id,
                    agriculteur=agriculteur
                )
                activite.type_activite = request.POST['type_activite']
                activite.date_prevue = request.POST['date_prevue']
                activite.description = request.POST.get('description', '')
                activite.type_culture = TypeCulture.objects.get(id=request.POST['type_culture'])
                activite.save()
                messages.success(request, 'Activité modifiée avec succès!')
                
            elif action == 'delete':
                # Supprimer une activité
                activity_id = request.POST['activity_id']
                ActiviteAgricole.objects.filter(
                    id=activity_id,
                    agriculteur=agriculteur
                ).delete()
                messages.success(request, 'Activité supprimée avec succès!')
                
            return redirect('monapp:calendrier')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'opération: {str(e)}')
    
    try:
        agriculteur = request.user.agriculteur
        cultures_utilisateur = agriculteur.cultures_pratiquees.all()
        if cultures_utilisateur:
            culture_selectionnee = cultures_utilisateur.first()
            # Afficher toutes les activités de l'utilisateur, toutes cultures confondues
            activites_utilisateur = ActiviteAgricole.objects.filter(
                agriculteur=agriculteur
            ).order_by('date_prevue')
    except Agriculteur.DoesNotExist:
        cultures_utilisateur = []
        activites_utilisateur = []
    
    # Activités par défaut pour la culture sélectionnée
    activites_defaut = [
        {
            'nom': 'Semis',
            'description': 'Période idéale: début saison des pluies',
            'couleur': 'emerald',
            'icone': 'fas fa-seedling',
            'periode': 'Mars - Avril'
        },
        {
            'nom': 'Fertilisation',
            'description': '3-4 semaines après semis',
            'couleur': 'purple',
            'icone': 'fas fa-leaf',
            'periode': 'Avril - Mai'
        },
        {
            'nom': 'Irrigation',
            'description': 'Arrosage régulier pendant la croissance',
            'couleur': 'cyan',
            'icone': 'fas fa-tint',
            'periode': 'Hebdomadaire'
        },
        {
            'nom': 'Entretien',
            'description': 'Désherbage et sarclage',
            'couleur': 'amber',
            'icone': 'fas fa-tools',
            'periode': 'Mensuel'
        },
        {
            'nom': 'Récolte',
            'description': '90-120 jours après semis',
            'couleur': 'orange',
            'icone': 'fas fa-wheat-awn',
            'periode': 'Août - Septembre'
        }
    ]
    
    # Conversion en JSON pour JavaScript
    activites_utilisateur_json = json.dumps([
        {
            'id': activite.id,
            'type_activite': activite.type_activite,
            'date_prevue': activite.date_prevue.isoformat(),
            'description': activite.description,
            'type_culture_id': activite.type_culture.id
        }
        for activite in activites_utilisateur
    ])
    
    context = {
        'cultures_utilisateur': cultures_utilisateur,
        'culture_selectionnee': culture_selectionnee,
        'activites_utilisateur': activites_utilisateur,
        'activites_utilisateur_json': activites_utilisateur_json,
        'activites_defaut': activites_defaut,
        'mois_actuel': datetime.now().strftime('%B %Y'),
    }
    
    return render(request, 'monapp/calendrier.html', context)

def conseils_view(request):
    """Vue pour les conseils avec filtrage personnalisé selon les cultures de l'utilisateur"""
    
    # Vérifier si l'utilisateur est connecté et a un profil agriculteur
    cultures_utilisateur = []
    if request.user.is_authenticated:
        try:
            agriculteur = request.user.agriculteur
            cultures_utilisateur = agriculteur.cultures_pratiquees.all()
        except Agriculteur.DoesNotExist:
            cultures_utilisateur = []
    
    # Si l'utilisateur n'est pas connecté ou n'a pas de cultures, afficher tous les conseils
    if not cultures_utilisateur:
        conseils = ConseilAgricole.objects.all().select_related('type_culture').order_by('-date_creation')
        cultures_pour_filtre = TypeCulture.objects.all()
    else:
        # Filtrer les conseils selon les cultures de l'utilisateur
        conseils = ConseilAgricole.objects.filter(
            type_culture__in=cultures_utilisateur
        ).select_related('type_culture').order_by('-date_creation')
        cultures_pour_filtre = cultures_utilisateur
    
    # Récupération des filtres de la requête
    culture_selectionnee = request.GET.get('culture')
    theme_selectionne = request.GET.get('theme')
    search_query = request.GET.get('q', '')
    
    # Application des filtres
    if culture_selectionnee:
        try:
            culture_obj = TypeCulture.objects.get(id=culture_selectionnee)
            # Vérifier que la culture est dans les cultures de l'utilisateur
            if not cultures_utilisateur or culture_obj in cultures_utilisateur:
                conseils = conseils.filter(type_culture=culture_obj)
        except TypeCulture.DoesNotExist:
            pass
    
    if theme_selectionne:
        conseils = conseils.filter(theme=theme_selectionne)
    
    if search_query:
        conseils = conseils.filter(
            Q(titre__icontains=search_query) | 
            Q(contenu__icontains=search_query)
        )
    
    # Organiser les conseils par catégorie pour l'affichage
    conseils_organises = {}
    for conseil in conseils:
        theme_display = conseil.get_theme_display()
        if theme_display not in conseils_organises:
            conseils_organises[theme_display] = []
        conseils_organises[theme_display].append(conseil)
    
    # Pagination
    paginator = Paginator(conseils, 12)  # 12 conseils par page
    page_number = request.GET.get('page')
    conseils_paginated = paginator.get_page(page_number)
    
    # Données pour les filtres
    themes_conseils = ConseilAgricole.THEMES_CHOICES
    
    # Comptage des conseils par thème (seulement pour les cultures de l'utilisateur)
    conseils_counts = {}
    for theme_key, theme_label in themes_conseils:
        if cultures_utilisateur:
            count = ConseilAgricole.objects.filter(
                theme=theme_key, 
                type_culture__in=cultures_utilisateur
            ).count()
        else:
            count = ConseilAgricole.objects.filter(theme=theme_key).count()
        conseils_counts[theme_key] = count
    
    context = {
        'conseils': conseils_paginated,
        'conseils_organises': conseils_organises,
        'cultures_utilisateur': cultures_utilisateur,
        'cultures_pour_filtre': cultures_pour_filtre,
        'themes_conseils': themes_conseils,
        'conseils_counts': conseils_counts,
        'culture_selectionnee': culture_selectionnee,
        'theme_selectionne': theme_selectionne,
        'search_query': search_query,
        'total_conseils': conseils.count(),
        'is_filtered': bool(culture_selectionnee or theme_selectionne or search_query),
    }
    
    return render(request, 'monapp/conseils.html', context)

def filtrer_conseils_ajax(request):
    """Vue AJAX pour le filtrage dynamique des conseils"""
    if request.method == 'GET':
        culture_id = request.GET.get('culture_id')
        theme = request.GET.get('theme')
        
        # Récupérer les cultures de l'utilisateur si connecté
        cultures_utilisateur = []
        if request.user.is_authenticated:
            try:
                agriculteur = request.user.agriculteur
                cultures_utilisateur = agriculteur.cultures_pratiquees.all()
            except Agriculteur.DoesNotExist:
                pass
        
        # Base queryset
        if cultures_utilisateur:
            conseils = ConseilAgricole.objects.filter(type_culture__in=cultures_utilisateur)
        else:
            conseils = ConseilAgricole.objects.all()
        
        # Appliquer les filtres
        if culture_id:
            try:
                culture_obj = TypeCulture.objects.get(id=culture_id)
                if not cultures_utilisateur or culture_obj in cultures_utilisateur:
                    conseils = conseils.filter(type_culture=culture_obj)
            except TypeCulture.DoesNotExist:
                pass
        
        if theme:
            conseils = conseils.filter(theme=theme)
        
        # Préparer les données de réponse
        conseils_data = []
        for conseil in conseils.select_related('type_culture')[:20]:  # Limiter à 20 résultats
            conseils_data.append({
                'id': conseil.id,
                'titre': conseil.titre,
                'contenu': conseil.contenu[:200] + '...' if len(conseil.contenu) > 200 else conseil.contenu,
                'culture': conseil.type_culture.nom,
                'theme': conseil.get_theme_display(),
                'niveau': conseil.get_niveau_difficulte_display(),
                'date_creation': conseil.date_creation.strftime('%d/%m/%Y'),
            })
        
        return JsonResponse({
            'success': True,
            'conseils': conseils_data,
            'total': conseils.count()
        })
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

def conseil_detail(request, conseil_id):
    conseil = get_object_or_404(ConseilAgricole, id=conseil_id)
    
    # Conseils similaires (même culture ou même thème)
    conseils_similaires = ConseilAgricole.objects.filter(
        Q(type_culture=conseil.type_culture) | Q(theme=conseil.theme)
    ).exclude(id=conseil.id)[:3]
    
    context = {
        'conseil': conseil,
        'conseils_similaires': conseils_similaires,
    }
    
    return render(request, 'monapp/conseil_detail.html', context)

def auth_view(request):
    """Vue unifiée pour connexion et inscription"""
    login_form = AuthenticationForm()
    register_form = CustomUserCreationForm()
    agriculteur_form = AgriculteurForm()
    
    # Récupération du rôle par défaut depuis l'URL
    default_role = request.GET.get('role', 'agriculteur')
    
    login_errors = []
    register_errors = []
    
    if request.method == 'POST':
        action = request.POST.get('action')
        logger.debug("Action auth recue: %s", action)
        
        if action == 'login':
            return handle_login(request)
        elif action == 'register':
            return handle_register(request)
    
    context = {
        'login_form': login_form,
        'register_form': register_form,
        'agriculteur_form': agriculteur_form,
        'types_cultures': TypeCulture.objects.all(),
        'login_errors': login_errors,
        'register_errors': register_errors,
        'default_role': default_role,
    }
    
    return render(request, 'monapp/auth.html', context)

def handle_login(request):
    """Gestion de la connexion"""
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    remember_me = request.POST.get('remember_me')
    login_limiter = LoginAttemptLimiter()
    identifier = f"{username}:{get_client_ip(request)}"
    
    # Validation des données d'entrée
    if not username or not password:
        messages.error(request, 'Veuillez remplir tous les champs.')
        return redirect('monapp:auth')
    
    if login_limiter.is_locked(identifier):
        messages.error(request, 'Trop de tentatives de connexion. Réessayez dans quelques minutes.')
        return redirect('monapp:auth')
    
    user = authenticate_by_username_or_email(request, username, password)
    
    if user is not None:
        if user.is_active:
            login_limiter.record_successful_attempt(identifier)
            login(request, user)
            
            # Gestion du "se souvenir de moi"
            if not remember_me:
                request.session.set_expiry(0)  # Session expire à la fermeture du navigateur
            else:
                request.session.set_expiry(1209600)  # 2 semaines
            
            messages.success(request, f'Bienvenue {user.get_full_name() or user.username} !')
            
            # Redirection vers la page demandée ou le tableau de bord approprié
            next_page = request.GET.get('next')
            if not next_page:
                # Redirection selon le rôle de l'utilisateur
                next_page = get_user_dashboard_url(user)
            
            return redirect(next_page)
        else:
            messages.error(request, 'Votre compte est désactivé.')
    else:
        login_limiter.record_failed_attempt(identifier)
        messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    
    return render(request, 'monapp/auth.html', {
        'login_form': AuthenticationForm(),
        'register_form': CustomUserCreationForm(),
        'agriculteur_form': AgriculteurForm(),
        'types_cultures': TypeCulture.objects.all(),
        'login_errors': ['Nom d\'utilisateur ou mot de passe incorrect.'] if not user else [],
        'register_errors': [],
    })

def handle_register(request):
    """Gestion de l'inscription"""
    logger.debug("handle_register appele")
    
    user_form = CustomUserCreationForm(request.POST)
    
    logger.debug("handle_register validite formulaire: %s", user_form.is_valid())
    if not user_form.is_valid():
        logger.debug("Erreurs formulaire utilisateur: %s", user_form.errors)
    
    if user_form.is_valid():
        try:
            # Création de l'utilisateur dans une transaction
            from django.db import transaction
            
            with transaction.atomic():
                # Création de l'utilisateur
                user = user_form.save()
                
                # Récupération du rôle choisi
                role = user_form.cleaned_data.get('role', 'agriculteur')
                
                if role == 'agriculteur':
                    # Le profil a déjà été créé par le formulaire; on le complète
                    agriculteur = user.agriculteur
                    agriculteur.contact = request.POST.get('contact', '')
                    agriculteur.localisation = request.POST.get('localisation', '')
                    agriculteur.superficie = request.POST.get('superficie', '')
                    agriculteur.save()
                    
                    # Gestion de la photo
                    if 'photo' in request.FILES:
                        agriculteur.photo = request.FILES['photo']
                        agriculteur.save()
                    
                    # Gestion des cultures pratiquées
                    cultures_noms = request.POST.getlist('cultures_pratiquees')
                    if cultures_noms:
                        cultures = []
                        for nom in cultures_noms:
                            # Créer ou récupérer la culture
                            culture, created = TypeCulture.objects.get_or_create(
                                nom__iexact=nom,
                                defaults={'nom': nom.capitalize()}
                            )
                            cultures.append(culture)
                        agriculteur.cultures_pratiquees.set(cultures)
                
                elif role == 'expert':
                    # Le profil a déjà été créé par le formulaire; on le complète
                    expert = user.expert
                    expert.nom = user.last_name
                    expert.prenom = user.first_name
                    expert.email = user.email
                    expert.specialite = request.POST.get('specialite', '')
                    expert.experience = request.POST.get('experience', '')
                    expert.bio = request.POST.get('bio', '')
                    expert.est_verifie = False  # Les experts doivent être vérifiés par un admin
                    expert.save()
                
                # Connexion automatique après inscription
                username = user_form.cleaned_data.get('username')
                password = user_form.cleaned_data.get('password1')
                user = authenticate_by_username_or_email(request, username, password)
                if user:
                    login(request, user)
                    if role == 'agriculteur':
                        messages.success(request, 'Votre compte agriculteur a été créé avec succès ! Bienvenue sur AgriSmart.')
                        return redirect('monapp:compte')
                    else:
                        messages.success(request, 'Votre compte expert a été créé avec succès ! Votre profil est en attente de vérification.')
                        return redirect('monapp:expert_dashboard')
                else:
                    messages.error(request, 'Compte créé mais erreur de connexion. Veuillez vous connecter manuellement.')
                    return redirect('monapp:auth')
                    
        except Exception as e:
            messages.error(request, f'Erreur lors de la création du profil: {str(e)}')
            # L'utilisateur sera supprimé automatiquement par la transaction atomique
    
    # En cas d'erreur, réafficher le formulaire avec les erreurs
    errors = []
    for field, field_errors in user_form.errors.items():
        for error in field_errors:
            errors.append(f"{field}: {error}")
    
    return render(request, 'monapp/auth.html', {
        'login_form': AuthenticationForm(),
        'register_form': user_form,
        'types_cultures': TypeCulture.objects.all(),
        'login_errors': [],
        'register_errors': errors,
    })

def logout_view(request):
    """Déconnexion"""
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('monapp:index')

def expert_registration_view(request):
    """Vue spécialisée pour l'inscription des experts"""
    if request.method == 'POST':
        form = ExpertRegistrationForm(request.POST)
        
        if form.is_valid():
            try:
                from django.db import transaction
                
                with transaction.atomic():
                    # Vérifier si c'est une validation directe par un admin
                    validate_directly = request.POST.get('validate_directly') == 'true' and request.user.is_superuser
                    
                    # Création de l'utilisateur (toujours actif maintenant)
                    user = User.objects.create_user(
                        username=form.cleaned_data['email'],  # Utiliser l'email comme username
                        email=form.cleaned_data['email'],
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        password=form.cleaned_data['password1'],  # Utiliser le mot de passe fourni
                        is_active=True  # Toujours activer l'utilisateur maintenant
                    )
                    
                    # Création du profil expert (toujours vérifié maintenant)
                    expert = Expert.objects.create(
                        user=user,
                        nom=form.cleaned_data['last_name'],
                        prenom=form.cleaned_data['first_name'],
                        email=form.cleaned_data['email'],
                        specialite=form.cleaned_data['specialite'],
                        experience=form.cleaned_data['experience'],
                        bio=form.cleaned_data['bio'],
                        contact=form.cleaned_data.get('contact', ''),
                        localisation=form.cleaned_data['localisation'],
                        statut_professionnel=form.cleaned_data['statut_professionnel'],
                        formation=form.cleaned_data.get('formation', ''),
                        certifications=form.cleaned_data.get('certifications', ''),
                        disponibilite=form.cleaned_data.get('disponibilite', ''),
                        est_verifie=True,  # Toujours valider directement maintenant
                        date_verification=timezone.now()  # Date de validation automatique
                    )
                    
                    # Envoyer un email de bienvenue avec les instructions de connexion
                    from django.core.mail import send_mail
                    from django.template.loader import render_to_string
                    
                    temp_password = user.password  # Sauvegarder le mot de passe temporaire
                    
                    try:
                        # Email de bienvenue (optionnel, si email configuré)
                        subject = 'Bienvenue sur AgriSmart - Inscription Expert'
                        message = f"""
                        Bonjour {user.get_full_name()},
                        
                        Votre demande d'inscription en tant qu'expert sur AgriSmart a été reçue.
                        
                        Votre profil est actuellement en cours de vérification par notre équipe.
                        Vous recevrez un email de confirmation une fois votre profil validé.
                        
                        Informations de votre compte :
                        - Email : {user.email}
                        - Spécialité : {expert.get_specialite_display()}
                        - Localisation : {expert.localisation}
                        
                        Merci de rejoindre notre communauté d'experts !
                        
                        L'équipe AgriSmart
                        """
                        
                        # send_mail(subject, message, 'noreply@agrismart.com', [user.email])
                    except Exception as e:
                        # Si l'email échoue, ce n'est pas critique
                        logger.warning("Erreur envoi email: %s", e)
                    
                    # Connexion automatique de l'expert
                    authenticated_user = authenticate_by_username_or_email(
                        request,
                        form.cleaned_data['email'],
                        form.cleaned_data['password1']
                    )
                    
                    if authenticated_user:
                        login(request, authenticated_user)
                        messages.success(
                            request,
                            f'Bienvenue {expert.nom_complet} ! Votre profil d\'expert a été créé avec succès. '
                            f'Vous êtes maintenant connecté et pouvez commencer à conseiller les agriculteurs.'
                        )
                        # Redirection directe vers le tableau de bord expert
                        return redirect('monapp:expert_dashboard')
                    else:
                        messages.success(
                            request,
                            f'Votre profil d\'expert a été créé avec succès ! '
                            f'Vous pouvez maintenant vous connecter avec vos identifiants.'
                        )
                        return redirect('monapp:expert_login')
                    
            except Exception as e:
                messages.error(request, f'Erreur lors de l\'inscription : {str(e)}')
                return render(request, 'monapp/expert_registration.html', {'form': form})
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = ExpertRegistrationForm()
    
    return render(request, 'monapp/expert_registration.html', {'form': form})

# Vue de connexion dédiée aux experts
def expert_login_view(request):
    """Vue de connexion spécialement conçue pour les experts"""
    if request.user.is_authenticated:
        # Si l'utilisateur est déjà connecté, rediriger selon son rôle
        try:
            expert = Expert.objects.get(user=request.user)
            return redirect('monapp:expert_dashboard')
        except Expert.DoesNotExist:
            # Si ce n'est pas un expert, déconnecter et redemander la connexion
            logout(request)
            messages.warning(request, 'Accès réservé aux experts uniquement.')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember')
        
        if username and password:
            # Authentification
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Vérifier que l'utilisateur est bien un expert
                try:
                    expert = Expert.objects.get(user=user)
                    
                    # Connexion réussie (accès immédiat sans validation)
                    login(request, user)
                    
                    # Gestion du "Se souvenir de moi"
                    if not remember_me:
                        request.session.set_expiry(0)  # Session expire à la fermeture du navigateur
                    
                    messages.success(request, f'Bienvenue Dr. {expert.user.get_full_name() or expert.user.username} !')
                    
                    # Redirection vers le dashboard expert
                    next_url = request.GET.get('next', 'monapp:expert_dashboard')
                    return redirect(next_url)
                    
                except Expert.DoesNotExist:
                    context = {
                        'error_message': 'Ce compte n\'est pas enregistré comme expert. Veuillez vous inscrire en tant qu\'expert ou utiliser la connexion agriculteur.',
                        'form': {'username': {'value': username}}
                    }
                    return render(request, 'monapp/expert_login.html', context)
            else:
                context = {
                    'error_message': 'Email/nom d\'utilisateur ou mot de passe incorrect.',
                    'form': {'username': {'value': username}}
                }
                return render(request, 'monapp/expert_login.html', context)
        else:
            context = {
                'error_message': 'Veuillez saisir votre email et votre mot de passe.',
                'form': {'username': {'value': username}}
            }
            return render(request, 'monapp/expert_login.html', context)
    
    # GET request - afficher le formulaire
    return render(request, 'monapp/expert_login.html')

# Vues séparées pour compatibilité URL
def login_view(request):
    return auth_view(request)

def register_view(request):
    return auth_view(request)


# Vues manquantes
def meteo_view(request):
    """Vue pour la page météo avec intégration API OpenWeatherMap"""
    from .weather_service import WeatherService
    
    # Récupération de la ville depuis les paramètres GET (optionnel)
    city = request.GET.get('city', None)
    country = request.GET.get('country', None)
    
    # Initialisation du service météo
    weather_service = WeatherService()
    
    # Récupération des données météo via l'API
    meteo_actuelle = weather_service.get_current_weather(city, country)
    previsions_5_jours = weather_service.get_forecast(city, country, days=5)
    
    # Génération des conseils agricoles basés sur la météo
    conseil_meteo = weather_service.get_agricultural_advice(meteo_actuelle, previsions_5_jours)
    
    # Indicateurs pour l'agriculture
    impact_agriculture = []
    if meteo_actuelle:
        temp = meteo_actuelle['temperature']
        humidite = meteo_actuelle['humidite']
        vent = meteo_actuelle['vent']
        
        # Évaluation des conditions pour l'irrigation
        if humidite < 60 or temp > 30:
            impact_agriculture.append({
                'icon': 'fas fa-water text-blue-500',
                'text': 'Conditions favorables pour l\'irrigation',
                'status': 'good'
            })
        else:
            impact_agriculture.append({
                'icon': 'fas fa-water text-gray-500',
                'text': 'Irrigation modérée recommandée',
                'status': 'neutral'
            })
        
        # Évaluation pour la croissance des cultures
        if 20 <= temp <= 35 and 50 <= humidite <= 80:
            impact_agriculture.append({
                'icon': 'fas fa-leaf text-green-500',
                'text': 'Croissance optimale des cultures',
                'status': 'good'
            })
        else:
            impact_agriculture.append({
                'icon': 'fas fa-leaf text-yellow-500',
                'text': 'Conditions de croissance modérées',
                'status': 'neutral'
            })
        
        # Évaluation du risque de parasites
        if humidite > 70 and temp > 25:
            impact_agriculture.append({
                'icon': 'fas fa-bug text-red-500',
                'text': 'Risque élevé de parasites',
                'status': 'warning'
            })
        elif humidite > 60:
            impact_agriculture.append({
                'icon': 'fas fa-bug text-orange-500',
                'text': 'Risque modéré de parasites',
                'status': 'neutral'
            })
        else:
            impact_agriculture.append({
                'icon': 'fas fa-bug text-green-500',
                'text': 'Risque faible de parasites',
                'status': 'good'
            })
    
    # Tendances saisonnières calculées
    tendances = {}
    if previsions_5_jours:
        temperatures = [p['temp_max'] for p in previsions_5_jours] + [p['temp_min'] for p in previsions_5_jours]
        humidites = [p.get('humidite_moyenne', 65) for p in previsions_5_jours]
        precipitations = sum(p['probabilite_pluie'] for p in previsions_5_jours) / len(previsions_5_jours)
        
        tendances = {
            'temperature_moyenne': round(sum(temperatures) / len(temperatures)),
            'humidite_moyenne': round(sum(humidites) / len(humidites)),
            'pluviometrie_prevue': round(precipitations)
        }
    else:
        tendances = {
            'temperature_moyenne': 29,
            'humidite_moyenne': 68,
            'pluviometrie_prevue': 30
        }
    
    context = {
        'meteo_actuelle': meteo_actuelle,
        'previsions_5_jours': previsions_5_jours,
        'conseil_meteo': conseil_meteo,
        'impact_agriculture': impact_agriculture,
        'tendances': tendances,
        'city_requested': city,
        'api_active': meteo_actuelle is not None and 'derniere_maj' in meteo_actuelle and meteo_actuelle['derniere_maj'] != 'Données de secours'
    }
    
    return render(request, 'monapp/meteo.html', context)

@login_required
def add_activite(request):
    """Vue pour ajouter une activité"""
    if request.method == 'POST':
        try:
            agriculteur = request.user.agriculteur
            type_culture = TypeCulture.objects.get(id=request.POST['type_culture'])
            
            activite = ActiviteAgricole.objects.create(
                agriculteur=agriculteur,
                type_culture=type_culture,
                type_activite=request.POST['type_activite'],
                date_prevue=request.POST['date_prevue'],
                description=request.POST.get('description', '')
            )
            
            return JsonResponse({'success': True, 'id': activite.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False})


@login_required
def edit_activite(request):
    """Vue pour modifier une activité"""
    if request.method == 'POST':
        try:
            activity_id = request.POST['activity_id']
            activite = ActiviteAgricole.objects.get(
                id=activity_id,
                agriculteur=request.user.agriculteur
            )
            
            activite.type_activite = request.POST['type_activite']
            activite.date_prevue = request.POST['date_prevue']
            activite.description = request.POST.get('description', '')
            activite.type_culture = TypeCulture.objects.get(id=request.POST['type_culture'])
            activite.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False})


@login_required
def delete_activite(request):
    """Vue pour supprimer une activité"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            activity_id = data['activity_id']
            
            ActiviteAgricole.objects.filter(
                id=activity_id,
                agriculteur=request.user.agriculteur
            ).delete()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Méthode non autorisée.'})


@login_required
def add_user_culture(request):
    """Vue pour ajouter une culture au profil de l'utilisateur"""
    if request.method == 'POST':
        try:
            # Récupérer ou créer le profil agriculteur
            agriculteur, created = Agriculteur.objects.get_or_create(
                user=request.user,
                defaults={
                    'contact': '',
                    'localisation': '',
                    'superficie': ''
                }
            )
            
            if created:
                messages.info(request, 'Votre profil agriculteur a été créé automatiquement.')
            
            culture_id = request.POST.get('culture_id')
            
            if culture_id:
                culture = get_object_or_404(TypeCulture, id=culture_id)
                
                # Vérifier si la culture n'est pas déjà dans le profil
                if agriculteur.cultures_pratiquees.filter(id=culture_id).exists():
                    messages.warning(request, f'La culture "{culture.nom}" est déjà dans votre profil.')
                else:
                    agriculteur.cultures_pratiquees.add(culture)
                    messages.success(request, f'La culture "{culture.nom}" a été ajoutée à votre profil.')
            else:
                messages.error(request, 'Veuillez sélectionner une culture.')
                
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'ajout de la culture : {str(e)}')
    
    return redirect('monapp:compte')


@login_required
def remove_user_culture(request):
    """Vue pour supprimer une culture du profil de l'utilisateur"""
    if request.method == 'POST':
        try:
            # Récupérer ou créer le profil agriculteur
            agriculteur, created = Agriculteur.objects.get_or_create(
                user=request.user,
                defaults={
                    'contact': '',
                    'localisation': '',
                    'superficie': ''
                }
            )
            
            if created:
                messages.info(request, 'Votre profil agriculteur a été créé automatiquement.')
                # Si le profil vient d'être créé, il n'y a pas de culture à supprimer
                messages.warning(request, 'Aucune culture à supprimer dans un profil vide.')
                return redirect('monapp:compte')
            
            culture_id = request.POST.get('culture_id')
            
            if culture_id:
                culture = get_object_or_404(TypeCulture, id=culture_id)
                
                # Vérifier si la culture est dans le profil
                if agriculteur.cultures_pratiquees.filter(id=culture_id).exists():
                    agriculteur.cultures_pratiquees.remove(culture)
                    messages.success(request, f'La culture "{culture.nom}" a été retirée de votre profil.')
                else:
                    messages.warning(request, f'La culture "{culture.nom}" n\'était pas dans votre profil.')
            else:
                messages.error(request, 'Culture non spécifiée.')
                
        except Exception as e:
            messages.error(request, f'Erreur lors de la suppression de la culture : {str(e)}')
    
    return redirect('monapp:compte')


@login_required
def update_profile(request):
    """Vue pour mettre à jour le profil de l'utilisateur"""
    if request.method == 'POST':
        try:
            user = request.user
            
            # Récupérer ou créer le profil agriculteur
            agriculteur, created = Agriculteur.objects.get_or_create(
                user=user,
                defaults={
                    'contact': '',
                    'localisation': '',
                    'superficie': ''
                }
            )
            
            if created:
                messages.info(request, 'Votre profil agriculteur a été créé automatiquement.')
            
            # Mise à jour des informations utilisateur
            email = request.POST.get('email', '').strip()
            if email:
                user.email = email
                user.save()
            
            # Mise à jour des informations agriculteur
            contact = request.POST.get('contact', '').strip()
            localisation = request.POST.get('localisation', '').strip()
            superficie = request.POST.get('superficie', '').strip()
            
            agriculteur.contact = contact
            agriculteur.localisation = localisation
            agriculteur.superficie = superficie
            
            # Gestion de la photo
            if 'photo' in request.FILES:
                agriculteur.photo = request.FILES['photo']

            # Mise à jour du mot de passe si demandé
            current_password = request.POST.get('current_password', '').strip()
            new_password1 = request.POST.get('new_password1', '')
            new_password2 = request.POST.get('new_password2', '')

            password_fields_filled = any([current_password, new_password1, new_password2])
            if password_fields_filled:
                if not current_password or not new_password1 or not new_password2:
                    messages.error(request, 'Veuillez remplir l’ancien mot de passe et les deux champs du nouveau mot de passe.')
                    return redirect('monapp:compte')

                if not user.check_password(current_password):
                    messages.error(request, 'L’ancien mot de passe est incorrect.')
                    return redirect('monapp:compte')

                if new_password1 != new_password2:
                    messages.error(request, 'Les deux nouveaux mots de passe ne correspondent pas.')
                    return redirect('monapp:compte')

                user.set_password(new_password1)
                user.save()
                update_session_auth_hash(request, user)
            
            agriculteur.save()
            
            messages.success(request, 'Votre profil a été mis à jour avec succès.')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la mise à jour du profil : {str(e)}')
    
    return redirect('monapp:compte')


@login_required
def upload_photo(request):
    """Vue pour l'upload de photo de profil via AJAX"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            agriculteur = request.user.agriculteur
            photo = request.FILES.get('photo')
            
            if not photo:
                return JsonResponse({'success': False, 'error': 'Aucun fichier sélectionné.'})
            
            # Validation du type de fichier
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
            if photo.content_type not in allowed_types:
                return JsonResponse({'success': False, 'error': 'Type de fichier non autorisé. Utilisez JPEG, PNG ou GIF.'})
            
            # Validation de la taille (5MB max)
            if photo.size > 5 * 1024 * 1024:
                return JsonResponse({'success': False, 'error': 'Le fichier ne doit pas dépasser 5MB.'})
            
            # Supprimer l'ancienne photo si elle existe
            if agriculteur.photo:
                try:
                    agriculteur.photo.delete(save=False)
                except Exception:
                    pass  # Ignorer les erreurs de suppression
            
            # Sauvegarder la nouvelle photo
            agriculteur.photo = photo
            agriculteur.save()
            
            return JsonResponse({
                'success': True, 
                'photo_url': agriculteur.photo.url,
                'message': 'Photo de profil mise à jour avec succès.'
            })
            
        except Agriculteur.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Profil agriculteur non trouvé.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Erreur lors de l\'upload : {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Requête non autorisée.'})


# Vues pour la gestion des experts
def experts_view(request):
    """Page principale des experts avec liste des experts et formulaire de demande"""
    experts_disponibles = Expert.objects.filter(disponible=True).select_related('user')
    
    # Statistiques sur les experts
    stats = {
        'total_experts': Expert.objects.filter(disponible=True).count(),
        'domaines': Expert.objects.filter(disponible=True).values('domaines_expertise').annotate(count=Count('id')),
        'demandes_en_attente': DemandeExpert.objects.filter(statut='en_attente').count() if request.user.is_authenticated else 0,
    }
    
    form = None
    user_demandes = []
    
    if request.user.is_authenticated:
        try:
            agriculteur = request.user.agriculteur
            if request.method == 'POST':
                form = DemandeExpertForm(request.POST)
                if form.is_valid():
                    demande = form.save(commit=False)
                    demande.agriculteur = agriculteur
                    demande.save()
                    messages.success(request, 'Votre demande a été envoyée avec succès. Un expert vous contactera bientôt.')
                    return redirect('monapp:experts')
            else:
                form = DemandeExpertForm()
            
            # Récupérer les demandes de l'utilisateur
            user_demandes = DemandeExpert.objects.filter(agriculteur=agriculteur).order_by('-date_creation')[:5]
            
        except Agriculteur.DoesNotExist:
            # Créer le profil agriculteur si nécessaire
            Agriculteur.objects.create(user=request.user)
            form = DemandeExpertForm()
    
    context = {
        'experts': experts_disponibles,
        'form': form,
        'stats': stats,
        'user_demandes': user_demandes,
    }
    
    return render(request, 'monapp/experts.html', context)


@login_required
def mes_demandes_experts_view(request):
    """Page pour voir toutes les demandes de l'utilisateur"""
    try:
        agriculteur = request.user.agriculteur
        demandes = DemandeExpert.objects.filter(agriculteur=agriculteur).order_by('-date_creation')
        
        # Statistiques
        stats = {
            'total': demandes.count(),
            'en_attente': demandes.filter(statut='en_attente').count(),
            'en_cours': demandes.filter(statut__in=['acceptee', 'en_cours']).count(),
            'terminees': demandes.filter(statut='terminee').count(),
        }
        
        # Pagination
        paginator = Paginator(demandes, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'demandes': page_obj,
            'stats': stats,
            'title': 'Mes demandes d\'experts',
        }
        
        return render(request, 'monapp/mes_demandes_experts.html', context)
        
    except Agriculteur.DoesNotExist:
        messages.error(request, 'Veuillez compléter votre profil agriculteur pour accéder à cette page.')
        return redirect('monapp:compte')


@login_required
def annuler_demande_expert(request, demande_id):
    """Annuler une demande d'expert"""
    if request.method == 'POST':
        try:
            agriculteur = request.user.agriculteur
            demande = get_object_or_404(DemandeExpert, id=demande_id, agriculteur=agriculteur)
            
            if demande.statut == 'en_attente':
                demande.statut = 'refusee'
                demande.save()
                return JsonResponse({'success': True, 'message': 'Demande annulée avec succès.'})
            else:
                return JsonResponse({'success': False, 'error': 'Cette demande ne peut pas être annulée.'})
                
        except (Agriculteur.DoesNotExist, DemandeExpert.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'Demande non trouvée.'})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée.'})


def expert_detail_view(request, expert_id):
    """Détail d'un expert spécifique"""
    expert = get_object_or_404(Expert, id=expert_id, disponible=True)
    
    # Statistiques de l'expert
    demandes_traitees = DemandeExpert.objects.filter(
        expert=expert, 
        statut__in=['terminee', 'en_cours']
    ).count()
    
    context = {
        'expert': expert,
        'demandes_traitees': demandes_traitees,
    }
    
    return render(request, 'monapp/expert_detail.html', context)


# Interface pour les experts
@login_required
def expert_dashboard_view(request):
    """Tableau de bord pour les experts"""
    try:
        expert = request.user.expert
    except Expert.DoesNotExist:
        messages.error(request, 'Accès réservé aux experts uniquement.')
        return redirect('monapp:index')
    
    # Filtrer par statut si spécifié
    status_filter = request.GET.get('status')
    
    # Récupérer toutes les demandes assignées à cet expert
    demandes_base = DemandeExpert.objects.filter(
        expert=expert
    ).order_by('-date_creation')
    
    # Appliquer le filtre de statut
    if status_filter:
        if status_filter == 'en_attente':
            demandes = demandes_base.filter(statut='en_attente')
        elif status_filter == 'acceptee':
            demandes = demandes_base.filter(statut='acceptee')
        elif status_filter == 'en_cours':
            demandes = demandes_base.filter(statut='en_cours')
        elif status_filter == 'terminee':
            demandes = demandes_base.filter(statut='terminee')
        else:
            demandes = demandes_base
    else:
        demandes = demandes_base
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(demandes, 10)  # 10 demandes par page
    page_number = request.GET.get('page')
    demandes = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'nouvelles': DemandeExpert.objects.filter(expert=expert, statut='en_attente').count(),
        'en_cours': DemandeExpert.objects.filter(expert=expert, statut__in=['acceptee', 'en_cours']).count(),
        'terminees': DemandeExpert.objects.filter(expert=expert, statut='terminee').count(),
        'note_moyenne': expert.note_moyenne if expert.note_moyenne > 0 else 0.0,
    }
    
    context = {
        'expert': expert,
        'demandes': demandes,
        'stats': stats,
    }
    
    return render(request, 'monapp/expert_dashboard.html', context)


@login_required
def expert_nouvelles_demandes(request):
    """Voir les nouvelles demandes disponibles (sans expert assigné) et les demandes assignées directement"""
    try:
        expert = request.user.expert
    except Expert.DoesNotExist:
        messages.error(request, 'Accès réservé aux experts uniquement.')
        return redirect('monapp:index')
    
    # Récupérer les demandes sans expert assigné dans le domaine de l'expert
    # ET les demandes assignées directement à cet expert qui sont encore en attente
    nouvelles_demandes = DemandeExpert.objects.filter(
        Q(expert__isnull=True, domaine_demande=expert.domaines_expertise) |
        Q(expert=expert, statut='en_attente'),
        statut='en_attente'
    ).order_by('-date_creation')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(nouvelles_demandes, 10)
    page_number = request.GET.get('page')
    nouvelles_demandes = paginator.get_page(page_number)
    
    context = {
        'expert': expert,
        'nouvelles_demandes': nouvelles_demandes,
    }
    
    return render(request, 'monapp/expert_nouvelles_demandes.html', context)


@login_required
def expert_demande_detail(request, demande_id):
    """Détail d'une demande pour un expert"""
    try:
        expert = request.user.expert
    except Expert.DoesNotExist:
        messages.error(request, 'Accès réservé aux experts uniquement.')
        return redirect('monapp:index')
    
    # Récupérer la demande assignée à cet expert avec son fil de discussion
    demande = get_object_or_404(
        DemandeExpert.objects.select_related('agriculteur__user', 'expert__user').prefetch_related('messages_discussion__auteur'),
        id=demande_id,
        expert=expert,
    )
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'repondre':
            reponse = request.POST.get('reponse', '').strip()
            if reponse:
                demande.reponse = reponse
                demande.date_reponse = timezone.now()
                # Changer le statut à "en_cours" quand l'expert répond
                if demande.statut == 'acceptee':
                    demande.statut = 'en_cours'
                demande.save()
                messages.success(request, 'Réponse envoyée avec succès.')
                
        elif action == 'terminer':
            demande.statut = 'terminee'
            demande.date_traitement = timezone.now()
            demande.save()
            messages.success(request, 'Consultation marquée comme terminée.')
            return redirect('monapp:expert_dashboard')
            
        elif action == 'en_cours':
            demande.statut = 'en_cours'
            demande.save()
            messages.success(request, 'Demande marquée en cours de traitement.')
    
    context = {
        'demande': demande,
        'expert': expert,
        'discussion_messages': demande.messages_discussion.all(),
    }
    
    return render(request, 'monapp/expert_demande_detail.html', context)


@login_required
def expert_accepter_demande(request, demande_id):
    """Accepter une nouvelle demande (AJAX)"""
    if request.method == 'POST':
        try:
            expert = request.user.expert
            
            # Récupérer la demande (peut être avec ou sans expert assigné)
            demande = get_object_or_404(DemandeExpert, id=demande_id, statut='en_attente')
            
            # Cas 1: Demande sans expert assigné (demande générale)
            if demande.expert is None:
                # Assigner l'expert et changer le statut
                demande.expert = expert
                demande.statut = 'acceptee'
                demande.save()
                
                return JsonResponse({
                    'success': True, 
                    'message': 'Demande acceptée avec succès.'
                })
            
            # Cas 2: Demande déjà assignée à cet expert (contact direct)
            elif demande.expert == expert:
                # Simplement changer le statut à acceptée
                demande.statut = 'acceptee'
                demande.save()
                
                return JsonResponse({
                    'success': True, 
                    'message': 'Demande acceptée avec succès.'
                })
            
            # Cas 3: Demande assignée à un autre expert
            else:
                return JsonResponse({
                    'success': False, 
                    'error': 'Cette demande est déjà assignée à un autre expert.'
                })
            
        except Expert.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'error': 'Accès réservé aux experts.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Erreur lors de l\'acceptation : {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée.'})

@user_passes_test(lambda u: u.is_superuser)
def admin_validate_experts(request):
    """Vue d'administration pour valider les experts en attente"""
    # Experts en attente de validation
    experts_en_attente = Expert.objects.filter(est_verifie=False).order_by('-date_inscription')
    
    # Experts déjà validés (pour affichage)
    experts_valides = Expert.objects.filter(est_verifie=True).order_by('-date_verification')[:10]
    
    # Statistiques
    total_experts = Expert.objects.count()
    experts_valides_count = Expert.objects.filter(est_verifie=True).count()
    experts_attente_count = experts_en_attente.count()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        expert_id = request.POST.get('expert_id')
        
        try:
            expert = Expert.objects.get(id=expert_id)
            
            if action == 'valider':
                from django.utils import timezone
                expert.est_verifie = True
                expert.date_verification = timezone.now()
                expert.save()
                
                # Activer le compte utilisateur si nécessaire
                expert.user.is_active = True
                expert.user.save()
                
                messages.success(request, f'Expert {expert.nom_complet} validé avec succès !')
                
                # Optionnel : Envoyer un email de confirmation
                try:
                    from django.core.mail import send_mail
                    subject = 'Validation de votre profil expert - AgriSmart'
                    message = f"""
Bonjour {expert.nom_complet},

Excellente nouvelle ! Votre profil d'expert sur AgriSmart a été validé par notre équipe.

Vous pouvez maintenant :
- Vous connecter à votre espace expert
- Répondre aux demandes de consultation des agriculteurs
- Accéder à votre tableau de bord professionnel

Informations de connexion :
- Email : {expert.email}
- Page de connexion : http://127.0.0.1:8000/expert-login/

Bienvenue dans l'équipe des experts AgriSmart !

L'équipe AgriSmart
                    """
                    
                    # send_mail(subject, message, 'noreply@agrismart.com', [expert.email])
                except Exception as e:
                    logger.warning("Erreur envoi email: %s", e)
                    
            elif action == 'rejeter':
                expert.est_verifie = False
                expert.date_verification = None
                expert.save()
                
                # Optionnel : Désactiver le compte
                expert.user.is_active = False
                expert.user.save()
                
                messages.warning(request, f'Expert {expert.nom_complet} rejeté.')
                
        except Expert.DoesNotExist:
            messages.error(request, 'Expert introuvable.')
        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')
        
        return redirect('monapp:admin_validate_experts')
    
    context = {
        'experts_en_attente': experts_en_attente,
        'experts_valides': experts_valides,
        'total_experts': total_experts,
        'experts_valides_count': experts_valides_count,
        'experts_attente_count': experts_attente_count,
    }
    
    return render(request, 'monapp/admin_validate_experts.html', context)


@login_required
def contacter_expert_view(request, expert_id):
    """Vue pour contacter directement un expert spécifique"""
    expert = get_object_or_404(Expert, id=expert_id, disponible=True)
    
    # Vérifier que l'utilisateur est un agriculteur
    try:
        agriculteur = request.user.agriculteur
    except Agriculteur.DoesNotExist:
        # Créer le profil agriculteur si nécessaire
        agriculteur = Agriculteur.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = DemandeExpertForm(request.POST)
        if form.is_valid():
            demande = form.save(commit=False)
            demande.agriculteur = agriculteur
            demande.expert = expert
            demande.save()
            
            messages.success(request, f'Votre demande a été envoyée à {expert.nom_complet}. L\'expert vous contactera bientôt.')
            return redirect('monapp:mes_demandes_experts')
    else:
        form = DemandeExpertForm()
    
    # Statistiques de l'expert
    demandes_traitees = DemandeExpert.objects.filter(
        expert=expert, 
        statut__in=['terminee']
    ).count()
    
    demandes_en_cours = DemandeExpert.objects.filter(
        expert=expert,
        statut__in=['en_attente', 'acceptee', 'en_cours']
    ).count()
    
    context = {
        'expert': expert,
        'form': form,
        'demandes_traitees': demandes_traitees,
        'demandes_en_cours': demandes_en_cours,
    }
    
    return render(request, 'monapp/contacter_expert.html', context)


@login_required
def demande_detail_agriculteur(request, demande_id):
    """Vue pour que l'agriculteur voie le détail de sa demande et la réponse de l'expert"""
    try:
        agriculteur = request.user.agriculteur
    except Agriculteur.DoesNotExist:
        messages.error(request, 'Accès réservé aux agriculteurs.')
        return redirect('monapp:index')
    
    # Récupérer la demande de cet agriculteur avec son fil de discussion
    demande = get_object_or_404(
        DemandeExpert.objects.select_related('agriculteur__user', 'expert__user').prefetch_related('messages_discussion__auteur'),
        id=demande_id,
        agriculteur=agriculteur,
    )
    
    # Gestion de l'évaluation de satisfaction
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'evaluer' and demande.statut == 'terminee':
            note = request.POST.get('note_satisfaction')
            commentaire = request.POST.get('commentaire_satisfaction', '').strip()
            
            if note and note.isdigit() and 1 <= int(note) <= 5:
                demande.note_satisfaction = int(note)
                demande.commentaire_satisfaction = commentaire
                demande.save()
                
                # Mettre à jour la note moyenne de l'expert
                if demande.expert:
                    expert = demande.expert
                    demandes_evaluees = DemandeExpert.objects.filter(
                        expert=expert,
                        note_satisfaction__isnull=False
                    )
                    if demandes_evaluees.exists():
                        total_notes = sum(d.note_satisfaction for d in demandes_evaluees)
                        expert.note_moyenne = total_notes / demandes_evaluees.count()
                        expert.save()
                
                messages.success(request, 'Merci pour votre évaluation !')
                return redirect('monapp:mes_demandes_experts')
            else:
                messages.error(request, 'Veuillez sélectionner une note de 1 à 5.')
    
    context = {
        'demande': demande,
        'peut_evaluer': demande.statut == 'terminee' and not demande.note_satisfaction,
        'discussion_messages': demande.messages_discussion.all(),
    }
    
    return render(request, 'monapp/demande_detail_agriculteur.html', context)


@login_required
def discussion_historique_json(request, demande_id):
    """Retourne l'historique des messages d'une demande pour le fallback AJAX/JSON."""
    try:
        user = request.user
        if hasattr(user, 'agriculteur'):
            demande = get_object_or_404(
                DemandeExpert.objects.select_related('agriculteur__user', 'expert__user').prefetch_related('messages_discussion__auteur'),
                id=demande_id,
                agriculteur=user.agriculteur,
            )
        elif hasattr(user, 'expert'):
            demande = get_object_or_404(
                DemandeExpert.objects.select_related('agriculteur__user', 'expert__user').prefetch_related('messages_discussion__auteur'),
                id=demande_id,
                expert=user.expert,
            )
        else:
            return JsonResponse({'success': False, 'error': 'Accès non autorisé.'}, status=403)

        messages_data = _serialize_discussion_messages(demande)

        return JsonResponse({
            'success': True,
            'demande_id': demande.id,
            'messages': messages_data,
        })
    except DemandeExpert.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Demande introuvable.'}, status=404)


def _serialize_discussion_messages(demande):
    return [
        {
            'id': message.id,
            'contenu': message.contenu,
            'date_envoi': message.date_envoi.isoformat(),
            'auteur_id': message.auteur_id,
            'auteur_nom': message.auteur.get_full_name() or message.auteur.username,
        }
        for message in demande.messages_discussion.all()
    ]
