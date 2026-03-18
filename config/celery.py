import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('personal_finance')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# ── Periodic Tasks ──────────────────────────────────────────────────────────
app.conf.beat_schedule = {
    # Check budgets every hour and fire alerts
    'check-budget-alerts-hourly': {
        'task': 'apps.budgets.tasks.check_budget_alerts',
        'schedule': crontab(minute=0),
    },
    # Daily reminder for upcoming recurring transactions
    'send-recurring-reminders-daily': {
        'task': 'apps.transactions.tasks.send_recurring_reminders',
        'schedule': crontab(hour=8, minute=0),
    },
    # Weekly summary every Monday 9am
    'send-weekly-summary': {
        'task': 'apps.reports.tasks.send_weekly_summary',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),
    },
    # Snapshot net worth every midnight
    'snapshot-net-worth-daily': {
        'task': 'apps.accounts.tasks.snapshot_net_worth',
        'schedule': crontab(hour=0, minute=0),
    },
    # Rollover budgets on 1st of each month
    'rollover-monthly-budgets': {
        'task': 'apps.budgets.tasks.rollover_monthly_budgets',
        'schedule': crontab(hour=0, minute=5, day_of_month=1),
    },
    # Clean up old notifications weekly
    'cleanup-old-notifications': {
        'task': 'apps.notifications.tasks.cleanup_old_notifications',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),
    },
}
