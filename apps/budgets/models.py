from django.db import models
from django.conf import settings
import uuid
from decimal import Decimal


class Budget(models.Model):
    PERIOD_WEEKLY = 'weekly'
    PERIOD_MONTHLY = 'monthly'
    PERIOD_YEARLY = 'yearly'
    PERIOD_CUSTOM = 'custom'
    PERIOD_CHOICES = [
        (PERIOD_WEEKLY, 'Weekly'),
        (PERIOD_MONTHLY, 'Monthly'),
        (PERIOD_YEARLY, 'Yearly'),
        (PERIOD_CUSTOM, 'Custom'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(
        'categories.Category',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='budgets',
    )  # null = overall budget
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default=PERIOD_MONTHLY)
    start_date = models.DateField(null=True, blank=True)   # for custom period
    end_date = models.DateField(null=True, blank=True)     # for custom period
    alert_threshold = models.DecimalField(
        max_digits=4, decimal_places=2, default=Decimal('0.80'),
        help_text='Alert when spending reaches this fraction (e.g. 0.80 = 80%)',
    )
    is_active = models.BooleanField(default=True)
    rollover = models.BooleanField(default=False, help_text='Carry unspent amount to next period')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'budgets'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.period})"

    def get_period_dates(self):
        """Return (start, end) for current period."""
        from django.utils import timezone
        import datetime
        today = timezone.now().date()
        if self.period == self.PERIOD_CUSTOM:
            return self.start_date, self.end_date
        elif self.period == self.PERIOD_WEEKLY:
            start = today - datetime.timedelta(days=today.weekday())
            end = start + datetime.timedelta(days=6)
        elif self.period == self.PERIOD_MONTHLY:
            start = today.replace(day=1)
            next_month = (today.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
            end = next_month - datetime.timedelta(days=1)
        else:  # yearly
            start = today.replace(month=1, day=1)
            end = today.replace(month=12, day=31)
        return start, end

    def get_spent(self):
        """Calculate amount spent in current period."""
        from apps.transactions.models import Transaction
        from django.db.models import Sum
        start, end = self.get_period_dates()
        qs = Transaction.objects.filter(
            user=self.user,
            transaction_type=Transaction.TYPE_EXPENSE,
            date__gte=start,
            date__lte=end,
        )
        if self.category:
            qs = qs.filter(category=self.category)
        total = qs.aggregate(s=Sum('amount'))['s']
        return total or Decimal('0')
