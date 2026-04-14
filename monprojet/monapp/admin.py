from django.contrib import admin
from .models import TypeCulture, Agriculteur, ConseilAgricole, ActiviteAgricole, Expert, DemandeExpert

# Register your models here.

@admin.register(TypeCulture)
class TypeCultureAdmin(admin.ModelAdmin):
    list_display = ['nom', 'statut_saison', 'periode_semis_debut', 'periode_semis_fin']
    list_filter = ['statut_saison']
    search_fields = ['nom']


@admin.register(Agriculteur)
class AgriculteurAdmin(admin.ModelAdmin):
    list_display = ['user', 'contact', 'localisation', 'superficie']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'localisation']
    filter_horizontal = ['cultures_pratiquees']


@admin.register(ConseilAgricole)
class ConseilAgricoleAdmin(admin.ModelAdmin):
    list_display = ['titre', 'theme', 'type_culture', 'niveau_difficulte', 'date_creation']
    list_filter = ['theme', 'niveau_difficulte', 'type_culture', 'date_creation']
    search_fields = ['titre', 'contenu', 'auteur']
    date_hierarchy = 'date_creation'


@admin.register(ActiviteAgricole)
class ActiviteAgricoleAdmin(admin.ModelAdmin):
    list_display = ['agriculteur', 'type_culture', 'type_activite', 'date_prevue', 'terminee']
    list_filter = ['type_activite', 'terminee', 'date_prevue']
    search_fields = ['agriculteur__user__username', 'type_culture__nom', 'description']
    date_hierarchy = 'date_prevue'


@admin.register(Expert)
class ExpertAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialite', 'est_verifie', 'disponible', 'date_inscription', 'contact']
    list_filter = ['specialite', 'est_verifie', 'disponible', 'experience', 'statut_professionnel']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'formation', 'email']
    readonly_fields = ['user', 'date_inscription', 'nombre_consultations']
    actions = ['valider_experts', 'rejeter_experts']
    
    fieldsets = (
        ('Informations utilisateur', {
            'fields': ('user', 'date_inscription')
        }),
        ('Informations professionnelles', {
            'fields': ('specialite', 'experience', 'statut_professionnel', 'formation', 'certifications')
        }),
        ('Contact et localisation', {
            'fields': ('email', 'contact', 'localisation')
        }),
        ('Profil et disponibilité', {
            'fields': ('bio', 'disponibilite', 'disponible', 'photo')
        }),
        ('Statut et validation', {
            'fields': ('est_verifie', 'date_verification', 'note_moyenne', 'nombre_consultations'),
            'classes': ('collapse',)
        }),
    )
    
    def valider_experts(self, request, queryset):
        """Action pour valider plusieurs experts à la fois"""
        from django.utils import timezone
        count = queryset.filter(est_verifie=False).update(
            est_verifie=True,
            date_verification=timezone.now()
        )
        self.message_user(request, f'{count} expert(s) validé(s) avec succès.')
    valider_experts.short_description = "Valider les experts sélectionnés"
    
    def rejeter_experts(self, request, queryset):
        """Action pour rejeter la validation d'experts"""
        count = queryset.filter(est_verifie=True).update(
            est_verifie=False,
            date_verification=None
        )
        self.message_user(request, f'{count} expert(s) rejeté(s).')
    rejeter_experts.short_description = "Rejeter la validation des experts sélectionnés"


@admin.register(DemandeExpert)
class DemandeExpertAdmin(admin.ModelAdmin):
    list_display = ['agriculteur', 'sujet', 'domaine_demande', 'statut', 'urgence', 'expert', 'date_creation', 'note_satisfaction', 'commentaire_satisfaction_short']
    list_filter = ['statut', 'urgence', 'domaine_demande', 'date_creation', 'note_satisfaction']
    search_fields = ['agriculteur__user__username', 'sujet', 'description', 'commentaire_satisfaction']
    date_hierarchy = 'date_creation'
    readonly_fields = ['date_creation']
    actions = ['marquer_terminee', 'refuser_demande']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('agriculteur', 'domaine_demande', 'sujet', 'description', 'urgence')
        }),
        ('Traitement', {
            'fields': ('expert', 'statut', 'reponse', 'date_traitement', 'note_satisfaction', 'commentaire_satisfaction')
        }),
        ('Métadonnées', {
            'fields': ('date_creation',)
        }),
    )

    def commentaire_satisfaction_short(self, obj):
        if obj.commentaire_satisfaction:
            return (obj.commentaire_satisfaction[:40] + '...') if len(obj.commentaire_satisfaction) > 40 else obj.commentaire_satisfaction
        return ''
    commentaire_satisfaction_short.short_description = 'Commentaire'

    def marquer_terminee(self, request, queryset):
        count = queryset.exclude(statut='terminee').update(statut='terminee')
        self.message_user(request, f"{count} demande(s) marquée(s) comme terminée(s).")
    marquer_terminee.short_description = "Marquer comme terminée"

    def refuser_demande(self, request, queryset):
        count = queryset.exclude(statut='refusee').update(statut='refusee')
        self.message_user(request, f"{count} demande(s) refusée(s).")
    refuser_demande.short_description = "Refuser la demande"
