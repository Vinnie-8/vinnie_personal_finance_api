from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['description', 'user', 'account', 'transaction_type', 'amount', 'date', 'is_recurring']
    list_filter = ['transaction_type', 'is_recurring', 'date']
    search_fields = ['description', 'notes', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'date'
    ordering = ['-date']
