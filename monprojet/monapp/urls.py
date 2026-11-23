from django.urls import path
from . import views

app_name = 'monapp'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('conseils/', views.conseils_view, name='conseils'),
    path('conseils/filtrer/', views.filtrer_conseils_ajax, name='filtrer_conseils_ajax'),
    path('conseils/<int:conseil_id>/', views.conseil_detail, name='conseil_detail'),
    path('calendrier/', views.calendrier_view, name='calendrier'),
    path('calendrier/add-activite/', views.add_activite, name='add_activite'),
    path('calendrier/edit-activite/', views.edit_activite, name='edit_activite'),
    path('calendrier/delete-activite/', views.delete_activite, name='delete_activite'),
    path('meteo/', views.meteo_view, name='meteo'),
    path('compte/', views.compte_view, name='compte'),
    path('compte/add-culture/', views.add_user_culture, name='add_user_culture'),
    path('compte/remove-culture/', views.remove_user_culture, name='remove_user_culture'),
    path('compte/update-profile/', views.update_profile, name='update_profile'),
    path('compte/upload-photo/', views.upload_photo, name='upload_photo'),
    # Experts
    path('experts/', views.experts_view, name='experts'),
    path('experts/<int:expert_id>/', views.expert_detail_view, name='expert_detail'),
    path('experts/<int:expert_id>/contacter/', views.contacter_expert_view, name='contacter_expert'),
    path('mes-demandes-experts/', views.mes_demandes_experts_view, name='mes_demandes_experts'),
    path('demande-detail/<int:demande_id>/', views.demande_detail_agriculteur, name='demande_detail_agriculteur'),
    path('demande-detail/<int:demande_id>/discussion-historique/', views.discussion_historique_json, name='discussion_historique_json'),
    path('annuler-demande/<int:demande_id>/', views.annuler_demande_expert, name='annuler_demande_expert'),
    # Interface expert
    path('expert-dashboard/', views.expert_dashboard_view, name='expert_dashboard'),
    path('expert-nouvelles-demandes/', views.expert_nouvelles_demandes, name='expert_nouvelles_demandes'),
    path('expert-demande/<int:demande_id>/', views.expert_demande_detail, name='expert_demande_detail'),
    path('expert-accepter/<int:demande_id>/', views.expert_accepter_demande, name='expert_accepter_demande'),
    # Authentification
    path('auth/', views.auth_view, name='auth'),
    path('login/', views.login_view, name='login'),
    path('expert-login/', views.expert_login_view, name='expert_login'),
    path('register/', views.register_view, name='register'),
    path('expert-registration/', views.expert_registration_view, name='expert_registration'),
    path('logout/', views.logout_view, name='logout'),
    # Administration
    path('admin/validate-experts/', views.admin_validate_experts, name='admin_validate_experts'),
]