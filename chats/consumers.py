import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Chat, Mensagem

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'
        
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
            
        # Verifica se o usuário pertence ao chat
        has_access = await self.check_user_in_chat(self.chat_id, self.user.id)
        if not has_access:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '').strip()

        if not message:
            return

        # Salva a mensagem no banco de dados
        msg_obj = await self.save_message(self.chat_id, self.user.id, message)

        if not msg_obj:
            # Avisa só o remetente (não o grupo) que a mensagem não foi
            # persistida, em vez de falhar silenciosamente.
            await self.send(text_data=json.dumps({
                'type': 'error',
                'detail': 'Não foi possível enviar a mensagem. Tente novamente.',
            }))
            return

        data_envio = msg_obj.data_envio.strftime("%d/%m/%Y %H:%M")

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'id': msg_obj.id,
                'message': message,
                'remetente': self.user.username,
                'remetente_id': self.user.id,
                'data_envio': data_envio,
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'id': event['id'],
            'message': event['message'],
            'remetente': event['remetente'],
            'is_me': (self.user.id == event['remetente_id']),
            'data_envio': event['data_envio']
        }))

    @database_sync_to_async
    def check_user_in_chat(self, chat_id, user_id):
        try:
            chat = Chat.objects.get(id=chat_id)
            return user_id in (chat.criado_por_id, chat.dono_item_id)
        except (Chat.DoesNotExist, ValueError, ValidationError):
            # ValueError/ValidationError cobrem chat_id não numérico vindo da URL do WS
            return False

    @database_sync_to_async
    def save_message(self, chat_id, user_id, conteudo):
        try:
            chat = Chat.objects.get(id=chat_id)
            if chat.status != 'ativo':
                return None
                
            m = Mensagem.objects.create(
                chat=chat,
                remetente_id=user_id,
                conteudo=conteudo,
                tipo="texto",
                lida=False,
            )
            chat.atualizado_em = timezone.now()
            chat.save(update_fields=["atualizado_em"])
            
            # Notifica a outra parte
            try:
                destinatario = chat.criado_por if user_id == chat.dono_item_id else chat.dono_item
                from items.models import Notificacao
                from django.urls import reverse
                link_chat = reverse('chat_detail', args=[chat.id])
                Notificacao.objects.create(
                    usuario=destinatario,
                    titulo="Nova mensagem",
                    mensagem=f"Sobre o item: {chat.item.titulo if chat.item else 'Item removido'}",
                    icone="bi-chat-dots-fill",
                    link=link_chat
                )
            except Exception:
                logger.exception(f"Falha ao criar notificação de nova mensagem (chat_id={chat_id})")

            return m
        except (Chat.DoesNotExist, ValueError, ValidationError):
            return None
        except Exception:
            logger.exception(f"Falha ao salvar mensagem de chat (chat_id={chat_id}, user_id={user_id})")
            return None

