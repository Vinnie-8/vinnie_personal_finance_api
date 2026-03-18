from celery import shared_task
from django.db.models import Sum
from decimal import Decimal
from django.utils import timezone


@shared_task
def snapshot_net_worth():
    """Daily task: snapshot each user's net worth for historical graph."""
    from apps.users.models import User
    from .models import Account, NetWorthSnapshot

    today = timezone.now().date()
    users = User.objects.filter(is_active=True)

    for user in users:
        accounts = Account.objects.filter(user=user, is_active=True, include_in_total=True)
        assets = accounts.filter(
            account_type__in=['checking', 'savings', 'cash', 'investment']
        ).aggregate(s=Sum('balance'))['s'] or Decimal('0')
        liabilities = accounts.filter(
            account_type__in=['credit_card', 'loan']
        ).aggregate(s=Sum('balance'))['s'] or Decimal('0')
        net_worth = assets - liabilities

        NetWorthSnapshot.objects.update_or_create(
            user=user,
            snapshot_date=today,
            defaults={
                'total_assets': assets,
                'total_liabilities': liabilities,
                'net_worth': net_worth,
            }
        )

    return f"Snapshotted net worth for {users.count()} users."
