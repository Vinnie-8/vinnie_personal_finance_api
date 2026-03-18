from celery import shared_task
from decimal import Decimal


@shared_task
def check_budget_alerts():
    """Hourly: find budgets exceeding threshold and create notifications."""
    from .models import Budget
    from apps.notifications.models import Notification

    budgets = Budget.objects.filter(is_active=True).select_related('user', 'category')
    count = 0
    for budget in budgets:
        spent = budget.get_spent()
        if spent >= budget.amount * budget.alert_threshold:
            pct = float(spent / budget.amount * 100) if budget.amount else 0
            level = 'exceeded' if spent >= budget.amount else f"{pct:.0f}%"
            Notification.objects.create(
                user=budget.user,
                notification_type=Notification.TYPE_BUDGET_ALERT,
                title=f"Budget Alert: {budget.name}",
                message=f"You've used {level} of your {budget.name} budget "
                        f"({budget.currency if hasattr(budget, 'currency') else ''} {spent:.2f} / {budget.amount:.2f}).",
                data={
                    'budget_id': str(budget.id),
                    'spent': str(spent),
                    'amount': str(budget.amount),
                    'percentage': pct,
                },
            )
            count += 1
    return f"Created {count} budget alert notifications."


@shared_task
def rollover_monthly_budgets():
    """1st of month: rollover unspent amounts for eligible budgets."""
    from .models import Budget
    budgets = Budget.objects.filter(is_active=True, rollover=True, period='monthly')
    for budget in budgets:
        spent = budget.get_spent()
        unspent = budget.amount - spent
        if unspent > Decimal('0'):
            budget.amount += unspent
            budget.save(update_fields=['amount'])
    return f"Rolled over {budgets.count()} budgets."
