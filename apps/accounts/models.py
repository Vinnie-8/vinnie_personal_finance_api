from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
import uuid
from decimal import Decimal


class Account(models.Model):
    TYPE_CHECKING = 'checking'
    TYPE_SAVINGS = 'savings'
    TYPE_CREDIT = 'credit_card'
    TYPE_CASH = 'cash'
    TYPE_INVESTMENT = 'investment'
    TYPE_LOAN = 'loan'

    ACCOUNT_TYPES = [
        (TYPE_CHECKING, 'Checking'),
        (TYPE_SAVINGS, 'Savings'),
        (TYPE_CREDIT, 'Credit Card'),
        (TYPE_CASH, 'Cash'),
        (TYPE_INVESTMENT, 'Investment'),
        (TYPE_LOAN, 'Loan'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'), ('EUR', 'Euro'), ('GBP', 'British Pound'),
        ('KES', 'Kenyan Shilling'), ('NGN', 'Nigerian Naira'), ('ZAR', 'South African Rand'),
        ('GHS', 'Ghanaian Cedi'), ('CAD', 'Canadian Dollar'), ('AUD', 'Australian Dollar'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='accounts')
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default=TYPE_CHECKING)
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    institution_name = models.CharField(max_length=100, blank=True)
    account_number_last4 = models.CharField(max_length=4, blank=True)
    color = models.CharField(max_length=7, default='#0d6efd')
    icon = models.CharField(max_length=50, default='bank')
    is_active = models.BooleanField(default=True)
    include_in_total = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.user.email})"

    @property
    def is_liability(self):
        return self.account_type in [self.TYPE_CREDIT, self.TYPE_LOAN]


class NetWorthSnapshot(models.Model):
    """Daily snapshot of user's net worth for historical graph."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='net_worth_snapshots')
    total_assets = models.DecimalField(max_digits=14, decimal_places=2)
    total_liabilities = models.DecimalField(max_digits=14, decimal_places=2)
    net_worth = models.DecimalField(max_digits=14, decimal_places=2)
    snapshot_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'net_worth_snapshots'
        ordering = ['-snapshot_date']
        unique_together = [['user', 'snapshot_date']]
