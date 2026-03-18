from django.db import models
from django.conf import settings
import uuid


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
    )
    budget_alerts_inapp = models.BooleanField(default=True)
    budget_alerts_email = models.BooleanField(default=True)
    recurring_reminders_inapp = models.BooleanField(default=True)
    recurring_reminders_email = models.BooleanField(default=False)
    weekly_summary_email = models.BooleanField(default=True)
    system_notifications = models.BooleanField(default=True)

    class Meta:
        db_table = 'notification_preferences'

    def __str__(self):
        return f"Prefs({self.user.email})"


class Notification(models.Model):
    TYPE_BUDGET_ALERT = 'budget_alert'
    TYPE_RECURRING = 'recurring_reminder'
    TYPE_WEEKLY = 'weekly_summary'
    TYPE_SYSTEM = 'system'
    TYPE_CHOICES = [
        (TYPE_BUDGET_ALERT, 'Budget Alert'),
        (TYPE_RECURRING, 'Recurring Reminder'),
        (TYPE_WEEKLY, 'Weekly Summary'),
        (TYPE_SYSTEM, 'System'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    notification_type = models.CharField(max_length=25, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)   # extra context (budget_id, tx_id, etc.)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type}: {self.title}"

    def mark_read(self):
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Push to WebSocket after save
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"user_{self.user_id}",
                    {
                        'type': 'notification_message',
                        'id': str(self.id),
                        'notification_type': self.notification_type,
                        'title': self.title,
                        'message': self.message,
                        'data': self.data,
                        'created_at': self.created_at.isoformat(),
                    }
                )
        except Exception:
            pass  # Don't fail save if WS push fails
