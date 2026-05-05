import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Notification


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_group_name = f"notifications_{self.user.id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        unread_count = await self.get_unread_notifications()
        await self.send(text_data=json.dumps({
            "type": "initial_count",
            "unread_count": unread_count,
        }))

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get("type")

        if msg_type == "mark_as_read":
            notification_id = data.get("notification_id")
            await self.mark_notification_read(notification_id)
            unread_count = await self.get_unread_notifications()
            await self.send(text_data=json.dumps({
                "type": "count_update",
                "unread_count": unread_count,
            }))

    async def notification_message(self, event):
        notification_id = event.get("notification_id")
        title = event.get("title")
        message = event.get("message")
        created_at = event.get("created_at")

        unread_count = await self.get_unread_notifications()

        await self.send(text_data=json.dumps({
            "type": "new_notification",
            "notification_id": notification_id,
            "title": title,
            "message": message,
            "created_at": created_at,
            "unread_count": unread_count,
        }))

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        try:
            notification = Notification.objects.get(id=notification_id, user=self.user)
            notification.is_read = True
            notification.save()
        except Notification.DoesNotExist:
            pass

    @database_sync_to_async
    def get_unread_notifications(self):
        return self.user.notifications.filter(is_read=False).count()
