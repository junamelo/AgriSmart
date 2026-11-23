from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import DemandeExpert, MessageDiscussion


class DiscussionConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.demande_id = self.scope['url_route']['kwargs']['demande_id']
        self.user = self.scope['user']

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.demande = await self.get_demande(self.demande_id)
        if not self.demande:
            await self.close(code=4004)
            return

        if not await self.user_can_access_demande(self.user.id, self.demande_id):
            await self.close(code=4003)
            return

        self.group_name = f'discussion_{self.demande_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self.send_json({
            'type': 'history',
            'messages': await self.get_messages(self.demande_id),
        })

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get('type') != 'message':
            return

        message_text = (content.get('contenu') or '').strip()
        if not message_text:
            await self.send_json({'type': 'error', 'message': 'Le message ne peut pas être vide.'})
            return

        if not await self.user_can_access_demande(self.user.id, self.demande_id):
            await self.send_json({'type': 'error', 'message': 'Accès refusé à cette discussion.'})
            return

        message = await self.create_message(self.demande_id, self.user.id, message_text)
        payload = {
            'type': 'chat_message',
            'message': {
                'id': message.id,
                'contenu': message.contenu,
                'date_envoi': message.date_envoi.isoformat(),
                'auteur_id': self.user.id,
                'auteur_nom': self.user.get_full_name() or self.user.username,
            },
        }
        await self.channel_layer.group_send(self.group_name, payload)

    async def chat_message(self, event):
        await self.send_json({
            'type': 'message',
            'message': event['message'],
        })

    @database_sync_to_async
    def get_demande(self, demande_id):
        try:
            return DemandeExpert.objects.select_related('agriculteur__user', 'expert__user').get(id=demande_id)
        except DemandeExpert.DoesNotExist:
            return None

    @database_sync_to_async
    def user_can_access_demande(self, user_id, demande_id):
        try:
            demande = DemandeExpert.objects.select_related('agriculteur__user', 'expert__user').get(id=demande_id)
        except DemandeExpert.DoesNotExist:
            return False

        if demande.agriculteur and demande.agriculteur.user_id == user_id:
            return True

        if demande.expert and demande.expert.user_id == user_id:
            return True

        return False

    @database_sync_to_async
    def get_messages(self, demande_id):
        messages = MessageDiscussion.objects.select_related('auteur').filter(demande_id=demande_id)[:100]
        return [
            {
                'id': message.id,
                'contenu': message.contenu,
                'date_envoi': message.date_envoi.isoformat(),
                'auteur_id': message.auteur_id,
                'auteur_nom': message.auteur.get_full_name() or message.auteur.username,
            }
            for message in messages
        ]

    @database_sync_to_async
    def create_message(self, demande_id, auteur_id, contenu):
        return MessageDiscussion.objects.create(
            demande_id=demande_id,
            auteur_id=auteur_id,
            contenu=contenu,
        )