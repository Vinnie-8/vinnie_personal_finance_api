from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
import uuid
from decimal import Decimal


class Transaction(models.Model):
    TYPE_INCOME = 'income'
    TYPE_EXPENSE = 'expense'
    TYPE_TRANSFER = 'transfer'
    TYPE_CHOICES = [
        (TYPE_INCOME, 'Income'),
        (TYPE_EXPENSE, 'Expense'),
        (TYPE_TRANSFER, 'Transfer'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='transactions')
    destination_account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='incoming_transfers',
    )
    category = models.ForeignKey(
        'categories.Category',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='transactions',
    )
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, default='USD')
    description = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    date = models.DateField()
    attachment = models.FileField(upload_to='attachments/', null=True, blank=True)

    # Recurring support
    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.CharField(max_length=100, blank=True)  # iCal RRULE e.g. FREQ=MONTHLY
    next_occurrence = models.DateField(null=True, blank=True)

    # Tags stored as PostgreSQL array
    tags = ArrayField(models.CharField(max_length=50), blank=True, default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'transactions'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.transaction_type}: {self.amount} — {self.description}"

    def save(self, *args, **kwargs):
        # Update account balance on create
        is_new = self._state.adding
        if is_new:
            self._apply_balance_change(self.amount)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Reverse balance change on delete
        self._apply_balance_change(-self.amount)
        super().delete(*args, **kwargs)

    def _apply_balance_change(self, amount):
        from apps.accounts.models import Account
        if self.transaction_type == self.TYPE_INCOME:
            Account.objects.filter(pk=self.account_id).update(
                balance=models.F('balance') + amount
            )
        elif self.transaction_type == self.TYPE_EXPENSE:
            Account.objects.filter(pk=self.account_id).update(
                balance=models.F('balance') - amount
            )
        elif self.transaction_type == self.TYPE_TRANSFER and self.destination_account_id:
            Account.objects.filter(pk=self.account_id).update(
                balance=models.F('balance') - amount
            )
            Account.objects.filter(pk=self.destination_account_id).update(
                balance=models.F('balance') + amount
            )
