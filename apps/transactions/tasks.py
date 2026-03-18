from celery import shared_task
from django.utils import timezone
import datetime


@shared_task
def send_recurring_reminders():
    """Daily: notify users about upcoming recurring transactions."""
    from .models import Transaction
    from apps.notifications.models import Notification

    today = timezone.now().date()
    upcoming = today + datetime.timedelta(days=3)

    transactions = Transaction.objects.filter(
        is_recurring=True,
        next_occurrence__gte=today,
        next_occurrence__lte=upcoming,
    ).select_related('user', 'account')

    count = 0
    for tx in transactions:
        Notification.objects.create(
            user=tx.user,
            notification_type=Notification.TYPE_RECURRING,
            title=f"Upcoming: {tx.description}",
            message=f"Your recurring {tx.transaction_type} of {tx.currency} {tx.amount} "
                    f"({tx.description}) is due on {tx.next_occurrence}.",
            data={'transaction_id': str(tx.id), 'amount': str(tx.amount)},
        )
        count += 1

    return f"Sent {count} recurring reminders."
