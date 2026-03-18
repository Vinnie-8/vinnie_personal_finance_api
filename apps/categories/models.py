from django.db import models
from django.conf import settings
import uuid


class Category(models.Model):
    TYPE_INCOME = 'income'
    TYPE_EXPENSE = 'expense'
    TYPE_BOTH = 'both'
    TYPE_CHOICES = [
        (TYPE_INCOME, 'Income'),
        (TYPE_EXPENSE, 'Expense'),
        (TYPE_BOTH, 'Both'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='categories',
        null=True, blank=True,  # null = system/default category
    )
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='tag')   # icon name (e.g. FontAwesome)
    color = models.CharField(max_length=7, default='#6c757d')  # hex
    category_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_EXPENSE)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='children',
    )
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'categories'
        ordering = ['name']
        verbose_name_plural = 'categories'
        unique_together = [['user', 'name', 'parent']]

    def __str__(self):
        return f"{self.name} ({'system' if self.is_system else self.user})"
