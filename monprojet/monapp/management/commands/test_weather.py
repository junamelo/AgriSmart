# -*- coding: utf-8 -*-
"""
Commande de gestion pour tester l'API météo
Usage: python manage.py test_weather [ville]
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from monapp.weather_service import WeatherService

class Command(BaseCommand):
    help = 'Test l\'intégration de l\'API météo OpenWeatherMap'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--city',
            type=str,
            default=None,
            help='Ville pour laquelle récupérer la météo (défaut: Abidjan)'
        )
        parser.add_argument(
            '--country',
            type=str,
            default=None,
            help='Code pays ISO (défaut: CI)'
        )
        parser.add_argument(
            '--forecast',
            action='store_true',
            help='Afficher aussi les prévisions sur 5 jours'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🌦️  Test de l\'API météo AgriSmart')
        )
        self.stdout.write('=' * 50)
        
        # Vérification de la clé API
        api_key = settings.OPENWEATHER_API_KEY
        if api_key == 'your-api-key-here':
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  Clé API non configurée. Utilisation des données de secours.'
                )
            )
            self.stdout.write(
                'Pour configuer votre clé API :'
            )
            self.stdout.write(
                '1. Créez un compte sur https://openweathermap.org/api'
            )
            self.stdout.write(
                '2. Obtenez votre clé API gratuite'
            )
            self.stdout.write(
                '3. Ajoutez OPENWEATHER_API_KEY=votre-cle dans le fichier .env'
            )
            self.stdout.write('')
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Clé API configurée: {api_key[:8]}...')
            )
        
        # Initialisation du service météo
        weather_service = WeatherService()
        city = options['city']
        country = options['country']
        
        self.stdout.write(f'🏙️  Ville: {city or settings.DEFAULT_CITY}')
        self.stdout.write(f'🌍 Pays: {country or settings.DEFAULT_COUNTRY}')
        self.stdout.write('')
        
        # Test de la météo actuelle
        self.stdout.write(self.style.HTTP_INFO('📡 Récupération de la météo actuelle...'))
        current_weather = weather_service.get_current_weather(city, country)
        
        if current_weather:
            self.stdout.write(self.style.SUCCESS('✅ Météo actuelle récupérée:'))
            self._display_current_weather(current_weather)
        else:
            self.stdout.write(self.style.ERROR('❌ Impossible de récupérer la météo actuelle'))
        
        # Test des prévisions si demandé
        if options['forecast']:
            self.stdout.write('')
            self.stdout.write(self.style.HTTP_INFO('📅 Récupération des prévisions...'))
            forecast = weather_service.get_forecast(city, country, days=5)
            
            if forecast:
                self.stdout.write(self.style.SUCCESS('✅ Prévisions récupérées:'))
                self._display_forecast(forecast)
            else:
                self.stdout.write(self.style.ERROR('❌ Impossible de récupérer les prévisions'))
        
        # Test des conseils agricoles
        if current_weather and options['forecast']:
            self.stdout.write('')
            self.stdout.write(self.style.HTTP_INFO('🌱 Génération des conseils agricoles...'))
            advice = weather_service.get_agricultural_advice(current_weather, forecast)
            
            if advice:
                self.stdout.write(self.style.SUCCESS('✅ Conseils générés:'))
                self._display_advice(advice)
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('🎉 Test terminé!'))
    
    def _display_current_weather(self, weather):
        """Affiche les données météo actuelles"""
        self.stdout.write(f'   🏙️  {weather["ville"]}, {weather.get("pays", "")}: {weather["temperature"]}°C')
        self.stdout.write(f'   ☁️  {weather["description"]}')
        self.stdout.write(f'   💨 Vent: {weather["vent"]} km/h')
        self.stdout.write(f'   💧 Humidité: {weather["humidite"]}%')
        self.stdout.write(f'   🌅 Lever: {weather["lever_soleil"]} | 🌇 Coucher: {weather["coucher_soleil"]}')
        
        if weather.get('derniere_maj') != 'Données de secours':
            self.stdout.write(f'   ⏰ Dernière mise à jour: {weather["derniere_maj"]}')
        else:
            self.stdout.write(self.style.WARNING('   ⚠️  Données de secours utilisées'))
    
    def _display_forecast(self, forecast):
        """Affiche les prévisions"""
        for day in forecast:
            self.stdout.write(
                f'   📅 {day["jour"]}: {day["temp_min"]}°C - {day["temp_max"]}°C, '
                f'{day["description"]}, Pluie: {day["probabilite_pluie"]}%'
            )
    
    def _display_advice(self, advice):
        """Affiche les conseils agricoles"""
        self.stdout.write(f'   🎯 {advice["titre"]}')
        for conseil in advice["conseils"]:
            self.stdout.write(f'   • {conseil}')
