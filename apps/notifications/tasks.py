from celery import shared_task
from django.utils import timezone
import datetime


@shared_task
def cleanup_old_notifications():
    """Weekly: delete notifications older than 90 days."""
    from .models import Notification
    cutoff = timezone.now() - datetime.timedelta(days=90)
    deleted, _ = Notification.objects.filter(created_at__lt=cutoff, is_read=True).delete()
    return f"Deleted {deleted} old notifications."
