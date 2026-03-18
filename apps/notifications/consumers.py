import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket: ws://localhost:8000/ws/notifications/
    Requires JWT in query string: ?token=<access_token>
    """

    async def connect(self):
        user = await self._get_user_from_token()
        if user is None or not user.is_active:
            await self.close()
            return

        self.user = user
        self.group_name = f"user_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send unread count on connect
        count = await self._get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'connected',
            'message': 'Connected to notification stream.',
            'unread_count': count,
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """Handle client messages: mark_read, mark_all_read"""
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'mark_read':
            notif_id = data.get('notification_id')
            await self._mark_notification_read(notif_id)
            await self.send(text_data=json.dumps({'type': 'marked_read', 'id': notif_id}))
        elif action == 'mark_all_read':
            count = await self._mark_all_read()
            await self.send(text_data=json.dumps({'type': 'all_marked_read', 'count': count}))
        elif action == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))

    async def notification_message(self, event):
        """Called when a new notification is pushed to this group."""
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            **{k: v for k, v in event.items() if k != 'type'},
        }))

    # ── DB helpers ──────────────────────────────────────────────────────────

    @database_sync_to_async
    def _get_user_from_token(self):
        try:
            token_str = self.scope['query_string'].decode().split('token=')[-1]
            from rest_framework_simplejwt.tokens import AccessToken
            from apps.users.models import User
            token = AccessToken(token_str)
            return User.objects.get(pk=token['user_id'])
        except Exception:
            return None

    @database_sync_to_async
    def _get_unread_count(self):
        from .models import Notification
        return Notification.objects.filter(user=self.user, is_read=False).count()

    @database_sync_to_async
    def _mark_notification_read(self, notif_id):
        from .models import Notification
        try:
            n = Notification.objects.get(pk=notif_id, user=self.user)
            n.mark_read()
        except Notification.DoesNotExist:
            pass

    @database_sync_to_async
    def _mark_all_read(self):
        from .models import Notification
        from django.utils import timezone
        return Notification.objects.filter(user=self.user, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
