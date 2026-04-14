# -*- coding: utf-8 -*-
"""
Service API Météo pour AgriSmart
Intégration avec OpenWeatherMap API
Version 1.0.0 - Août 2025
"""

import requests
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class WeatherService:
    """Service pour récupérer les données météorologiques via OpenWeatherMap API"""
    
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = settings.OPENWEATHER_BASE_URL
        self.default_city = settings.DEFAULT_CITY
        self.default_country = settings.DEFAULT_COUNTRY
        self.lang = settings.WEATHER_LANG
        self.units = settings.WEATHER_UNITS
    
    def get_current_weather(self, city=None, country=None):
        """
        Récupère la météo actuelle pour une ville
        Args:
            city (str): Nom de la ville (défaut: settings.DEFAULT_CITY)
            country (str): Code pays ISO (défaut: settings.DEFAULT_COUNTRY)
        Returns:
            dict: Données météo formatées ou None en cas d'erreur
        """
        city = city or self.default_city
        country = country or self.default_country
        
        # Clé de cache pour éviter trop de requêtes API
        cache_key = f'current_weather_{city}_{country}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Données météo récupérées du cache pour {city}")
            return cached_data
        
        try:
            # Construction de l'URL avec paramètres
            url = f"{self.base_url}/weather"
            params = {
                'q': f"{city},{country}",
                'appid': self.api_key,
                'lang': self.lang,
                'units': self.units
            }
            
            logger.info(f"Requête API météo pour {city}, {country}")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Formatage des données
            weather_data = self._format_current_weather(data)
            
            # Mise en cache pour 10 minutes
            cache.set(cache_key, weather_data, 600)
            
            logger.info(f"Données météo récupérées avec succès pour {city}")
            return weather_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la requête API météo: {e}")
            return self._get_fallback_current_weather(city)
        
        except Exception as e:
            logger.error(f"Erreur inattendue dans get_current_weather: {e}")
            return self._get_fallback_current_weather(city)
    
    def get_forecast(self, city=None, country=None, days=5):
        """
        Récupère les prévisions météo sur plusieurs jours
        Args:
            city (str): Nom de la ville
            country (str): Code pays ISO
            days (int): Nombre de jours de prévision (max 5 pour API gratuite)
        Returns:
            list: Liste des prévisions formatées
        """
        city = city or self.default_city
        country = country or self.default_country
        
        cache_key = f'forecast_{city}_{country}_{days}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Prévisions récupérées du cache pour {city}")
            return cached_data
        
        try:
            url = f"{self.base_url}/forecast"
            params = {
                'q': f"{city},{country}",
                'appid': self.api_key,
                'lang': self.lang,
                'units': self.units,
                'cnt': days * 8  # 8 prévisions par jour (toutes les 3h)
            }
            
            logger.info(f"Requête prévisions météo pour {city}, {country}")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Formatage des prévisions
            forecast_data = self._format_forecast_data(data, days)
            
            # Mise en cache pour 30 minutes
            cache.set(cache_key, forecast_data, 1800)
            
            logger.info(f"Prévisions récupérées avec succès pour {city}")
            return forecast_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la requête prévisions: {e}")
            return self._get_fallback_forecast()
        
        except Exception as e:
            logger.error(f"Erreur inattendue dans get_forecast: {e}")
            return self._get_fallback_forecast()
    
    def _format_current_weather(self, api_data):
        """Formate les données de l'API pour l'affichage"""
        try:
            main = api_data['main']
            weather = api_data['weather'][0]
            wind = api_data.get('wind', {})
            sys = api_data['sys']
            
            # Conversion des timestamps
            sunrise = datetime.fromtimestamp(sys['sunrise']).strftime('%H:%M')
            sunset = datetime.fromtimestamp(sys['sunset']).strftime('%H:%M')
            
            return {
                'ville': api_data['name'],
                'pays': sys['country'],
                'temperature': round(main['temp']),
                'temperature_ressentie': round(main['feels_like']),
                'description': weather['description'].capitalize(),
                'humidite': main['humidity'],
                'pression': main['pressure'],
                'vent': round(wind.get('speed', 0) * 3.6),  # Conversion m/s en km/h
                'direction_vent': wind.get('deg', 0),
                'visibilite': api_data.get('visibility', 10000) // 1000,  # En km
                'lever_soleil': sunrise,
                'coucher_soleil': sunset,
                'icone': weather['icon'],
                'code_meteo': weather['id'],
                'derniere_maj': datetime.now().strftime('%H:%M')
            }
            
        except KeyError as e:
            logger.error(f"Clé manquante dans les données API: {e}")
            return self._get_fallback_current_weather()
    
    def _format_forecast_data(self, api_data, days):
        """Formate les données de prévision"""
        try:
            forecasts = []
            daily_data = {}
            
            # Grouper les prévisions par jour
            for item in api_data['list'][:days * 8]:
                date = datetime.fromtimestamp(item['dt']).date()
                
                if date not in daily_data:
                    daily_data[date] = {
                        'temps': [],
                        'temperatures': [],
                        'humidites': [],
                        'vents': [],
                        'precipitations': []
                    }
                
                daily_data[date]['temps'].append(item['weather'][0])
                daily_data[date]['temperatures'].append(item['main']['temp'])
                daily_data[date]['humidites'].append(item['main']['humidity'])
                daily_data[date]['vents'].append(item['wind'].get('speed', 0) * 3.6)
                daily_data[date]['precipitations'].append(
                    item.get('rain', {}).get('3h', 0) + item.get('snow', {}).get('3h', 0)
                )
            
            # Créer les prévisions quotidiennes
            for date, data in list(daily_data.items())[:days]:
                # Température min/max
                temp_min = round(min(data['temperatures']))
                temp_max = round(max(data['temperatures']))
                
                # Météo dominante (la plus fréquente)
                weather_codes = [w['id'] for w in data['temps']]
                dominant_weather = max(set(weather_codes), key=weather_codes.count)
                dominant_weather_info = next(w for w in data['temps'] if w['id'] == dominant_weather)
                
                # Probabilité de pluie (basée sur les précipitations)
                total_rain = sum(data['precipitations'])
                rain_probability = min(100, round(total_rain * 20))  # Approximation
                
                # Formatage du jour
                if date == datetime.now().date():
                    jour = "Aujourd'hui"
                elif date == datetime.now().date() + timedelta(days=1):
                    jour = "Demain"
                else:
                    jour = date.strftime('%d %b')
                
                forecasts.append({
                    'jour': jour,
                    'date': date.strftime('%Y-%m-%d'),
                    'temp_min': temp_min,
                    'temp_max': temp_max,
                    'description': dominant_weather_info['description'].capitalize(),
                    'icone': self._get_weather_icon_class(dominant_weather_info['icon']),
                    'probabilite_pluie': rain_probability,
                    'humidite_moyenne': round(sum(data['humidites']) / len(data['humidites'])),
                    'vent_moyen': round(sum(data['vents']) / len(data['vents']))
                })
            
            return forecasts
            
        except Exception as e:
            logger.error(f"Erreur lors du formatage des prévisions: {e}")
            return self._get_fallback_forecast()
    
    def _get_weather_icon_class(self, icon_code):
        """Convertit le code icône OpenWeatherMap en classe Font Awesome"""
        icon_mapping = {
            '01d': 'fas fa-sun text-yellow-400',           # Soleil
            '01n': 'fas fa-moon text-blue-300',            # Lune
            '02d': 'fas fa-cloud-sun text-yellow-500',     # Peu nuageux jour
            '02n': 'fas fa-cloud-moon text-blue-400',      # Peu nuageux nuit
            '03d': 'fas fa-cloud text-gray-400',           # Nuageux
            '03n': 'fas fa-cloud text-gray-500',           # Nuageux nuit
            '04d': 'fas fa-cloud text-gray-600',           # Très nuageux
            '04n': 'fas fa-cloud text-gray-700',           # Très nuageux nuit
            '09d': 'fas fa-cloud-showers-heavy text-blue-500',  # Pluie
            '09n': 'fas fa-cloud-showers-heavy text-blue-600',  # Pluie nuit
            '10d': 'fas fa-cloud-rain text-blue-500',      # Pluie jour
            '10n': 'fas fa-cloud-rain text-blue-600',      # Pluie nuit
            '11d': 'fas fa-bolt text-yellow-600',          # Orage
            '11n': 'fas fa-bolt text-purple-600',          # Orage nuit
            '13d': 'fas fa-snowflake text-blue-200',       # Neige
            '13n': 'fas fa-snowflake text-blue-300',       # Neige nuit
            '50d': 'fas fa-smog text-gray-500',            # Brouillard
            '50n': 'fas fa-smog text-gray-600'             # Brouillard nuit
        }
        
        return icon_mapping.get(icon_code, 'fas fa-cloud text-gray-500')
    
    def get_agricultural_advice(self, weather_data, forecast_data):
        """
        Génère des conseils agricoles basés sur la météo
        Args:
            weather_data (dict): Données météo actuelles
            forecast_data (list): Prévisions sur plusieurs jours
        Returns:
            dict: Conseils formatés pour l'agriculture
        """
        if not weather_data or not forecast_data:
            return None
        
        conseils = []
        titre = ""
        
        # Analyse de la température
        temp_actuelle = weather_data['temperature']
        if temp_actuelle > 35:
            conseils.append("Températures élevées : arrosez vos cultures tôt le matin ou en soirée")
            conseils.append("Protégez les jeunes plants avec des ombrages temporaires")
            titre = "Chaleur intense - Précautions nécessaires"
        elif temp_actuelle < 15:
            conseils.append("Températures fraîches : protégez les cultures sensibles au froid")
            titre = "Températures fraîches - Protection recommandée"
        
        # Analyse de l'humidité
        humidite = weather_data['humidite']
        if humidite > 80:
            conseils.append("Humidité élevée : surveillez les maladies fongiques")
            conseils.append("Aérez bien vos cultures pour éviter la stagnation d'air")
            if not titre:
                titre = "Humidité élevée - Surveillance nécessaire"
        elif humidite < 30:
            conseils.append("Air sec : augmentez la fréquence d'arrosage")
            if not titre:
                titre = "Air sec - Arrosage recommandé"
        
        # Analyse des prévisions de pluie
        pluie_prevue = any(p['probabilite_pluie'] > 60 for p in forecast_data[:3])
        if pluie_prevue:
            conseils.append("Pluie prévue : reportez l'application d'engrais et de traitements")
            conseils.append("Vérifiez vos systèmes de drainage")
            conseils.append("Protégez les récoltes sensibles à l'humidité")
            titre = "Pluie prévue - Ajustez vos activités"
        
        # Analyse du vent
        vent = weather_data['vent']
        if vent > 30:
            conseils.append("Vent fort : évitez les traitements phytosanitaires")
            conseils.append("Tuteurez solidement les plantes hautes")
            if not titre:
                titre = "Vent fort - Précautions recommandées"
        
        # Conseils par défaut si aucune condition spéciale
        if not conseils:
            conseils = [
                "Conditions météo favorables pour les activités agricoles",
                "Maintenez un arrosage régulier selon les besoins de vos cultures",
                "Surveillez l'évolution météorologique pour les prochains jours"
            ]
            titre = "Conditions favorables - Activités normales"
        
        return {
            'titre': titre,
            'conseils': conseils
        }
    
    def _get_fallback_current_weather(self, city=None):
        """Données météo de secours en cas d'échec de l'API"""
        city = city or self.default_city
        return {
            'ville': city,
            'pays': 'CI',
            'temperature': 28,
            'temperature_ressentie': 30,
            'description': 'Nuageux',
            'humidite': 65,
            'pression': 1013,
            'vent': 12,
            'direction_vent': 180,
            'visibilite': 10,
            'lever_soleil': '6:12',
            'coucher_soleil': '18:35',
            'icone': '02d',
            'code_meteo': 802,
            'derniere_maj': 'Données de secours'
        }
    
    def _get_fallback_forecast(self):
        """Prévisions de secours en cas d'échec de l'API"""
        return [
            {
                'jour': 'Aujourd\'hui',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'temp_min': 24,
                'temp_max': 28,
                'description': 'Nuageux',
                'icone': 'fas fa-cloud text-gray-500',
                'probabilite_pluie': 20,
                'humidite_moyenne': 65,
                'vent_moyen': 12
            },
            {
                'jour': 'Demain',
                'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'temp_min': 23,
                'temp_max': 27,
                'description': 'Pluies éparses',
                'icone': 'fas fa-cloud-showers-heavy text-blue-500',
                'probabilite_pluie': 80,
                'humidite_moyenne': 75,
                'vent_moyen': 15
            },
            {
                'jour': (datetime.now() + timedelta(days=2)).strftime('%d %b'),
                'date': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
                'temp_min': 24,
                'temp_max': 29,
                'description': 'Partiellement ensoleillé',
                'icone': 'fas fa-cloud-sun text-yellow-500',
                'probabilite_pluie': 10,
                'humidite_moyenne': 60,
                'vent_moyen': 10
            },
            {
                'jour': (datetime.now() + timedelta(days=3)).strftime('%d %b'),
                'date': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
                'temp_min': 25,
                'temp_max': 31,
                'description': 'Ensoleillé',
                'icone': 'fas fa-sun text-yellow-400',
                'probabilite_pluie': 0,
                'humidite_moyenne': 55,
                'vent_moyen': 8
            },
            {
                'jour': (datetime.now() + timedelta(days=4)).strftime('%d %b'),
                'date': (datetime.now() + timedelta(days=4)).strftime('%Y-%m-%d'),
                'temp_min': 26,
                'temp_max': 32,
                'description': 'Ensoleillé',
                'icone': 'fas fa-sun text-yellow-400',
                'probabilite_pluie': 0,
                'humidite_moyenne': 50,
                'vent_moyen': 7
            }
        ]
