from django.urls import path

from .consumers import DiscussionConsumer

websocket_urlpatterns = [
    path('ws/demandes/<int:demande_id>/discussion/', DiscussionConsumer.as_asgi()),
]